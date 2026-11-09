from __future__ import annotations

import asyncio
import hashlib
import io
import hmac
import base64
import csv
import html as html_lib
import json
import logging
import os
import re
import secrets
import smtplib
import ssl
import sqlite3
import time
import zipfile
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal, Optional
from zoneinfo import ZoneInfo
from urllib.parse import quote, urlsplit
from email.utils import getaddresses
from email.message import EmailMessage
from cryptography.fernet import Fernet, InvalidToken

import httpx
import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile, WebSocket, WebSocketDisconnect
from starlette.datastructures import Headers, UploadFile as StarletteUploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.resolution import build_resolution, review_support_reply
from backend.rulebook import RULEBOOK_VERSION, RULEBOOK_REVIEWED_ON
from backend.action_pack import ALL_CHECKLIST_KEYS, build_action_pack
from backend.completion_loop import build_completion_loop, stage_for_reply_category
from backend.passport import build_passport_export, render_printable_passport
from backend.extraction import extract_case_facts
from backend.evidence_review import extract_evidence_text, EvidenceExtractionError
from backend.commitments import extract_commitment_candidate, evaluate_commitment, source_hash as commitment_source_hash, VERSION as COMMITMENTS_VERSION
from backend.security import scrub_sensitive_text
from backend import agent_assist
from backend.adaptive_workflow import build_adaptive_workflow, extract_workflow_facts
from backend.reconciliation import parse_reconciliation_csv, MAX_CSV_BYTES
from PIL import Image, ImageOps
from backend.support_directory import find_support_destinations, build_quick_support_draft, find_nch_convergence_match, NCH_CONVERGENCE_DIRECTORY_URL, NCH_CONVERGENCE_REVIEWED_ON
from backend import whatsapp as whatsapp_service
from backend import twilio_whatsapp as twilio_service
from backend import messaging as messaging_service

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
# Load .env before reading configuration. OS-level environment variables still win.
load_dotenv(ROOT / ".env")
DATA_DIR = Path(os.getenv("BOLKE_DATA_DIR", str(ROOT / "runtime"))).expanduser().resolve()
UPLOAD_DIR = DATA_DIR / "evidence"
DB_PATH = DATA_DIR / "bolkeresolve.sqlite3"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DEPLOYMENT_ENV = os.getenv("BOLKE_ENV", "development").strip().lower()
AUTH_REQUIRED = DEPLOYMENT_ENV == "production" or os.getenv("BOLKE_AUTH_REQUIRED", "false").strip().lower() in {"1", "true", "yes", "on"}
# Accounts are available in local development too; BOLKE_AUTH_REQUIRED decides whether
# they are mandatory. This makes sign-up discoverable without forcing a local login.
AUTH_ENABLED = AUTH_REQUIRED or os.getenv("BOLKE_ACCOUNTS_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
EMAIL_VERIFICATION_REQUIRED = DEPLOYMENT_ENV == "production" or os.getenv("BOLKE_EMAIL_VERIFICATION_REQUIRED", "false").strip().lower() in {"1", "true", "yes", "on"}
COOKIE_SECURE = DEPLOYMENT_ENV == "production" or os.getenv("BOLKE_COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes", "on"}
SESSION_COOKIE_NAME = "bolke_session"
SESSION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
PASSWORD_HASH_ITERATIONS = 600_000
CURRENT_USER_ID: ContextVar[str | None] = ContextVar("bolke_current_user_id", default=None)
AUTH_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_AUTH_ATTEMPTS: dict[str, list[float]] = {}
_VOICE_ATTEMPTS: dict[str, list[float]] = {}
_PREVIEW_ATTEMPTS: dict[str, list[float]] = {}

logger = logging.getLogger("bolkeresolve.voice")


def is_allowed_browser_origin(origin: str, request_host: str) -> bool:
    """Match browser Origin against an exact allowlist, falling back to same-host locally.

    BOLKE_PUBLIC_ORIGIN remains the canonical URL for email links. Additional exact
    origins (for example a stable Vercel Preview alias) can be added through
    BOLKE_ALLOWED_ORIGINS as a comma-separated list. Wildcards are never accepted.
    """
    normalized_origin = str(origin or "").strip().rstrip("/")
    if not normalized_origin:
        return False

    candidates = [os.getenv("BOLKE_PUBLIC_ORIGIN", "")]
    candidates.extend(os.getenv("BOLKE_ALLOWED_ORIGINS", "").split(","))
    allowed: set[str] = set()
    for candidate in candidates:
        candidate = str(candidate or "").strip().rstrip("/")
        if not candidate:
            continue
        try:
            parsed = urlsplit(candidate)
        except ValueError:
            continue
        if (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
            and not parsed.username
            and not parsed.password
            and parsed.path in {"", "/"}
            and not parsed.query
            and not parsed.fragment
        ):
            allowed.add(candidate)

    if allowed:
        return normalized_origin in allowed

    try:
        parsed_origin = urlsplit(normalized_origin)
    except ValueError:
        return False
    return (
        parsed_origin.scheme in {"http", "https"}
        and bool(parsed_origin.netloc)
        and parsed_origin.netloc.lower() == str(request_host or "").lower()
    )


@asynccontextmanager
async def app_lifespan(_app):
    """Run bounded retention cleanup so pending forwarded email doesn't rely on a visit."""
    async def retention_sweeper():
        while True:
            try:
                with get_db() as con:
                    expired = _expire_inbound_email(con)
                    expired_share_intakes = _expire_shared_intakes(con)
                    con.execute("DELETE FROM auth_action_tokens WHERE expires_at < ? OR (consumed_at != '' AND consumed_at < ?)", (int(time.time()) - 86400, (datetime.now(timezone.utc) - __import__("datetime").timedelta(days=7)).astimezone().isoformat(timespec="seconds")))
                if expired:
                    logger.info("Expired %s inbound case email records according to retention policy", expired)
                if expired_share_intakes:
                    logger.info("Expired %s unclaimed share-sheet intakes", expired_share_intakes)
            except Exception as exc:  # cleanup failure should not stop serving normal app requests
                logger.warning("Inbound email retention sweep failed (%s)", type(exc).__name__)
            await asyncio.sleep(3600)

    retention_task = asyncio.create_task(retention_sweeper())
    try:
        yield
    finally:
        retention_task.cancel()
        try:
            await retention_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="BolKeResolve API", version="0.5.0", lifespan=app_lifespan)

@app.middleware("http")
async def basic_security_headers(request, call_next):
    response = None
    path = request.url.path
    # Public shell/status and authentication routes remain available; personal APIs are gated in production.
    public_api_paths = {"/api/health", "/api/config", "/api/support-directory", "/api/auth/me", "/api/auth/login", "/api/auth/register", "/api/auth/logout", "/api/auth/verify-email", "/api/auth/verification/resend", "/api/auth/password-reset/request", "/api/auth/password-reset/confirm", "/api/extraction/preview", "/api/resolution/preview", "/api/webhooks/whatsapp", "/api/webhooks/twilio/whatsapp", "/api/webhooks/twilio/whatsapp/status", "/api/webhooks/inbound-email", "/api/shared-intake/preview", "/api/shared-intake/discard"}
    # Anonymous voice intake can incur paid STT calls, so production must opt in explicitly.
    public_voice_enabled = os.getenv("BOLKE_PUBLIC_VOICE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    if public_voice_enabled and os.getenv("GNANI_API_KEY", "").strip():
        public_api_paths.add("/api/voice/transcribe")
    is_private_api = path.startswith("/api/") and path not in public_api_paths
    user_marker = None
    if AUTH_REQUIRED and request.method in {"POST", "PUT", "PATCH", "DELETE"} and path.startswith("/api/") and path not in {"/api/webhooks/whatsapp", "/api/webhooks/twilio/whatsapp", "/api/webhooks/twilio/whatsapp/status", "/api/webhooks/inbound-email", "/api/shared-intake/preview", "/api/shared-intake/discard"}:
        # Mutating requests from the shipped same-origin browser client include Origin.
        # Reject missing Origin as well as a cross-origin value in authenticated mode.
        origin = request.headers.get("origin", "").strip()
        expected_host = request.headers.get("host", "").lower()
        origin_is_valid = is_allowed_browser_origin(origin, expected_host)
        if not origin_is_valid:
            response = JSONResponse({"detail": "Request origin is missing or not allowed."}, status_code=403)
    if response is None and is_private_api:
        # Resolve an optional account session in development as well as mandatory
        # production mode. Handlers then scope every case lookup to that owner.
        token = request.cookies.get(SESSION_COOKIE_NAME, "")
        user_id = lookup_session_user(token) if token else None
        if AUTH_REQUIRED and not user_id:
            response = JSONResponse({"detail": "Please sign in to access your private cases."}, status_code=401)
        elif user_id:
            user_marker = CURRENT_USER_ID.set(user_id)
            try:
                response = await call_next(request)
            finally:
                CURRENT_USER_ID.reset(user_marker)
        else:
            response = await call_next(request)
    elif response is None:
        response = await call_next(request)
    if path.startswith("/api/") or path == "/" or path.endswith(("/app.js", "/share-token.js", "/styles.css", "/design-v2.css", "/index.html")):
        # API payloads may include case, evidence, account, or provider-event data.
        # Keep them out of shared/browser caches even when a future handler forgets
        # to set route-specific cache headers.
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    if path == "/" and (request.query_params.get("shared_intake") or request.query_params.get("verify_email") or request.query_params.get("reset_password")):
        # One-time bearer links must never be forwarded to third-party resources.
        response.headers["Referrer-Policy"] = "no-referrer"
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(self), microphone=(self), display-capture=(self), geolocation=(), payment=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https://images.pexels.com; connect-src 'self' ws: wss:; media-src 'self' blob:; form-action 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'")
    if DEPLOYMENT_ENV == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


MAX_AUDIO_BYTES = 12 * 1024 * 1024
MAX_EVIDENCE_BYTES = 8 * 1024 * 1024
CASE_STAGES = ("Needs next step", "Contacted support", "Awaiting response", "Follow-up needed", "Resolved (user-reported)")
ALLOWED_EVIDENCE = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".webm": "video/webm",
    ".mp4": "video/mp4",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".csv": "text/csv",
}
LANGUAGES = {
    "hi-IN": "Hindi",
    "en-IN": "English (India)",
    "mr-IN": "Marathi",
    "bn-IN": "Bengali",
    "gu-IN": "Gujarati",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "pa-IN": "Punjabi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
}
# Official Timbre v2.5 voice catalog: use a voice optimised for the chosen language.
# Source: https://docs.gnani.ai/api/TTS/available-voices (reviewed 2026-10-17).
TTS_VOICES_BY_LANGUAGE = {
    "en-IN": ("Kaveri", "Trupti", "Devika", "Pranav", "Shlok", "Girish"),
    "hi-IN": ("Nalini", "Bhavna", "Yashvi", "Urmila", "Jwala", "Chitra", "Ambuja", "Deepak", "Roopesh", "Vikrant", "Hemraj", "Jalaj", "Omkar"),
    "hi-en": ("Poorvi",),
    "ta-IN": ("Asmita", "Trisha", "Brinda", "Vedika", "Noopur"),
    "te-IN": ("Suhana", "Lehara", "Lavanya", "Yukti", "Varuni"),
    "kn-IN": ("Saanvi", "Kavin"),
    "ml-IN": ("Reshma", "Riyaan"),
    "mr-IN": ("Zahira", "Ishaan"),
    "bn-IN": ("Kirra", "Dhruva"),
    "gu-IN": ("Falak", "Veera"),
    "pa-IN": ("Mehuli", "Zayan"),
}
TTS_DEFAULT_VOICE = {language: voices[0] for language, voices in TTS_VOICES_BY_LANGUAGE.items()}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def validate_payment_date(value: str) -> None:
    """Accept an empty date or a real ISO calendar date from the date input."""
    if not value:
        return
    try:
        date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=422, detail="Payment date must be a valid YYYY-MM-DD date.")


@contextmanager
def get_db():
    con = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout = 10000")
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA synchronous = NORMAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    with get_db() as con:
        # WAL supports concurrent local readers/writers better than SQLite's default journal.
        con.execute("PRAGMA journal_mode = WAL")
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                email_verified INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                expires_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);
            CREATE TABLE IF NOT EXISTS auth_rate_limit_attempts (
                attempt_id TEXT PRIMARY KEY,
                action_key TEXT NOT NULL,
                ip_hash TEXT NOT NULL,
                attempted_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_auth_rate_limit_lookup ON auth_rate_limit_attempts(action_key, ip_hash, attempted_at);
            CREATE TABLE IF NOT EXISTS auth_action_tokens (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                token_type TEXT NOT NULL CHECK(token_type IN ('email_verification','password_reset')),
                created_at TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                consumed_at TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_auth_action_tokens_expiry ON auth_action_tokens(expires_at, consumed_at);
            CREATE TABLE IF NOT EXISTS audit_events (
                audit_event_id TEXT PRIMARY KEY,
                case_id TEXT REFERENCES cases(case_id) ON DELETE SET NULL,
                user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
                event_type TEXT NOT NULL,
                target_type TEXT NOT NULL DEFAULT '',
                target_id TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_audit_events_case ON audit_events(case_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_audit_events_user ON audit_events(user_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS case_exports (
                export_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
                export_mode TEXT NOT NULL CHECK(export_mode IN ('complete','share')),
                included_evidence_json TEXT NOT NULL DEFAULT '[]',
                redaction_requested INTEGER NOT NULL DEFAULT 0,
                manifest_sha256 TEXT NOT NULL DEFAULT '',
                package_sha256 TEXT NOT NULL DEFAULT '',
                package_filename TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_case_exports_case ON case_exports(case_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                owner_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                merchant TEXT NOT NULL DEFAULT '',
                amount REAL,
                payment_date TEXT NOT NULL DEFAULT '',
                language_code TEXT NOT NULL DEFAULT 'hi-IN',
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Received',
                case_stage TEXT NOT NULL DEFAULT 'Needs next step',
                payment_status TEXT NOT NULL DEFAULT 'unknown',
                contacted_support INTEGER,
                resolution_json TEXT NOT NULL DEFAULT '{}',
                redaction_json TEXT NOT NULL DEFAULT '[]',
                support_draft TEXT NOT NULL DEFAULT '',
                source_contact_hash TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conversation_turns (
                turn_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                speaker TEXT NOT NULL DEFAULT 'user' CHECK(speaker IN ('user','assistant','organisation','system')),
                text TEXT NOT NULL,
                language_code TEXT NOT NULL DEFAULT 'en-IN',
                input_source TEXT NOT NULL DEFAULT 'typed',
                transcript_confidence REAL,
                source_evidence_id TEXT REFERENCES evidence(evidence_id) ON DELETE SET NULL,
                session_id TEXT NOT NULL DEFAULT '',
                user_confirmed INTEGER NOT NULL DEFAULT 1,
                supersedes_turn_id TEXT REFERENCES conversation_turns(turn_id) ON DELETE SET NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_conversation_turns_case ON conversation_turns(case_id, created_at, turn_id);
            CREATE TABLE IF NOT EXISTS evidence_derivatives (
                derivative_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
                derivative_type TEXT NOT NULL,
                mime_type TEXT NOT NULL DEFAULT 'application/json',
                content_text TEXT NOT NULL DEFAULT '',
                content_json TEXT NOT NULL DEFAULT '{}',
                content_sha256 TEXT NOT NULL DEFAULT '',
                processor TEXT NOT NULL DEFAULT '',
                processor_version TEXT NOT NULL DEFAULT '',
                source_range_json TEXT NOT NULL DEFAULT '{}',
                processing_status TEXT NOT NULL DEFAULT 'complete',
                review_status TEXT NOT NULL DEFAULT 'needs_review',
                supersedes_derivative_id TEXT REFERENCES evidence_derivatives(derivative_id) ON DELETE SET NULL,
                created_at TEXT NOT NULL,
                confirmed_at TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_derivatives_case ON evidence_derivatives(case_id, evidence_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS timeline (
                event_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                actor TEXT NOT NULL DEFAULT 'system',
                channel TEXT NOT NULL DEFAULT 'web',
                source TEXT NOT NULL DEFAULT 'bolkeresolve',
                metadata_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS case_checklist_state (
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                task_key TEXT NOT NULL,
                checked INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (case_id, task_key)
            );
            CREATE TABLE IF NOT EXISTS case_followups (
                case_id TEXT PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
                due_date TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                reminder_sent_for TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS whatsapp_contacts (
                phone_hash TEXT PRIMARY KEY,
                phone_ciphertext TEXT NOT NULL,
                owner_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
                consent_at TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS whatsapp_sessions (
                phone_hash TEXT PRIMARY KEY REFERENCES whatsapp_contacts(phone_hash) ON DELETE CASCADE,
                state TEXT NOT NULL DEFAULT 'idle',
                pending_story TEXT NOT NULL DEFAULT '',
                active_case_id TEXT REFERENCES cases(case_id) ON DELETE SET NULL,
                language_code TEXT NOT NULL DEFAULT 'hi-IN',
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS whatsapp_case_links (
                phone_hash TEXT NOT NULL REFERENCES whatsapp_contacts(phone_hash) ON DELETE CASCADE,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                PRIMARY KEY (phone_hash, case_id)
            );
            CREATE TABLE IF NOT EXISTS whatsapp_link_tokens (
                token_hash TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                owner_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
                expires_at INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                consumed_at TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_whatsapp_link_expiry ON whatsapp_link_tokens(expires_at, consumed_at);
            CREATE TABLE IF NOT EXISTS whatsapp_webhook_messages (
                message_id TEXT PRIMARY KEY,
                phone_hash TEXT NOT NULL,
                reply_text TEXT NOT NULL DEFAULT '',
                case_id TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'processing',
                created_at TEXT NOT NULL,
                reply_sent_at TEXT NOT NULL DEFAULT '',
                lease_until INTEGER NOT NULL DEFAULT 0,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error_type TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS whatsapp_outbound_messages (
                message_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                purpose TEXT NOT NULL DEFAULT 'reminder',
                status TEXT NOT NULL DEFAULT 'accepted',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                error_code TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_whatsapp_outbound_case ON whatsapp_outbound_messages(case_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS reminder_delivery_claims (
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                followup_updated_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'sending',
                lease_until INTEGER NOT NULL DEFAULT 0,
                attempts INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                last_error_type TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (case_id, followup_updated_at)
            );
            CREATE TABLE IF NOT EXISTS case_outcomes (
                case_id TEXT PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
                outcome_code TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                reference TEXT NOT NULL DEFAULT '',
                provenance TEXT NOT NULL DEFAULT 'user_reported',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence_fact_reviews (
                review_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
                candidates_json TEXT NOT NULL DEFAULT '{}',
                conflicts_json TEXT NOT NULL DEFAULT '[]',
                extraction_method TEXT NOT NULL DEFAULT 'unknown',
                status TEXT NOT NULL DEFAULT 'previewed',
                created_at TEXT NOT NULL,
                confirmed_at TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_reviews_case ON evidence_fact_reviews(case_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS case_fact_sources (
                fact_source_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
                review_id TEXT NOT NULL REFERENCES evidence_fact_reviews(review_id) ON DELETE CASCADE,
                field_key TEXT NOT NULL,
                field_value_json TEXT NOT NULL,
                source_label TEXT NOT NULL DEFAULT 'User-uploaded evidence; not independently verified',
                applied_to_case INTEGER NOT NULL DEFAULT 0,
                confirmed_at TEXT NOT NULL,
                UNIQUE(review_id, field_key)
            );
            CREATE INDEX IF NOT EXISTS idx_fact_sources_case ON case_fact_sources(case_id, confirmed_at DESC);
            CREATE TABLE IF NOT EXISTS live_room_evidence_analyses (
                analysis_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
                model_name TEXT NOT NULL DEFAULT '',
                result_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'previewed',
                created_at TEXT NOT NULL,
                confirmed_at TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_live_room_analyses_case ON live_room_evidence_analyses(case_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS case_commitments (
                commitment_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                source_type TEXT NOT NULL,
                source_label TEXT NOT NULL DEFAULT '',
                source_excerpt_redacted TEXT NOT NULL DEFAULT '',
                source_hash TEXT NOT NULL DEFAULT '',
                source_evidence_id TEXT REFERENCES evidence(evidence_id) ON DELETE SET NULL,
                source_authenticity_verified INTEGER NOT NULL DEFAULT 0,
                speech_act TEXT NOT NULL,
                action_code TEXT NOT NULL DEFAULT 'unknown_action',
                action_text TEXT NOT NULL,
                amount_minor_units INTEGER,
                currency TEXT NOT NULL DEFAULT 'INR',
                condition_text TEXT NOT NULL DEFAULT '',
                trigger_type TEXT NOT NULL DEFAULT 'unspecified',
                duration_value INTEGER,
                duration_max_value INTEGER,
                duration_unit TEXT NOT NULL DEFAULT '',
                day_type TEXT NOT NULL DEFAULT 'unspecified',
                qualifier TEXT NOT NULL DEFAULT 'stated_by_speaker',
                statement_date TEXT NOT NULL DEFAULT '',
                review_state TEXT NOT NULL DEFAULT 'user_confirmed',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_commitments_case ON case_commitments(case_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS commitment_events (
                event_id TEXT PRIMARY KEY,
                commitment_id TEXT NOT NULL REFERENCES case_commitments(commitment_id) ON DELETE CASCADE,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                event_type TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'user_update',
                evidence_id TEXT REFERENCES evidence(evidence_id) ON DELETE SET NULL,
                source_excerpt_redacted TEXT NOT NULL DEFAULT '',
                relation TEXT NOT NULL DEFAULT 'unknown',
                evidence_status TEXT NOT NULL DEFAULT 'user_confirmed',
                event_date_claimed TEXT NOT NULL DEFAULT '',
                event_date_confirmed TEXT NOT NULL DEFAULT '',
                details_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                reviewed_by_user_at TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_commitment_events_case ON commitment_events(case_id, commitment_id, created_at ASC);
            CREATE TABLE IF NOT EXISTS case_inboxes (
                case_id TEXT PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
                alias_hash TEXT NOT NULL UNIQUE,
                alias_ciphertext TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_received_at TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS inbound_email_messages (
                inbound_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                provider_message_id TEXT NOT NULL UNIQUE,
                sender_domain TEXT NOT NULL DEFAULT '',
                subject_ciphertext TEXT NOT NULL DEFAULT '',
                body_ciphertext TEXT NOT NULL DEFAULT '',
                received_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending_review',
                attachments_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                reviewed_at TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_inbound_email_case_pending ON inbound_email_messages(case_id, status, received_at DESC);
            CREATE TABLE IF NOT EXISTS case_fact_ledger (
                fact_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                fact_key TEXT NOT NULL,
                fact_value_json TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'user_reported',
                source_event_id TEXT NOT NULL DEFAULT '',
                source_excerpt_redacted TEXT NOT NULL DEFAULT '',
                confidence TEXT NOT NULL DEFAULT 'reported',
                is_current INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_case_fact_ledger_current ON case_fact_ledger(case_id, fact_key, is_current, created_at DESC);
            CREATE TABLE IF NOT EXISTS evidence_claim_links (
                link_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
                claim_key TEXT NOT NULL,
                claim_label TEXT NOT NULL,
                relation TEXT NOT NULL CHECK(relation IN ('supports','contradicts','context')),
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                UNIQUE(evidence_id, claim_key, relation)
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_claim_links_case ON evidence_claim_links(case_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS product_quality_events (
                event_id TEXT PRIMARY KEY,
                case_id TEXT REFERENCES cases(case_id) ON DELETE CASCADE,
                event_name TEXT NOT NULL,
                issue_family TEXT NOT NULL DEFAULT '',
                workflow_stage TEXT NOT NULL DEFAULT '',
                channel TEXT NOT NULL DEFAULT 'web',
                duration_ms INTEGER,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_quality_events_created ON product_quality_events(created_at DESC, event_name);
            CREATE TABLE IF NOT EXISTS reconciliation_imports (
                import_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
                provider TEXT NOT NULL DEFAULT 'Unspecified provider',
                status TEXT NOT NULL DEFAULT 'previewed',
                preview_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                confirmed_at TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_reconciliation_imports_case ON reconciliation_imports(case_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS pending_share_intakes (
                token_hash TEXT PRIMARY KEY,
                title_ciphertext TEXT NOT NULL DEFAULT '',
                text_ciphertext TEXT NOT NULL DEFAULT '',
                url_ciphertext TEXT NOT NULL DEFAULT '',
                filename_ciphertext TEXT NOT NULL DEFAULT '',
                mime_type TEXT NOT NULL DEFAULT '',
                file_ciphertext BLOB,
                size_bytes INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                consumed_at TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_pending_share_expiry ON pending_share_intakes(expires_at);
            """
        )
        # Lightweight migrations keep existing local MVP databases usable.
        user_columns = {row["name"] for row in con.execute("PRAGMA table_info(users)").fetchall()}
        if "password_iterations" not in user_columns:
            con.execute("ALTER TABLE users ADD COLUMN password_iterations INTEGER NOT NULL DEFAULT 310000")
        if "password_algorithm" not in user_columns:
            con.execute("ALTER TABLE users ADD COLUMN password_algorithm TEXT NOT NULL DEFAULT 'pbkdf2_sha256'")
        if "email_verified" not in user_columns:
            # Existing accounts predate email verification; preserve their access.
            con.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 1")
        existing = {row["name"] for row in con.execute("PRAGMA table_info(cases)").fetchall()}
        migrations = {
            "owner_id": "ALTER TABLE cases ADD COLUMN owner_id TEXT REFERENCES users(user_id) ON DELETE CASCADE",
            "case_stage": "ALTER TABLE cases ADD COLUMN case_stage TEXT NOT NULL DEFAULT 'Needs next step'",
            "payment_status": "ALTER TABLE cases ADD COLUMN payment_status TEXT NOT NULL DEFAULT 'unknown'",
            "contacted_support": "ALTER TABLE cases ADD COLUMN contacted_support INTEGER",
            "resolution_json": "ALTER TABLE cases ADD COLUMN resolution_json TEXT NOT NULL DEFAULT '{}'",
            "redaction_json": "ALTER TABLE cases ADD COLUMN redaction_json TEXT NOT NULL DEFAULT '[]'",
            "source_contact_hash": "ALTER TABLE cases ADD COLUMN source_contact_hash TEXT NOT NULL DEFAULT ''",
        }
        for column, statement in migrations.items():
            if column not in existing:
                con.execute(statement)
        evidence_columns = {row["name"] for row in con.execute("PRAGMA table_info(evidence)").fetchall()}
        for column, statement in {
            "capture_source": "ALTER TABLE evidence ADD COLUMN capture_source TEXT NOT NULL DEFAULT 'user_upload'",
            "captured_at": "ALTER TABLE evidence ADD COLUMN captured_at TEXT NOT NULL DEFAULT ''",
            "session_id": "ALTER TABLE evidence ADD COLUMN session_id TEXT NOT NULL DEFAULT ''",
            "sha256": "ALTER TABLE evidence ADD COLUMN sha256 TEXT NOT NULL DEFAULT ''",
            "scan_status": "ALTER TABLE evidence ADD COLUMN scan_status TEXT NOT NULL DEFAULT 'not_scanned'",
        }.items():
            if column not in evidence_columns:
                con.execute(statement)
        whatsapp_session_columns = {row["name"] for row in con.execute("PRAGMA table_info(whatsapp_sessions)").fetchall()}
        if "language_code" not in whatsapp_session_columns:
            con.execute("ALTER TABLE whatsapp_sessions ADD COLUMN language_code TEXT NOT NULL DEFAULT 'hi-IN'")
        timeline_columns = {row["name"] for row in con.execute("PRAGMA table_info(timeline)").fetchall()}
        for column, statement in {
            "actor": "ALTER TABLE timeline ADD COLUMN actor TEXT NOT NULL DEFAULT 'system'",
            "channel": "ALTER TABLE timeline ADD COLUMN channel TEXT NOT NULL DEFAULT 'web'",
            "source": "ALTER TABLE timeline ADD COLUMN source TEXT NOT NULL DEFAULT 'bolkeresolve'",
            "metadata_json": "ALTER TABLE timeline ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'",
        }.items():
            if column not in timeline_columns:
                con.execute(statement)
        followup_columns = {row["name"] for row in con.execute("PRAGMA table_info(case_followups)").fetchall()}
        if "reminder_sent_for" not in followup_columns:
            con.execute("ALTER TABLE case_followups ADD COLUMN reminder_sent_for TEXT NOT NULL DEFAULT ''")
        # Recoverable webhook claims: stale processing/sending rows can be reclaimed
        # when Meta retries the same message ID after a process/network failure.
        webhook_columns = {row["name"] for row in con.execute("PRAGMA table_info(whatsapp_webhook_messages)").fetchall()}
        for column, statement in {
            "lease_until": "ALTER TABLE whatsapp_webhook_messages ADD COLUMN lease_until INTEGER NOT NULL DEFAULT 0",
            "attempts": "ALTER TABLE whatsapp_webhook_messages ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0",
            "last_error_type": "ALTER TABLE whatsapp_webhook_messages ADD COLUMN last_error_type TEXT NOT NULL DEFAULT ''",
        }.items():
            if column not in webhook_columns:
                con.execute(statement)
        con.execute("CREATE INDEX IF NOT EXISTS idx_whatsapp_webhook_lease ON whatsapp_webhook_messages(status, lease_until)")
        # Provider identifiers are kept alongside the shared workflow so adding a
        # second adapter never creates a parallel case store.
        webhook_columns = {row["name"] for row in con.execute("PRAGMA table_info(whatsapp_webhook_messages)").fetchall()}
        if "provider" not in webhook_columns:
            con.execute("ALTER TABLE whatsapp_webhook_messages ADD COLUMN provider TEXT NOT NULL DEFAULT 'meta'")
        outbound_columns = {row["name"] for row in con.execute("PRAGMA table_info(whatsapp_outbound_messages)").fetchall()}
        if "provider" not in outbound_columns:
            con.execute("ALTER TABLE whatsapp_outbound_messages ADD COLUMN provider TEXT NOT NULL DEFAULT 'meta'")


init_db()


class CaseCreate(BaseModel):
    issue_type: str = Field(min_length=2, max_length=80)
    merchant: str = Field(default="", max_length=100)
    amount: Optional[float] = Field(default=None, ge=0, le=100000000)
    payment_date: str = Field(default="", max_length=10, pattern=r"^(?:\d{4}-\d{2}-\d{2})?$")
    language_code: str = Field(default="hi-IN", max_length=15)
    payment_status: Literal["unknown", "failed", "pending", "successful", "refund_pending", "unauthorized"] = "unknown"
    contacted_support: Optional[bool] = None
    description: str = Field(min_length=8, max_length=5000)




class CaseDetailsUpdate(CaseCreate):
    """Full editable case facts; saving recalculates the guidance from the edited story."""

class ResolutionPreviewRequest(BaseModel):
    issue_type: str = Field(default="Other payment issue", min_length=2, max_length=80)
    merchant: str = Field(default="", max_length=100)
    amount: Optional[float] = Field(default=None, ge=0, le=100000000)
    payment_date: str = Field(default="", max_length=10, pattern=r"^(?:\d{4}-\d{2}-\d{2})?$")
    payment_status: Literal["unknown", "failed", "pending", "successful", "refund_pending", "unauthorized"] = "unknown"
    contacted_support: Optional[bool] = None
    description: str = Field(min_length=8, max_length=5000)


class ExtractPreviewRequest(BaseModel):
    description: str = Field(min_length=3, max_length=5000)


class SharedIntakeAttachRequest(BaseModel):
    """Constant-path attach request; capability token is carried only in a header."""
    case_id: str = Field(min_length=8, max_length=40, pattern=r"^BR-[A-Za-z0-9]{8,20}$")
    include_context: bool = True


class CaseProgressUpdate(BaseModel):
    case_stage: Literal[
        "Needs next step", "Contacted support", "Awaiting response",
        "Follow-up needed", "Resolved (user-reported)"
    ]
    note: str = Field(default="", max_length=500)


class DraftRequest(BaseModel):
    language: str = Field(default="en", pattern="^(en|hi|hinglish)$")


class DraftEditRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class ChecklistItemUpdate(BaseModel):
    checked: bool


class EvidenceClaimLinkRequest(BaseModel):
    claim_key: Literal["issue", "order", "payment", "refund_promise", "refund_status", "settlement", "support_contact", "support_reply", "bank_credit", "reference", "other"]
    claim_label: str = Field(min_length=2, max_length=120)
    relation: Literal["supports", "contradicts", "context"] = "supports"
    note: str = Field(default="", max_length=300)


class ReconciliationConfirmRequest(BaseModel):
    confirmed: bool = False
    selected_rows: list[int] = Field(default_factory=list, max_length=5000)


class FollowupUpdate(BaseModel):
    due_date: str = Field(default="", max_length=10, pattern=r"^(?:\d{4}-\d{2}-\d{2})?$")
    note: str = Field(default="", max_length=300)
    completed: bool = False


class TimelineCreate(BaseModel):
    message: str = Field(min_length=3, max_length=1000)


class ReplyReviewRequest(BaseModel):
    reply_text: str = Field(min_length=8, max_length=8000)


class ReplyReviewConfirmRequest(ReplyReviewRequest):
    reference: str = Field(default="", max_length=120)
    confirmed: bool = False


class LiveRoomDraftRequest(BaseModel):
    language_code: str = Field(default="indic-auto", max_length=15)
    session_id: str = Field(min_length=8, max_length=80)
    started_at: str = Field(default="", max_length=40)
    allow_ai_assistance: bool = False
    allow_ai_case_interpretation: bool = False


class LiveRoomCaseInterpretationConsentRequest(BaseModel):
    allowed: bool = False
    session_id: str = Field(default="", max_length=80)


class LiveRoomEvidenceAnalysisRequest(BaseModel):
    consent_to_external_processing: bool = False
    question: str = Field(default="", max_length=500)


class LiveRoomEvidenceAnalysisConfirmRequest(BaseModel):
    analysis_id: str = Field(min_length=16, max_length=80)
    confirmed: bool = False
    accepted_fields: list[str] = Field(default_factory=list, max_length=8)
    apply_fields: list[str] = Field(default_factory=list, max_length=4)


class LiveRoomTurnRequest(BaseModel):
    text: str = Field(min_length=2, max_length=4000)
    language_code: str = Field(default="en-IN", max_length=15)
    session_id: str = Field(default="", max_length=80)
    input_source: Literal["typed", "live_speech", "imported_call_recording", "user_note"] = "typed"


class LiveRoomGuidanceRequest(BaseModel):
    language_code: str = Field(default="en-IN", max_length=15)
    session_id: str = Field(default="", max_length=80)
    finish_intake: bool = False


class LiveRoomSessionEventRequest(BaseModel):
    event: Literal["started", "ended"]
    session_id: str = Field(default="", max_length=80)
    started_at: str = Field(default="", max_length=40)


class EvidenceReviewConfirmRequest(BaseModel):
    review_id: str = Field(min_length=16, max_length=80)
    accepted_fields: list[str] = Field(default_factory=list, max_length=8)
    apply_fields: list[str] = Field(default_factory=list, max_length=8)
    confirmed: bool = False


class InboundEmailConfirmRequest(BaseModel):
    reference: str = Field(default="", max_length=120)
    confirmed: bool = False


class CommitmentPreviewRequest(BaseModel):
    text: str = Field(min_length=8, max_length=4000)
    source_type: Literal["support_call_transcript", "support_email", "chat_message", "user_note", "case_evidence"] = "support_call_transcript"


class CommitmentConfirmRequest(BaseModel):
    confirmed: bool = False
    source_type: Literal["support_call_transcript", "support_email", "chat_message", "user_note", "case_evidence"]
    source_label: str = Field(default="", max_length=120)
    source_excerpt: str = Field(min_length=8, max_length=1200)
    source_evidence_id: str = Field(default="", max_length=80)
    speech_act: Literal["conditional_process_commitment", "process_commitment", "estimated_timeline", "request_or_process_step", "unclassified_statement"]
    action_code: str = Field(min_length=2, max_length=80)
    action_text: str = Field(min_length=2, max_length=200)
    amount_minor_units: Optional[int] = Field(default=None, ge=0, le=10000000000000)
    currency: Literal["INR"] = "INR"
    condition_text: str = Field(default="", max_length=300)
    trigger_type: Literal["condition_met", "statement_date", "unspecified"] = "unspecified"
    duration_value: Optional[int] = Field(default=None, ge=0, le=3650)
    duration_max_value: Optional[int] = Field(default=None, ge=0, le=3650)
    duration_unit: Literal["", "day", "week", "hour"] = ""
    day_type: Literal["unspecified", "calendar_day", "business_day"] = "unspecified"
    qualifier: str = Field(default="stated_by_speaker", max_length=50)
    statement_date: str = Field(default="", max_length=10, pattern=r"^(?:\d{4}-\d{2}-\d{2})?$")


class CommitmentReconcileRequest(BaseModel):
    event_text: str = Field(min_length=3, max_length=1500)
    relation: Literal["supports", "contradicts", "qualifies", "triggers", "fulfils", "supersedes", "unrelated", "unknown"] = "unknown"
    evidence_status: Literal["user_reported", "user_confirmed", "document_reviewed_by_user"] = "user_confirmed"
    evidence_id: str = Field(default="", max_length=80)
    event_date_claimed: str = Field(default="", max_length=10, pattern=r"^(?:\d{4}-\d{2}-\d{2})?$")
    event_date_confirmed: str = Field(default="", max_length=10, pattern=r"^(?:\d{4}-\d{2}-\d{2})?$")
    details: str = Field(default="", max_length=300)


class CaseEventCreate(BaseModel):
    event_type: Literal["contacted_support", "still_waiting", "submission_reported", "response_received", "resolved", "not_resolved", "official_channel_opened"]
    details: str = Field(default="", max_length=1000)
    reference: str = Field(default="", max_length=120)


class CaseOutcomeUpdate(BaseModel):
    outcome_code: Literal["still_pending", "no_response", "partially_resolved", "resolved", "stopped"]
    details: str = Field(default="", max_length=1000)
    reference: str = Field(default="", max_length=120)


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1500)
    language_code: str = Field(default="hi-IN", max_length=15)
    voice: str = Field(default="", max_length=40)


class AuthRegisterRequest(BaseModel):
    email: str = Field(min_length=6, max_length=254)
    password: str = Field(min_length=12, max_length=128)


class AuthLoginRequest(BaseModel):
    email: str = Field(min_length=6, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class AccountDeleteRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class AuthEmailRequest(BaseModel):
    email: str = Field(min_length=6, max_length=254)


class AuthTokenRequest(BaseModel):
    token: str = Field(min_length=24, max_length=256)


class PasswordResetRequest(AuthTokenRequest):
    new_password: str = Field(min_length=12, max_length=128)


class ConversationTurnCorrectionRequest(BaseModel):
    text: str = Field(min_length=2, max_length=4000)


def safe_case_id() -> str:
    return "BR-" + uuid.uuid4().hex[:10].upper()


def inbound_email_capability() -> dict[str, object]:
    """Expose feature readiness without disclosing domains' secrets or credentials."""
    domain = os.getenv("BOLKE_INBOUND_EMAIL_DOMAIN", "").strip().lower().rstrip(".")
    domain_ok = bool(re.fullmatch(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", domain))
    enc_key = os.getenv("BOLKE_INBOUND_EMAIL_ENCRYPTION_KEY", "").strip()
    encryption_ok = False
    if enc_key:
        try:
            Fernet(enc_key.encode("ascii"))
            encryption_ok = True
        except (ValueError, UnicodeEncodeError):
            encryption_ok = False
    bearer_value = os.getenv("BOLKE_INBOUND_WEBHOOK_TOKEN", "").strip()
    basic_username = os.getenv("BOLKE_INBOUND_WEBHOOK_USERNAME", "").strip()
    basic_password = os.getenv("BOLKE_INBOUND_WEBHOOK_PASSWORD", "").strip()
    # A webhook credential is a remote capability: reject short/shared defaults rather
    # than enabling an Internet-facing receiver with weak authentication.
    has_bearer = len(bearer_value) >= 32
    has_basic = len(basic_username) >= 8 and len(basic_password) >= 24
    webhook_auth_ok = has_bearer or has_basic
    return {
        "enabled": bool(domain_ok and encryption_ok and webhook_auth_ok),
        "domain_configured": domain_ok,
        "encryption_configured": encryption_ok,
        "webhook_auth_configured": webhook_auth_ok,
        "provider": "generic inbound email webhook",
        "notice": "Only configure this over HTTPS. Forwarded email text is encrypted temporarily and requires user review; email sender identity is not independently verified.",
    }


def inbound_email_fernet() -> Fernet:
    key = os.getenv("BOLKE_INBOUND_EMAIL_ENCRYPTION_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="Case Inbox Bridge is not configured for encrypted storage.")
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise HTTPException(status_code=503, detail="Case Inbox Bridge encryption key is invalid. Ask the operator to check its configuration.") from exc


def _inbound_webhook_authorized(request: Request) -> bool:
    """Support a configured bearer token or constant-time HTTP Basic comparison."""
    header = request.headers.get("authorization", "")
    bearer = os.getenv("BOLKE_INBOUND_WEBHOOK_TOKEN", "").strip()
    if bearer and header.lower().startswith("bearer "):
        provided = header[7:].strip()
        return hmac.compare_digest(provided, bearer)
    username = os.getenv("BOLKE_INBOUND_WEBHOOK_USERNAME", "")
    password = os.getenv("BOLKE_INBOUND_WEBHOOK_PASSWORD", "")
    if username and password and header.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(header[6:].strip(), validate=True).decode("utf-8")
            user, separator, secret = decoded.partition(":")
            return bool(separator and hmac.compare_digest(user, username) and hmac.compare_digest(secret, password))
        except (ValueError, UnicodeDecodeError):
            return False
    return False


def _inbound_alias_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _safe_email_body(payload: dict) -> str:
    # Bound parser/scrubber work independently of the 12 MB webhook payload cap.
    # The UI only needs a short excerpt to classify a reply, not a full mailbox archive.
    body = str(payload.get("TextBody") or payload.get("text_body") or "")[:60000]
    if not body:
        html_body = str(payload.get("HtmlBody") or payload.get("html_body") or "")
        # Remove non-content blocks before truncation so their tail cannot become visible text.
        html_body = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", " ", html_body)
        html_body = html_body[:60000]
        body = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>|</tr>", "\n", html_body)
        body = re.sub(r"(?s)<[^>]+>", " ", body)
        body = html_lib.unescape(body)
    scrubbed = scrub_sensitive_text(body).text
    scrubbed = re.sub(r"[\t\r ]+", " ", scrubbed)
    scrubbed = re.sub(r"\n[ \t]+", "\n", scrubbed)
    return scrubbed[:12000].strip()


def inbound_email_retention_days() -> int:
    try:
        return max(1, min(30, int(os.getenv("BOLKE_INBOUND_EMAIL_RETENTION_DAYS", "14"))))
    except (ValueError, OverflowError):
        return 14


def _safe_nonnegative_size(value: object) -> int:
    raw = str(value or "0").strip()
    if not raw.isascii() or not raw.isdigit() or len(raw) > 12:
        return 0
    try:
        return max(0, min(100_000_000, int(raw)))
    except (ValueError, OverflowError):
        return 0


def _expire_inbound_email(con: sqlite3.Connection, case_id: str | None = None) -> int:
    days = inbound_email_retention_days()
    cutoff = (datetime.now(timezone.utc) - __import__("datetime").timedelta(days=days)).astimezone().isoformat(timespec="seconds")
    if case_id:
        cur = con.execute("DELETE FROM inbound_email_messages WHERE case_id = ? AND received_at < ?", (case_id, cutoff))
    else:
        cur = con.execute("DELETE FROM inbound_email_messages WHERE received_at < ?", (cutoff,))
    return cur.rowcount


def share_intake_retention_minutes() -> int:
    try:
        return max(5, min(60, int(os.getenv("BOLKE_SHARE_INTAKE_RETENTION_MINUTES", "30"))))
    except (ValueError, OverflowError):
        return 30


def share_intake_fernet() -> Fernet:
    """Use a configured production key; local development may create a private stable key file."""
    key = os.getenv("BOLKE_SHARE_INTAKE_ENCRYPTION_KEY", "").strip()
    if not key and DEPLOYMENT_ENV != "production":
        key_path = DATA_DIR / ".share-intake.key"
        try:
            fd = os.open(str(key_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "wb") as out:
                out.write(Fernet.generate_key())
        except FileExistsError:
            pass
        except OSError as exc:
            raise HTTPException(status_code=503, detail="Share-to-Case could not initialise its local encryption key.") from exc
        try:
            key = key_path.read_text(encoding="ascii").strip()
        except OSError as exc:
            raise HTTPException(status_code=503, detail="Share-to-Case local encryption key is unavailable.") from exc
    if not key:
        raise HTTPException(status_code=503, detail="Share-to-Case is not configured for encrypted storage. Set BOLKE_SHARE_INTAKE_ENCRYPTION_KEY on the server.")
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise HTTPException(status_code=503, detail="Share-to-Case encryption key is invalid. Generate a valid Fernet key and configure it on the server.") from exc


def share_intake_capability() -> dict[str, object]:
    try:
        share_intake_fernet()
        encryption_ready = True
    except HTTPException:
        encryption_ready = False
    return {
        "enabled": encryption_ready,
        "encrypted_staging_ready": encryption_ready,
        "retention_minutes": share_intake_retention_minutes(),
        "notice": "Share Target is available only on supported installed PWAs. Shared items are staged encrypted for a short period and never added to a case until you choose a case and confirm. Regular file upload remains available.",
    }


def _expire_shared_intakes(con: sqlite3.Connection) -> int:
    """Clear abandoned encrypted share payloads after a short TTL and drop old consumed tokens."""
    now = int(time.time())
    cur = con.execute("DELETE FROM pending_share_intakes WHERE expires_at < ? OR (consumed_at != '' AND created_at < ?)", (now, (datetime.now(timezone.utc) - __import__("datetime").timedelta(days=1)).astimezone().isoformat(timespec="seconds")))
    return cur.rowcount


def _safe_shared_filename(name: str) -> str:
    basename = Path(str(name or "shared-file").replace("\\", "/")).name
    basename = re.sub(r"[^A-Za-z0-9._() -]", "_", basename).strip(" .")[:160]
    return basename or "shared-file"


def _safe_shared_text(text: str) -> str:
    """Scrub credentials and strip path/query/fragment from URLs in shared text.

    Shared strings can be copied from password-reset, order-detail, or tracking emails.
    A URL token may be a bearer credential even when it does not look like an OTP/PIN.
    The full HTTPS URL is encrypted only when provided in the separate source-url field;
    the preview uses source_domain only.
    """
    def reduce_url(match: re.Match[str]) -> str:
        raw = match.group(0).rstrip(".,);]")
        suffix = match.group(0)[len(raw):]
        try:
            parsed = urlsplit(raw)
            if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
                return "[link removed]" + suffix
            host = parsed.hostname[:253]
            if parsed.port and parsed.port not in (443,):
                return f"https://{host}:{parsed.port} [link details removed]" + suffix
            if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
                return f"https://{host} [link path and query removed]" + suffix
            return f"https://{host}" + suffix
        except ValueError:
            return "[link removed]" + suffix

    # Remove dangerous URL components before the general credential scrubber, which may
    # otherwise leave a redaction marker beside a URL and obscure what was sanitized.
    safe = re.sub(r"https?://[^\s<>\"']+", reduce_url, str(text or ""), flags=re.IGNORECASE)
    safe = scrub_sensitive_text(safe).text
    # Catch common OTP wording in either order. Do not retain a one-time code merely
    # because the sender put the number before the word OTP.
    safe = re.sub(r"(?i)\b(?:otp|one[- ]?time(?: password| passcode| code)?)\b\s*(?:is|:|=|of)?\s*\d{4,8}\b", "OTP [redacted]", safe)
    safe = re.sub(r"(?i)\b\d{4,8}\s+(?:(?:is|as)\s+)?(?:your\s+)?(?:otp|one[- ]?time(?: password| passcode| code)?)\b", "[redacted OTP]", safe)
    safe = re.sub(r"(?i)\b(?:UPI\s*PIN|PIN)\s*(?:is|:|=)?\s*\d{4,6}\b", "PIN [redacted]", safe)
    safe = re.sub(r"(?i)\b\d{4,6}\s+(?:(?:is|as)\s+)?(?:your\s+)?(?:UPI\s*PIN|PIN)\b", "[redacted PIN]", safe)
    return safe[:6000]


def _validate_shared_evidence(filename: str, content: bytes) -> tuple[str, str]:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EVIDENCE:
        raise HTTPException(status_code=415, detail="Shared files must be PNG, JPG, WEBP or PDF. You can still use the case's normal upload control.")
    if not content:
        raise HTTPException(status_code=400, detail="The shared file is empty.")
    if len(content) > MAX_EVIDENCE_BYTES:
        raise HTTPException(status_code=413, detail="Shared files must be 8 MB or smaller.")
    signatures = {
        ".pdf": content.startswith(b"%PDF-"),
        ".jpg": content.startswith(b"\xff\xd8\xff"),
        ".jpeg": content.startswith(b"\xff\xd8\xff"),
        ".png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        ".webp": content.startswith(b"RIFF") and content[8:12] == b"WEBP",
    }
    if not signatures.get(ext, False):
        raise HTTPException(status_code=400, detail="The shared file type does not match its file signature.")
    return ext, ALLOWED_EVIDENCE[ext]


def _shared_intake_row(con: sqlite3.Connection, token: str) -> sqlite3.Row:
    if not re.fullmatch(r"[A-Za-z0-9_-]{30,100}", str(token or "")):
        raise HTTPException(status_code=404, detail="This shared item is unavailable or has expired.")
    _expire_shared_intakes(con)
    row = con.execute("SELECT * FROM pending_share_intakes WHERE token_hash=? AND consumed_at='' AND expires_at>=?", (hashlib.sha256(token.encode("utf-8")).hexdigest(), int(time.time()))).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="This shared item is unavailable or has expired. Share it again from the original app.")
    return row


def _decrypt_share_value(fernet: Fernet, value: str | bytes | None) -> str:
    if not value:
        return ""
    try:
        return fernet.decrypt(value.encode("ascii") if isinstance(value, str) else value).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="This shared item cannot be decrypted with the configured key. Restore the correct key or discard the item.") from exc


def check_gnani_key() -> str:
    key = os.getenv("GNANI_API_KEY", "").strip()
    if not key:
        raise HTTPException(
            status_code=503,
            detail="Voice input is temporarily unavailable. You can type your complaint instead.",
        )
    return key


def hash_password(password: str, salt_hex: str | None = None, iterations: int | None = None) -> tuple[str, str]:
    """Hash a password with versioned PBKDF2 parameters for safe upgrades.

    PBKDF2 remains available for installations that already use it. New hashes use
    the current OWASP-recommended PBKDF2-HMAC-SHA256 work factor; successful logins
    transparently upgrade older hashes without forcing a password reset.
    """
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    work_factor = int(iterations or PASSWORD_HASH_ITERATIONS)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, work_factor).hex()
    return salt.hex(), digest


def verify_password(password: str, salt_hex: str, expected_hash: str, iterations: int | None = None) -> bool:
    _, actual_hash = hash_password(password, salt_hex, iterations or PASSWORD_HASH_ITERATIONS)
    return hmac.compare_digest(actual_hash, expected_hash)


def lookup_session_user(token: str) -> str | None:
    if not token or len(token) > 256:
        return None
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with get_db() as con:
        row = con.execute(
            "SELECT user_id FROM sessions WHERE token_hash = ? AND expires_at > ?",
            (digest, int(time.time())),
        ).fetchone()
    return str(row["user_id"]) if row else None


def new_session(con: sqlite3.Connection, user_id: str) -> str:
    # Only the hash is stored; a database read alone does not reveal a usable session cookie.
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    created = now_iso()
    con.execute("DELETE FROM sessions WHERE expires_at <= ?", (int(time.time()),))
    con.execute(
        "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (digest, user_id, created, int(time.time()) + SESSION_MAX_AGE_SECONDS),
    )
    return token


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME, value=token, max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True, secure=COOKIE_SECURE, samesite="lax", path="/",
    )


def enforce_auth_rate_limit(request: Request, action: str) -> None:
    """Persistent SQLite rate limit shared by app workers on the same database.

    A reverse-proxy/WAF limit is still recommended at internet scale, but restarts
    and multiple FastAPI workers no longer reset this application-level counter.
    """
    address = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(address.encode("utf-8")).hexdigest()
    now = int(time.time())
    with get_db() as con:
        con.execute("DELETE FROM auth_rate_limit_attempts WHERE attempted_at < ?", (now - 900,))
        count = con.execute(
            "SELECT COUNT(*) FROM auth_rate_limit_attempts WHERE action_key=? AND ip_hash=? AND attempted_at>=?",
            (action, ip_hash, now - 900),
        ).fetchone()[0]
        if count >= 12:
            raise HTTPException(status_code=429, detail="Too many sign-in attempts. Please wait 15 minutes and try again.")
        con.execute(
            "INSERT INTO auth_rate_limit_attempts (attempt_id, action_key, ip_hash, attempted_at) VALUES (?, ?, ?, ?)",
            (uuid.uuid4().hex, action, ip_hash, now),
        )


def enforce_public_preview_rate_limit(request: Request, action: str, limit: int = 25, window_seconds: int = 60) -> None:
    """Bound anonymous preview traffic; add a shared gateway limit in hosted production.

    The preview endpoints intentionally remain available before sign-in so visitors can
    receive first-pass guidance. This in-memory guard is only a first line of defence.
    """
    address = request.client.host if request.client else "unknown"
    key = f"{action}:{address}"
    now = time.monotonic()
    attempts = [stamp for stamp in _PREVIEW_ATTEMPTS.get(key, []) if now - stamp < window_seconds]
    if len(attempts) >= limit:
        raise HTTPException(
            status_code=429,
            detail="Too many preview requests in a short time. Please wait a moment and try again.",
            headers={"Retry-After": str(window_seconds)},
        )
    attempts.append(now)
    _PREVIEW_ATTEMPTS[key] = attempts
    if len(_PREVIEW_ATTEMPTS) > 2000:
        cutoff = now - window_seconds
        for stale_key, stamps in list(_PREVIEW_ATTEMPTS.items()):
            kept = [stamp for stamp in stamps if stamp >= cutoff]
            if kept:
                _PREVIEW_ATTEMPTS[stale_key] = kept
            else:
                _PREVIEW_ATTEMPTS.pop(stale_key, None)


def enforce_voice_rate_limit(request: Request, action: str, limit: int, window_seconds: int = 60) -> None:
    """Small single-process throttle to avoid accidental paid API loops in the MVP.

    Hosted deployments should additionally enforce shared quotas at the proxy/API gateway,
    because this in-memory limiter is per worker and resets on restart.
    """
    address = request.client.host if request.client else "unknown"
    key = f"{action}:{address}"
    now = time.monotonic()
    attempts = [stamp for stamp in _VOICE_ATTEMPTS.get(key, []) if now - stamp < window_seconds]
    if len(attempts) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Voice service rate limit reached. Please wait a moment before trying again; text entry is still available.",
            headers={"Retry-After": str(window_seconds)},
        )
    attempts.append(now)
    _VOICE_ATTEMPTS[key] = attempts
    # Periodically discard expired keys so long-running local sessions do not grow forever.
    if len(_VOICE_ATTEMPTS) > 2000:
        cutoff = now - window_seconds
        for stale_key, stamps in list(_VOICE_ATTEMPTS.items()):
            kept = [stamp for stamp in stamps if stamp >= cutoff]
            if kept:
                _VOICE_ATTEMPTS[stale_key] = kept
            else:
                _VOICE_ATTEMPTS.pop(stale_key, None)


def require_case_access(con: sqlite3.Connection, case_id: str):
    user_id = CURRENT_USER_ID.get()
    if user_id:
        row = con.execute("SELECT * FROM cases WHERE case_id = ? AND owner_id = ?", (case_id, user_id)).fetchone()
    elif AUTH_REQUIRED:
        raise HTTPException(status_code=401, detail="Please sign in to access your private cases.")
    else:
        row = con.execute("SELECT * FROM cases WHERE case_id = ? AND owner_id IS NULL", (case_id,)).fetchone()
    if not row:
        # Use the same result for an unknown ID and another user's ID to avoid disclosing case existence.
        raise HTTPException(status_code=404, detail="Case not found")
    return row


def record_case_event(
    con: sqlite3.Connection,
    case_id: str,
    event_type: str,
    message: str,
    created_at: str | None = None,
    *,
    actor: str = "system",
    channel: str = "web",
    source: str = "bolkeresolve",
    metadata: dict | None = None,
) -> None:
    created_at = created_at or now_iso()
    con.execute(
        "INSERT INTO timeline (event_id, case_id, event_type, message, created_at, actor, channel, source, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (uuid.uuid4().hex, case_id, event_type, message, created_at, actor, channel, source, json.dumps(metadata or {}, ensure_ascii=False)),
    )


def record_audit_event(
    con: sqlite3.Connection, event_type: str, *, case_id: str | None = None,
    user_id: str | None = None, target_type: str = "", target_id: str = "", metadata: dict | None = None,
) -> None:
    """Append a privacy-minimised security/activity event; never store raw file contents."""
    con.execute(
        "INSERT INTO audit_events (audit_event_id, case_id, user_id, event_type, target_type, target_id, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (uuid.uuid4().hex, case_id, user_id or CURRENT_USER_ID.get(), str(event_type)[:80], str(target_type)[:60], str(target_id)[:120], json.dumps(metadata or {}, ensure_ascii=False), now_iso()),
    )


_QUALITY_EVENT_NAMES = {
    "case_created", "user_turn_saved", "workflow_guidance_generated", "workflow_question_shown",
    "workflow_question_repeated", "workflow_action_ready", "evidence_added", "evidence_claim_linked",
    "reconciliation_previewed", "reconciliation_confirmed", "followup_set", "outcome_reported",
    "semantic_interpretation_failed", "speech_commit_timeout",
}
_FACT_LEDGER_KEYS = {
    "merchant", "gateway_provider", "payment_app", "amount", "issue_type", "issue_family",
    "order_outcome", "refund_scope", "refund_status", "refund_reason", "item_count",
    "promised_timeline", "promised_days", "elapsed", "elapsed_days", "support_contacted",
    "support_reference", "payment_method", "transaction_status", "transaction_date",
    "settlement_status", "settlement_reference", "payment_id", "order_id", "utr",
}


def record_product_quality_event(
    con: sqlite3.Connection, event_name: str, *, case_id: str | None = None,
    issue_family: str = "", workflow_stage: str = "", channel: str = "web",
    duration_ms: int | None = None,
) -> None:
    """Store privacy-preserving product telemetry; never store user text or evidence."""
    if event_name not in _QUALITY_EVENT_NAMES:
        return
    safe_duration = None if duration_ms is None else max(0, min(int(duration_ms), 3_600_000))
    con.execute(
        "INSERT INTO product_quality_events (event_id, case_id, event_name, issue_family, workflow_stage, channel, duration_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (uuid.uuid4().hex, case_id, event_name, str(issue_family or "")[:60], str(workflow_stage or "")[:80], str(channel or "web")[:30], safe_duration, now_iso()),
    )


def record_case_fact_snapshot(
    con: sqlite3.Connection, case_id: str, facts: dict, *, source_type: str = "user_reported",
    source_event_id: str = "", source_excerpt: str = "", confidence: str = "reported",
) -> int:
    """Append changed case facts with provenance while preserving prior values for audit."""
    if not isinstance(facts, dict):
        return 0
    safe_excerpt = scrub_sensitive_text(str(source_excerpt or "")).text[:500]
    inserted = 0
    for key, value in facts.items():
        if key not in _FACT_LEDGER_KEYS or value in (None, "", [], {}):
            continue
        try:
            value_json = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError):
            continue
        current = con.execute(
            "SELECT fact_value_json FROM case_fact_ledger WHERE case_id=? AND fact_key=? AND is_current=1 ORDER BY created_at DESC LIMIT 1",
            (case_id, key),
        ).fetchone()
        if current and current["fact_value_json"] == value_json:
            continue
        con.execute("UPDATE case_fact_ledger SET is_current=0 WHERE case_id=? AND fact_key=? AND is_current=1", (case_id, key))
        con.execute(
            "INSERT INTO case_fact_ledger (fact_id, case_id, fact_key, fact_value_json, source_type, source_event_id, source_excerpt_redacted, confidence, is_current, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)",
            (uuid.uuid4().hex, case_id, key, value_json, str(source_type)[:40], str(source_event_id)[:80], safe_excerpt, str(confidence)[:30], now_iso()),
        )
        inserted += 1
    return inserted


def _language_from_text(text: str) -> str:
    text = str(text or "")
    for pattern, code in ((r"[\u0980-\u09FF]", "bn-IN"), (r"[\u0A00-\u0A7F]", "pa-IN"), (r"[\u0A80-\u0AFF]", "gu-IN"), (r"[\u0B80-\u0BFF]", "ta-IN"), (r"[\u0C00-\u0C7F]", "te-IN"), (r"[\u0C80-\u0CFF]", "kn-IN"), (r"[\u0D00-\u0D7F]", "ml-IN")):
        if re.search(pattern, text):
            return code
    if re.search(r"[\u0900-\u097F]", text):
        return "hi-IN"
    if re.search(r"\b(mera|meri|mujhe|paise|paisa|nahi|nahin|hai|refund nahi|paisa wapas)\b", text, re.I):
        return "hi-IN"
    return "en-IN"


def add_support_context(resolution: dict, merchant: str = "", description: str = "", amount: float | None = None) -> dict:
    """Attach curated first-party support destinations and an editable unsent draft."""
    classification = resolution.get("classification", {}) if isinstance(resolution, dict) else {}
    issue_type = str(classification.get("issue_type") or "Other payment issue")
    resolution["support_destinations"] = find_support_destinations(merchant, description, issue_type)
    resolution["suggested_support_draft"] = build_quick_support_draft(merchant, issue_type, description, amount)
    resolution["nch_directory_match"] = find_nch_convergence_match(merchant)
    if not resolution.get("rulebook"):
        from backend.rulebook import rulebook_metadata
        resolution["rulebook"] = rulebook_metadata(issue_type, "unknown", description)
    return resolution


def current_conversation_turn_texts(con: sqlite3.Connection, case_id: str) -> list[str]:
    """Return the latest version of each structured user turn, falling back to the legacy timeline."""
    rows = con.execute(
        "SELECT turn_id, text, supersedes_turn_id FROM conversation_turns "
        "WHERE case_id=? AND speaker='user' ORDER BY created_at ASC, rowid ASC",
        (case_id,),
    ).fetchall()
    if rows:
        superseded_ids = {str(row["supersedes_turn_id"]) for row in rows if row["supersedes_turn_id"]}
        return [str(row["text"] or "") for row in rows if row["turn_id"] not in superseded_ids and str(row["text"] or "").strip()]
    legacy_rows = con.execute(
        "SELECT message FROM timeline WHERE case_id=? AND event_type='live_room_user_turn' ORDER BY created_at ASC, rowid ASC",
        (case_id,),
    ).fetchall()
    return [re.sub(r"^User said:\s*", "", str(item["message"] or "")) for item in legacy_rows]


def case_bundle(con: sqlite3.Connection, case_id: str) -> dict:
    row = require_case_access(con, case_id)
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    case = dict(row)
    case.pop("owner_id", None)
    case.pop("source_contact_hash", None)
    raw_resolution = case.pop("resolution_json", "") or "{}"
    try:
        case["resolution"] = json.loads(raw_resolution)
    except (TypeError, json.JSONDecodeError):
        case["resolution"] = {}
    if not case["resolution"].get("recommended_steps"):
        # Upgrade legacy recommendation data. An empty action list can be a
        # deliberate adaptive question/collection state, not missing data.
        adaptive_workflow = case["resolution"].get("adaptive_workflow")
        rebuilt_resolution = build_resolution(
            issue_type=case.get("issue_type", "Other payment issue"),
            description=case.get("description", ""), merchant=case.get("merchant", ""),
            amount=case.get("amount"), payment_date=case.get("payment_date", ""),
            payment_status=case.get("payment_status", "unknown"),
            contacted_support=None if case.get("contacted_support") is None else bool(case["contacted_support"]),
        )
        if isinstance(adaptive_workflow, dict):
            # The adaptive workflow is authoritative even when it currently has
            # no action step. Do not resurrect a question from the legacy engine.
            current_question = adaptive_workflow.get("next_question")
            rebuilt_resolution["adaptive_workflow"] = adaptive_workflow
            rebuilt_resolution["fastest_path"] = {
                "title": adaptive_workflow.get("title", "Tell us what happened"),
                "reason": adaptive_workflow.get("reason", ""),
            }
            rebuilt_resolution["recommended_steps"] = ([adaptive_workflow["current_step"]]
                                                        if adaptive_workflow.get("current_step") else [])
            rebuilt_resolution["next_question"] = current_question
            rebuilt_resolution["clarifying_question"] = (current_question or {}).get("prompt", "")
            rebuilt_resolution["support_destinations"] = adaptive_workflow.get("support_destinations", [])
            rebuilt_resolution["suggested_support_draft"] = adaptive_workflow.get("support_draft") or {}
        case["resolution"] = rebuilt_resolution
    case["resolution"] = add_support_context(
        case["resolution"], str(case.get("merchant") or ""), str(case.get("description") or ""),
        case.get("amount"),
    )
    try:
        case["redaction_types"] = json.loads(case.pop("redaction_json", "[]") or "[]")
    except (TypeError, json.JSONDecodeError):
        case["redaction_types"] = []
    case["contacted_support"] = None if case.get("contacted_support") is None else bool(case["contacted_support"])
    # Data provenance is explicit: these values were entered or reported by the user.
    # The app does not claim independent verification unless a future authorised integration adds it.
    fact_specs = [
        ("issue_type", "Issue category", case.get("issue_type"), "Selected by you"),
        ("description", "Problem story", "Story saved", "Your words"),
        ("merchant", "Merchant / app", case.get("merchant") or "", "Entered by you"),
        ("amount", "Amount", case.get("amount"), "Entered by you"),
        ("payment_date", "Payment date", case.get("payment_date") or "", "Entered by you"),
        ("payment_status", "Status shown in the app", case.get("payment_status") if case.get("payment_status") not in (None, "", "unknown") else "", "Selected or reported by you"),
        ("contacted_support", "Previously contacted support", case.get("contacted_support"), "Reported by you"),
    ]
    case["fact_provenance"] = [
        {
            "field": key, "label": label,
            "value": ("Yes" if value is True else "No" if value is False else "Not provided" if value in (None, "") else str(value)),
            "origin": origin if value not in (None, "", "unknown") else "Not provided yet",
            "status": "User-reported · not independently verified" if value not in (None, "", "unknown") else "Missing / unknown",
        }
        for key, label, value, origin in fact_specs
    ]
    case["evidence"] = [
        dict(r)
        for r in con.execute(
            "SELECT evidence_id, original_name, mime_type, size_bytes, created_at, capture_source, captured_at, session_id, sha256, scan_status FROM evidence WHERE case_id = ? ORDER BY created_at",
            (case_id,),
        ).fetchall()
    ]
    for evidence_item in case["evidence"]:
        evidence_item["origin"] = "Uploaded by you"
        evidence_item["verification_status"] = "File contents and authenticity not independently verified"
        evidence_item["scan_status"] = evidence_item.get("scan_status") or "not_scanned"
        evidence_item["claim_links"] = []
        for link_row in con.execute(
            "SELECT link_id, claim_key, claim_label, relation, note, created_at FROM evidence_claim_links WHERE evidence_id=? ORDER BY created_at DESC",
            (evidence_item["evidence_id"],),
        ).fetchall():
            evidence_item["claim_links"].append(dict(link_row))
        evidence_item["derivatives"] = []
        for derivative_row in con.execute(
            "SELECT derivative_id, derivative_type, mime_type, content_text, content_json, content_sha256, processor, processor_version, source_range_json, processing_status, review_status, supersedes_derivative_id, created_at, confirmed_at FROM evidence_derivatives WHERE evidence_id=? AND case_id=? ORDER BY created_at DESC",
            (evidence_item["evidence_id"], case_id),
        ).fetchall():
            derivative = dict(derivative_row)
            try:
                derivative["content"] = json.loads(derivative.pop("content_json", "{}") or "{}")
            except (TypeError, json.JSONDecodeError):
                derivative["content"] = {}
                derivative.pop("content_json", None)
            try:
                derivative["source_range"] = json.loads(derivative.pop("source_range_json", "{}") or "{}")
            except (TypeError, json.JSONDecodeError):
                derivative["source_range"] = {}
                derivative.pop("source_range_json", None)
            evidence_item["derivatives"].append(derivative)
    case["conversation_turns"] = []
    for turn_row in con.execute(
        "SELECT turn_id, speaker, text, language_code, input_source, transcript_confidence, source_evidence_id, session_id, user_confirmed, supersedes_turn_id, created_at FROM conversation_turns WHERE case_id=? ORDER BY created_at ASC, rowid ASC",
        (case_id,),
    ).fetchall():
        turn = dict(turn_row)
        turn["user_confirmed"] = bool(turn.get("user_confirmed"))
        case["conversation_turns"].append(turn)
    case["fact_ledger"] = []
    for fact_row in con.execute(
        "SELECT fact_id, fact_key, fact_value_json, source_type, source_event_id, source_excerpt_redacted, confidence, is_current, created_at FROM case_fact_ledger WHERE case_id=? ORDER BY created_at DESC LIMIT 100",
        (case_id,),
    ).fetchall():
        fact_item = dict(fact_row)
        try:
            fact_item["value"] = json.loads(fact_item.pop("fact_value_json", "null"))
        except (TypeError, json.JSONDecodeError):
            fact_item["value"] = None
            fact_item.pop("fact_value_json", None)
        fact_item["is_current"] = bool(fact_item["is_current"])
        case["fact_ledger"].append(fact_item)
    case["reconciliation_imports"] = []
    for import_row in con.execute(
        "SELECT import_id, evidence_id, provider, status, preview_json, created_at, confirmed_at FROM reconciliation_imports WHERE case_id=? ORDER BY created_at DESC LIMIT 10",
        (case_id,),
    ).fetchall():
        import_item = dict(import_row)
        try:
            import_item["preview"] = json.loads(import_item.pop("preview_json", "{}") or "{}")
        except (TypeError, json.JSONDecodeError):
            import_item["preview"] = {}
            import_item.pop("preview_json", None)
        case["reconciliation_imports"].append(import_item)
    case["exports"] = [
        dict(export_row) for export_row in con.execute(
            "SELECT export_id, export_mode, included_evidence_json, redaction_requested, manifest_sha256, package_sha256, package_filename, created_at FROM case_exports WHERE case_id=? ORDER BY created_at DESC LIMIT 20",
            (case_id,),
        ).fetchall()
    ]
    for export_item in case["exports"]:
        try:
            export_item["included_evidence"] = json.loads(export_item.pop("included_evidence_json", "[]") or "[]")
        except (TypeError, json.JSONDecodeError):
            export_item["included_evidence"] = []
            export_item.pop("included_evidence_json", None)
        export_item["redaction_requested"] = bool(export_item.get("redaction_requested"))
    case["timeline"] = [
        dict(r)
        for r in con.execute(
            "SELECT event_id, event_type, message, created_at, actor, channel, source, metadata_json FROM timeline WHERE case_id = ? ORDER BY created_at DESC, rowid DESC",
            (case_id,),
        ).fetchall()
    ]
    for event in case["timeline"]:
        try:
            event["metadata"] = json.loads(event.pop("metadata_json", "{}") or "{}")
        except (TypeError, json.JSONDecodeError):
            event["metadata"] = {}
            event.pop("metadata_json", None)
    checklist_rows = con.execute(
        "SELECT task_key, checked FROM case_checklist_state WHERE case_id = ?",
        (case_id,),
    ).fetchall()
    case["checklist_state"] = {r["task_key"]: bool(r["checked"]) for r in checklist_rows}
    followup_row = con.execute(
        "SELECT due_date, note, completed, created_at, updated_at FROM case_followups WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    case["follow_up"] = dict(followup_row) if followup_row else {"due_date": "", "note": "", "completed": False}
    if followup_row:
        case["follow_up"]["completed"] = bool(case["follow_up"]["completed"])
    outcome_row = con.execute(
        "SELECT outcome_code, details, reference, provenance, created_at, updated_at FROM case_outcomes WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    case["outcome"] = dict(outcome_row) if outcome_row else None
    case["evidence_fact_sources"] = []
    for source_row in con.execute(
        "SELECT s.fact_source_id, s.evidence_id, e.original_name, s.field_key, s.field_value_json, s.source_label, s.applied_to_case, s.confirmed_at "
        "FROM case_fact_sources s JOIN evidence e ON e.evidence_id=s.evidence_id WHERE s.case_id=? ORDER BY s.confirmed_at DESC",
        (case_id,),
    ).fetchall():
        source_item = dict(source_row)
        try:
            source_item["value"] = json.loads(source_item.pop("field_value_json", "null"))
        except (TypeError, json.JSONDecodeError):
            source_item["value"] = None
            source_item.pop("field_value_json", None)
        source_item["applied_to_case"] = bool(source_item["applied_to_case"])
        case["evidence_fact_sources"].append(source_item)
    case["evidence_fact_reviews"] = [
        dict(review_row) for review_row in con.execute(
            "SELECT review_id, evidence_id, extraction_method, status, created_at, confirmed_at FROM evidence_fact_reviews WHERE case_id=? ORDER BY created_at DESC LIMIT 10",
            (case_id,),
        ).fetchall()
    ]
    case["commitments"] = []
    commitment_rows = con.execute(
        "SELECT * FROM case_commitments WHERE case_id=? ORDER BY created_at DESC",
        (case_id,),
    ).fetchall()
    for commitment_row in commitment_rows:
        commitment = dict(commitment_row)
        commitment["source_authenticity_verified"] = bool(commitment.get("source_authenticity_verified"))
        event_rows = con.execute(
            "SELECT event_id, commitment_id, case_id, event_type, source_type, evidence_id, source_excerpt_redacted, relation, evidence_status, event_date_claimed, event_date_confirmed, details_json, created_at, reviewed_by_user_at FROM commitment_events WHERE case_id=? AND commitment_id=? ORDER BY created_at ASC, rowid ASC",
            (case_id, commitment["commitment_id"]),
        ).fetchall()
        commitment["events"] = []
        for event_row in event_rows:
            event_item = dict(event_row)
            try:
                event_item["details"] = json.loads(event_item.pop("details_json", "{}") or "{}")
            except (TypeError, json.JSONDecodeError):
                event_item["details"] = {}
                event_item.pop("details_json", None)
            commitment["events"].append(event_item)
        commitment["evaluation"] = evaluate_commitment(commitment, commitment["events"])
        case["commitments"].append(commitment)
    case["commitments_version"] = COMMITMENTS_VERSION
    case["action_pack"] = build_action_pack(case, case["checklist_state"], case["follow_up"])
    case["completion_loop"] = build_completion_loop(case, case["action_pack"])
    return case


def auth_email_delivery_capability() -> dict[str, object]:
    """Return non-secret readiness for one-time verification/recovery email delivery."""
    sender = (os.getenv("BOLKE_EMAIL_FROM", "").strip()
              or os.getenv("BOLKE_SMTP_FROM", "").strip())
    origin = os.getenv("BOLKE_PUBLIC_ORIGIN", "").strip().rstrip("/")
    resend_ready = bool(os.getenv("RESEND_API_KEY", "").strip())
    gmail_script_url = os.getenv("BOLKE_GMAIL_SCRIPT_URL", "").strip()
    gmail_script_token = os.getenv("BOLKE_GMAIL_SCRIPT_TOKEN", "").strip()
    gmail_script_ready = bool(
        gmail_script_url.startswith("https://script.google.com/macros/s/")
        and gmail_script_url.endswith("/exec")
        and len(gmail_script_token) >= 32
    )
    host = os.getenv("BOLKE_SMTP_HOST", "").strip()
    try:
        port = int(os.getenv("BOLKE_SMTP_PORT", "587"))
    except ValueError:
        port = 0
    ssl_enabled = os.getenv("BOLKE_SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes", "on"}
    starttls_enabled = os.getenv("BOLKE_SMTP_USE_STARTTLS", "true").strip().lower() in {"1", "true", "yes", "on"}
    secure_transport = ssl_enabled or starttls_enabled
    smtp_ready = bool(host and 1 <= port <= 65535 and secure_transport)
    origin_ok = bool(re.match(r"^https://[^/]+$", origin)) if DEPLOYMENT_ENV == "production" else bool(re.match(r"^https?://[^/]+$", origin))
    sender_ok = bool(AUTH_EMAIL_RE.fullmatch(sender))
    provider = (
        "resend" if resend_ready else
        "gmail_apps_script" if gmail_script_ready else
        "smtp" if smtp_ready else
        "none"
    )
    return {
        "configured": bool(provider != "none" and sender_ok and origin_ok),
        "provider": provider,
        "resend_api_configured": resend_ready,
        "gmail_apps_script_configured": gmail_script_ready,
        "smtp_configured": smtp_ready,
        "sender_configured": sender_ok,
        "public_origin_configured": origin_ok,
        "secure_transport_configured": secure_transport,
    }


def _auth_email_link(token: str, purpose: str) -> str:
    origin = os.getenv("BOLKE_PUBLIC_ORIGIN", "").strip().rstrip("/")
    parameter = "verify_email" if purpose == "email_verification" else "reset_password"
    return f"{origin}/?{parameter}={quote(token, safe='')}"


def _email_delivery_error_label(exc: Exception) -> str:
    """Produce a log-safe provider failure label without addresses or response bodies."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"email_api_http_{exc.response.status_code}"
    return type(exc).__name__


def send_auth_action_email(email: str, token: str, purpose: str) -> None:
    """Send a short-lived one-time link through Resend, Gmail bridge, or SMTP."""
    capability = auth_email_delivery_capability()
    if not capability["configured"]:
        raise RuntimeError("Account email delivery is not configured.")

    link = _auth_email_link(token, purpose)
    if purpose == "email_verification":
        subject = "Verify your BolKeResolve email"
        intro = "Confirm your email address to activate your BolKeResolve account."
        expiry = "This link expires in 30 minutes and can be used once."
    else:
        subject = "Reset your BolKeResolve password"
        intro = "A password reset was requested for your BolKeResolve account."
        expiry = "This link expires in 30 minutes and can be used once. If you did not request it, you can ignore this email."
    body = f"{intro}\n\nOpen this link: {link}\n\n{expiry}\n\nBolKeResolve will never ask for your banking PIN or OTP."
    sender = (os.getenv("BOLKE_EMAIL_FROM", "").strip()
              or os.getenv("BOLKE_SMTP_FROM", "").strip())

    resend_api_key = os.getenv("RESEND_API_KEY", "").strip()
    if resend_api_key:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "BolKeResolve/1.0",
                "Idempotency-Key": hashlib.sha256(f"{purpose}:{token}".encode("utf-8")).hexdigest(),
            },
            json={"from": sender, "to": [email], "subject": subject, "text": body},
            timeout=15.0,
        )
        response.raise_for_status()
        try:
            provider_result = response.json()
        except ValueError as exc:
            raise RuntimeError("Resend returned an invalid response.") from exc
        if not isinstance(provider_result, dict) or not provider_result.get("id"):
            raise RuntimeError("Resend did not confirm an email id.")
        return

    gmail_script_url = os.getenv("BOLKE_GMAIL_SCRIPT_URL", "").strip()
    gmail_script_token = os.getenv("BOLKE_GMAIL_SCRIPT_TOKEN", "").strip()
    if gmail_script_url and gmail_script_token:
        response = httpx.post(
            gmail_script_url,
            json={"token": gmail_script_token, "to": email, "subject": subject, "text": body},
            headers={"User-Agent": "BolKeResolve/1.0"},
            timeout=20.0,
            follow_redirects=True,
        )
        response.raise_for_status()
        try:
            provider_result = response.json()
        except ValueError as exc:
            raise RuntimeError("Gmail email bridge returned an invalid response.") from exc
        if not isinstance(provider_result, dict) or provider_result.get("ok") is not True:
            raise RuntimeError("Gmail email bridge did not confirm delivery.")
        return

    # SMTP fallback for deployments that allow outbound SMTP.
    host = os.getenv("BOLKE_SMTP_HOST", "").strip()
    port = int(os.getenv("BOLKE_SMTP_PORT", "587"))
    username = os.getenv("BOLKE_SMTP_USERNAME", "")
    password = os.getenv("BOLKE_SMTP_PASSWORD", "")
    use_ssl = os.getenv("BOLKE_SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes", "on"}
    use_starttls = os.getenv("BOLKE_SMTP_USE_STARTTLS", "true").strip().lower() in {"1", "true", "yes", "on"}
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = email
    message.set_content(body)
    context = ssl.create_default_context()
    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=12, context=context) as smtp:
            if username:
                smtp.login(username, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=12) as smtp:
            smtp.ehlo()
            if use_starttls:
                smtp.starttls(context=context)
                smtp.ehlo()
            if username:
                smtp.login(username, password)
            smtp.send_message(message)


def create_auth_action_token(con: sqlite3.Connection, user_id: str, purpose: str) -> str:
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    created = now_iso()
    expires = int(time.time()) + 1800
    con.execute("UPDATE auth_action_tokens SET consumed_at=? WHERE user_id=? AND token_type=? AND consumed_at=''", (created, user_id, purpose))
    con.execute(
        "INSERT INTO auth_action_tokens (token_hash,user_id,token_type,created_at,expires_at,consumed_at) VALUES (?,?,?,?,?,'')",
        (digest, user_id, purpose, created, expires),
    )
    return token


def _consume_auth_action_token(con: sqlite3.Connection, token: str, purpose: str):
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    row = con.execute(
        "SELECT token_hash,user_id FROM auth_action_tokens WHERE token_hash=? AND token_type=? AND consumed_at='' AND expires_at>?",
        (digest, purpose, int(time.time())),
    ).fetchone()
    if not row:
        return None
    con.execute("UPDATE auth_action_tokens SET consumed_at=? WHERE token_hash=?", (now_iso(), digest))
    return str(row["user_id"])


@app.get("/api/auth/me")
def auth_me(request: Request) -> dict:
    if not AUTH_ENABLED:
        return {"auth_required": AUTH_REQUIRED, "accounts_enabled": False, "user": None}
    user_id = lookup_session_user(request.cookies.get(SESSION_COOKIE_NAME, ""))
    if not user_id:
        return {"auth_required": AUTH_REQUIRED, "accounts_enabled": True, "user": None}
    with get_db() as con:
        user = con.execute("SELECT user_id, email, created_at, email_verified FROM users WHERE user_id = ?", (user_id,)).fetchone()
    user_payload = dict(user) if user else None
    if user_payload is not None:
        user_payload["email_verified"] = bool(user_payload.get("email_verified"))
    return {"auth_required": AUTH_REQUIRED, "accounts_enabled": True, "user": user_payload}


@app.post("/api/auth/register", status_code=201)
def register_account(request: Request, payload: AuthRegisterRequest, response: Response) -> dict:
    if not AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Account login is enabled only when BOLKE_ACCOUNTS_ENABLED is enabled.")
    enforce_auth_rate_limit(request, "register")
    email = payload.email.strip().lower()
    if not AUTH_EMAIL_RE.fullmatch(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    if not payload.password.strip() or len(payload.password) < 12:
        raise HTTPException(status_code=422, detail="Use a password with at least 12 characters.")
    if EMAIL_VERIFICATION_REQUIRED and not auth_email_delivery_capability()["configured"]:
        raise HTTPException(status_code=503, detail="Account email verification is not configured on this server yet. Please contact the site operator.")
    salt_hex, password_hash = hash_password(payload.password)
    user_id = uuid.uuid4().hex
    created = now_iso()
    token = ""
    try:
        with get_db() as con:
            con.execute(
                "INSERT INTO users (user_id, email, password_salt, password_hash, password_iterations, password_algorithm, created_at, email_verified) VALUES (?, ?, ?, ?, ?, 'pbkdf2_sha256', ?, ?)",
                (user_id, email, salt_hex, password_hash, PASSWORD_HASH_ITERATIONS, created, 0 if EMAIL_VERIFICATION_REQUIRED else 1),
            )
            if EMAIL_VERIFICATION_REQUIRED:
                token = create_auth_action_token(con, user_id, "email_verification")
            else:
                session_token = new_session(con, user_id)
            record_audit_event(con, "account_registered", user_id=user_id, target_type="account", target_id=user_id, metadata={"email_verification_required": EMAIL_VERIFICATION_REQUIRED})
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An account with that email already exists. Sign in instead.")
    if EMAIL_VERIFICATION_REQUIRED:
        try:
            send_auth_action_email(email, token, "email_verification")
        except Exception as exc:
            with get_db() as con:
                con.execute("DELETE FROM users WHERE user_id=? AND email_verified=0", (user_id,))
            logger.warning("Account verification email could not be delivered (%s)", _email_delivery_error_label(exc))
            raise HTTPException(status_code=503, detail="We could not send the verification email. Please check the site configuration or try again later.")
        return {"auth_required": AUTH_REQUIRED, "accounts_enabled": True, "verification_required": True, "message": "Check your inbox for a verification link. It expires in 30 minutes.", "user": {"user_id": user_id, "email": email, "created_at": created, "email_verified": False}}
    set_session_cookie(response, session_token)
    return {"auth_required": AUTH_REQUIRED, "accounts_enabled": True, "verification_required": False, "user": {"user_id": user_id, "email": email, "created_at": created, "email_verified": True}}


@app.post("/api/auth/login")
def login_account(request: Request, payload: AuthLoginRequest, response: Response) -> dict:
    if not AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Account login is enabled only when BOLKE_ACCOUNTS_ENABLED is enabled.")
    enforce_auth_rate_limit(request, "login")
    email = payload.email.strip().lower()
    with get_db() as con:
        user = con.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,)).fetchone()
        stored_iterations = int(user["password_iterations"] or 310000) if user else 310000
        if not user or user["password_algorithm"] != "pbkdf2_sha256" or not verify_password(payload.password, user["password_salt"], user["password_hash"], stored_iterations):
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        if EMAIL_VERIFICATION_REQUIRED and not bool(user["email_verified"]):
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        if stored_iterations < PASSWORD_HASH_ITERATIONS:
            upgraded_salt, upgraded_hash = hash_password(payload.password)
            con.execute(
                "UPDATE users SET password_salt=?, password_hash=?, password_iterations=?, password_algorithm='pbkdf2_sha256' WHERE user_id=?",
                (upgraded_salt, upgraded_hash, PASSWORD_HASH_ITERATIONS, user["user_id"]),
            )
        token = new_session(con, user["user_id"])
        record_audit_event(con, "account_signed_in", user_id=str(user["user_id"]), target_type="session", metadata={"session_created": True})
    set_session_cookie(response, token)
    return {"auth_required": AUTH_REQUIRED, "accounts_enabled": True, "user": {"user_id": user["user_id"], "email": user["email"], "created_at": user["created_at"], "email_verified": bool(user["email_verified"])}}


@app.post("/api/auth/verify-email")
def verify_account_email(payload: AuthTokenRequest, response: Response) -> dict:
    if not AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Account login is not enabled.")
    with get_db() as con:
        user_id = _consume_auth_action_token(con, payload.token, "email_verification")
        if not user_id:
            raise HTTPException(status_code=400, detail="This verification link is invalid or has expired. Request a new one.")
        con.execute("UPDATE users SET email_verified=1 WHERE user_id=?", (user_id,))
        record_audit_event(con, "account_email_verified", user_id=user_id, target_type="account", target_id=user_id)
        token = new_session(con, user_id)
        user = con.execute("SELECT user_id,email,created_at,email_verified FROM users WHERE user_id=?", (user_id,)).fetchone()
    set_session_cookie(response, token)
    return {"ok": True, "auth_required": AUTH_REQUIRED, "accounts_enabled": True, "user": dict(user)}


@app.post("/api/auth/verification/resend")
def resend_account_verification(request: Request, payload: AuthEmailRequest) -> dict:
    if not AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Account login is not enabled.")
    enforce_auth_rate_limit(request, "verification_resend")
    email = payload.email.strip().lower()
    if not AUTH_EMAIL_RE.fullmatch(email):
        return {"ok": True, "message": "If the account needs verification, an email will be sent."}
    token = ""
    with get_db() as con:
        user = con.execute("SELECT user_id,email_verified FROM users WHERE email=? COLLATE NOCASE", (email,)).fetchone()
        if user and not bool(user["email_verified"]):
            token = create_auth_action_token(con, str(user["user_id"]), "email_verification")
    if token:
        try:
            send_auth_action_email(email, token, "email_verification")
        except Exception as exc:
            logger.warning("Account verification resend failed (%s)", _email_delivery_error_label(exc))
    return {"ok": True, "message": "If the account needs verification, an email will be sent."}


@app.post("/api/auth/password-reset/request")
def request_password_reset(request: Request, payload: AuthEmailRequest) -> dict:
    if not AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Account login is not enabled.")
    enforce_auth_rate_limit(request, "password_reset")
    email = payload.email.strip().lower()
    token = ""
    with get_db() as con:
        user = con.execute("SELECT user_id,email_verified FROM users WHERE email=? COLLATE NOCASE", (email,)).fetchone() if AUTH_EMAIL_RE.fullmatch(email) else None
        if user and (bool(user["email_verified"]) or not EMAIL_VERIFICATION_REQUIRED) and auth_email_delivery_capability()["configured"]:
            token = create_auth_action_token(con, str(user["user_id"]), "password_reset")
    if token:
        try:
            send_auth_action_email(email, token, "password_reset")
        except Exception as exc:
            logger.warning("Password reset email could not be delivered (%s)", _email_delivery_error_label(exc))
    # Identical response for unknown and known addresses prevents account enumeration.
    return {"ok": True, "message": "If an account exists for that address, a password reset link will be sent."}


@app.post("/api/auth/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetRequest) -> dict:
    if not AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Account login is not enabled.")
    with get_db() as con:
        user_id = _consume_auth_action_token(con, payload.token, "password_reset")
        if not user_id:
            raise HTTPException(status_code=400, detail="This password reset link is invalid or has expired. Request a new one.")
        salt_hex, digest = hash_password(payload.new_password)
        con.execute("UPDATE users SET password_salt=?,password_hash=?,password_iterations=?,password_algorithm='pbkdf2_sha256' WHERE user_id=?", (salt_hex,digest,PASSWORD_HASH_ITERATIONS,user_id))
        con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        record_audit_event(con, "account_password_reset", user_id=user_id, target_type="account", target_id=user_id, metadata={"sessions_revoked": True})
        con.execute("UPDATE auth_action_tokens SET consumed_at=? WHERE user_id=? AND token_type='password_reset' AND consumed_at=''", (now_iso(),user_id))
    return {"ok": True, "message": "Password reset. Sign in with your new password."}


@app.post("/api/auth/logout")
def logout_account(request: Request, response: Response) -> dict:
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    if token:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with get_db() as con:
            session_row = con.execute("SELECT user_id FROM sessions WHERE token_hash=?", (digest,)).fetchone()
            con.execute("DELETE FROM sessions WHERE token_hash = ?", (digest,))
            if session_row:
                record_audit_event(con, "account_signed_out", user_id=str(session_row["user_id"]), target_type="session")
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/", httponly=True, secure=COOKIE_SECURE, samesite="lax")
    return {"ok": True}


@app.get("/api/auth/sessions")
def list_account_sessions(request: Request) -> dict:
    """Return safe session metadata only; raw session tokens are never exposed."""
    user_id = CURRENT_USER_ID.get()
    if not AUTH_ENABLED or not user_id:
        raise HTTPException(status_code=401, detail="Please sign in to manage sessions.")
    current_token = request.cookies.get(SESSION_COOKIE_NAME, "")
    current_hash = hashlib.sha256(current_token.encode("utf-8")).hexdigest() if current_token else ""
    with get_db() as con:
        rows = con.execute(
            "SELECT token_hash, created_at, expires_at FROM sessions WHERE user_id=? AND expires_at>? ORDER BY created_at DESC",
            (user_id, int(time.time())),
        ).fetchall()
    return {
        "active_sessions": len(rows),
        "sessions": [
            {"created_at": row["created_at"], "expires_at": row["expires_at"], "is_current": hmac.compare_digest(row["token_hash"], current_hash)}
            for row in rows
        ],
    }


@app.post("/api/auth/sessions/revoke-others")
def revoke_other_sessions(request: Request) -> dict:
    """Revoke all other sessions while keeping the current browser signed in."""
    user_id = CURRENT_USER_ID.get()
    if not AUTH_ENABLED or not user_id:
        raise HTTPException(status_code=401, detail="Please sign in to manage sessions.")
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    current_hash = hashlib.sha256(token.encode("utf-8")).hexdigest() if token else ""
    if not current_hash:
        raise HTTPException(status_code=401, detail="Your current session could not be verified.")
    with get_db() as con:
        removed = con.execute("DELETE FROM sessions WHERE user_id=? AND token_hash<>?", (user_id, current_hash)).rowcount
        record_audit_event(con, "account_sessions_revoked", user_id=user_id, target_type="session", metadata={"revoked_count": int(removed)})
    return {"ok": True, "revoked_sessions": int(removed)}


@app.post("/api/auth/password")
def change_account_password(request: Request, payload: PasswordChangeRequest) -> dict:
    user_id = CURRENT_USER_ID.get()
    if not AUTH_ENABLED or not user_id:
        raise HTTPException(status_code=401, detail="Please sign in to change your password.")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=422, detail="Choose a new password different from your current password.")
    with get_db() as con:
        user = con.execute("SELECT password_salt, password_hash, password_iterations, password_algorithm FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not user or user["password_algorithm"] != "pbkdf2_sha256" or not verify_password(payload.current_password, user["password_salt"], user["password_hash"], int(user["password_iterations"] or 310000)):
            raise HTTPException(status_code=403, detail="Your current password did not match.")
        salt_hex, digest = hash_password(payload.new_password)
        con.execute("UPDATE users SET password_salt=?, password_hash=?, password_iterations=?, password_algorithm='pbkdf2_sha256' WHERE user_id=?", (salt_hex, digest, PASSWORD_HASH_ITERATIONS, user_id))
        current_token = request.cookies.get(SESSION_COOKIE_NAME, "")
        current_hash = hashlib.sha256(current_token.encode("utf-8")).hexdigest() if current_token else ""
        removed = con.execute("DELETE FROM sessions WHERE user_id=? AND token_hash<>?", (user_id, current_hash)).rowcount
        record_audit_event(con, "account_password_changed", user_id=user_id, target_type="account", target_id=user_id, metadata={"other_sessions_revoked": int(removed)})
    return {"ok": True, "message": "Password updated. Other active sessions were signed out."}


@app.delete("/api/auth/account")
def delete_account(payload: AccountDeleteRequest, response: Response) -> dict:
    """Delete the signed-in account and its active application records after re-authentication.

    This does not erase downloaded/exported copies, messages already sent to external
    providers, or copies held in host backups under the operator's disclosed retention policy.
    """
    if not AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Account deletion is available only when account sign-in is enabled.")
    user_id = CURRENT_USER_ID.get()
    if not user_id:
        raise HTTPException(status_code=401, detail="Please sign in again before deleting your account.")

    stored_files: list[str] = []
    with get_db() as con:
        user = con.execute("SELECT user_id, password_salt, password_hash, password_iterations, password_algorithm FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Please sign in again before deleting your account.")
        if not verify_password(payload.password, user["password_salt"], user["password_hash"], int(user["password_iterations"] or 310000)):
            raise HTTPException(status_code=403, detail="The password did not match. Nothing was deleted.")

        stored_files = [str(row["stored_name"]) for row in con.execute(
            "SELECT e.stored_name FROM evidence e JOIN cases c ON c.case_id = e.case_id WHERE c.owner_id = ?",
            (user_id,),
        ).fetchall()]
        # WhatsApp webhook rows intentionally have no foreign key to a contact/case so
        # retries can be processed. Explicitly clear rows related to this account too.
        con.execute(
            "DELETE FROM whatsapp_webhook_messages WHERE phone_hash IN "
            "(SELECT phone_hash FROM whatsapp_contacts WHERE owner_id = ?) "
            "OR case_id IN (SELECT case_id FROM cases WHERE owner_id = ?)",
            (user_id, user_id),
        )
        con.execute(
            "DELETE FROM whatsapp_link_tokens WHERE owner_id = ? "
            "OR case_id IN (SELECT case_id FROM cases WHERE owner_id = ?)",
            (user_id, user_id),
        )
        # Deleting owned contacts cascades their active WhatsApp session, pending story,
        # and case-link records. Their encrypted phone identifiers are not kept orphaned.
        con.execute("DELETE FROM whatsapp_contacts WHERE owner_id = ?", (user_id,))
        # ON DELETE CASCADE removes sessions, owned cases, evidence metadata, timelines,
        # follow-ups, outcomes and checklist rows from the active SQLite database.
        con.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    # Remove associated evidence files after the database transaction commits. File names
    # are server-generated; basename checking prevents a malformed row becoming a path.
    cleanup_pending = 0
    for name in stored_files:
        safe_name = Path(name).name
        if safe_name == name and safe_name not in {"", ".", ".."}:
            try:
                (UPLOAD_DIR / safe_name).unlink(missing_ok=True)
            except OSError:
                cleanup_pending += 1
                logger.warning("Account deletion left an evidence file for operator cleanup")

    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/", httponly=True, secure=COOKIE_SECURE, samesite="lax")
    message = (
        "The account and its active case/evidence records were deleted from BolKeResolve. "
        "Downloaded/exported copies, information already sent to external services, and host backups "
        "are not recalled by this action."
    )
    if cleanup_pending:
        message += f" Operator cleanup is required for {cleanup_pending} evidence file(s) that the server could not remove."
    return {
        "ok": True,
        "deleted": True,
        "evidence_cleanup_pending": cleanup_pending,
        "message": message,
    }


def _whatsapp_upsert_contact(con: sqlite3.Connection, phone: str, phone_hash: str, *, owner_id: str | None = None, consent: bool = False) -> None:
    stamp = now_iso()
    ciphertext = whatsapp_service.encrypt_phone(phone)
    existing = con.execute("SELECT owner_id, consent_at FROM whatsapp_contacts WHERE phone_hash = ?", (phone_hash,)).fetchone()
    if existing and existing["owner_id"] and owner_id and existing["owner_id"] != owner_id:
        raise ValueError("This WhatsApp number is already linked to another account.")
    effective_owner = owner_id or (existing["owner_id"] if existing else None)
    consent_at = stamp if consent or not existing else existing["consent_at"]
    con.execute(
        "INSERT INTO whatsapp_contacts (phone_hash, phone_ciphertext, owner_id, consent_at, enabled, created_at, updated_at) VALUES (?, ?, ?, ?, 1, ?, ?) "
        "ON CONFLICT(phone_hash) DO UPDATE SET phone_ciphertext=excluded.phone_ciphertext, owner_id=COALESCE(excluded.owner_id, whatsapp_contacts.owner_id), consent_at=excluded.consent_at, enabled=1, updated_at=excluded.updated_at",
        (phone_hash, ciphertext, effective_owner, consent_at, stamp, stamp),
    )
    con.execute(
        "INSERT INTO whatsapp_sessions (phone_hash, state, pending_story, active_case_id, updated_at) VALUES (?, 'idle', '', NULL, ?) "
        "ON CONFLICT(phone_hash) DO UPDATE SET updated_at=excluded.updated_at",
        (phone_hash, stamp),
    )


def _whatsapp_link_case(con: sqlite3.Connection, phone: str, phone_hash: str, token: str) -> tuple[str | None, str]:
    token_hash = hashlib.sha256(token.upper().encode("ascii")).hexdigest()
    row = con.execute(
        "SELECT token_hash, case_id, owner_id, expires_at, consumed_at FROM whatsapp_link_tokens WHERE token_hash = ?",
        (token_hash,),
    ).fetchone()
    if not row or row["consumed_at"] or int(row["expires_at"]) < int(time.time()):
        return None, "That link code has expired or is not valid. Generate a fresh code from your BolKeResolve case and try again."
    owner_id = row["owner_id"]
    existing = con.execute("SELECT owner_id FROM whatsapp_contacts WHERE phone_hash = ?", (phone_hash,)).fetchone()
    if existing and existing["owner_id"] and owner_id and existing["owner_id"] != owner_id:
        return None, "For your privacy, this WhatsApp number cannot be linked to a different BolKeResolve account."
    _whatsapp_upsert_contact(con, phone, phone_hash, owner_id=owner_id, consent=True)
    created = now_iso()
    # Only this number's own WhatsApp-originated cases are claimed when a logged-in
    # account links the number. No unrelated local cases are swept into that account.
    if owner_id:
        con.execute("UPDATE cases SET owner_id = ? WHERE source_contact_hash = ? AND (owner_id IS NULL OR owner_id = ?)", (owner_id, phone_hash, owner_id))
        con.execute("UPDATE cases SET owner_id = ? WHERE case_id = ? AND (owner_id IS NULL OR owner_id = ?)", (owner_id, row["case_id"], owner_id))
    con.execute("INSERT OR IGNORE INTO whatsapp_case_links (phone_hash, case_id, created_at) VALUES (?, ?, ?)", (phone_hash, row["case_id"], created))
    con.execute("UPDATE whatsapp_link_tokens SET consumed_at = ? WHERE token_hash = ?", (created, token_hash))
    con.execute(
        "INSERT INTO whatsapp_sessions (phone_hash, state, pending_story, active_case_id, updated_at) VALUES (?, 'active_case', '', ?, ?) "
        "ON CONFLICT(phone_hash) DO UPDATE SET state='active_case', pending_story='', active_case_id=excluded.active_case_id, updated_at=excluded.updated_at",
        (phone_hash, row["case_id"], created),
    )
    record_case_event(
        con, row["case_id"], "whatsapp_linked", "The user linked this case to a WhatsApp number using a one-time code.", created,
        actor="user", channel="whatsapp", source="case_link_code", metadata={"phone_fingerprint": phone_hash[:12]},
    )
    con.execute("UPDATE cases SET updated_at = ? WHERE case_id = ?", (created, row["case_id"]))
    return row["case_id"], "Your WhatsApp is connected to this case. Send STATUS to check progress, UPDATE followed by a note to add what happened, or HELP to see the options."


def _wa_case_row(con: sqlite3.Connection, phone_hash: str, session_row: sqlite3.Row | None) -> sqlite3.Row | None:
    case_id = str(session_row["active_case_id"] or "") if session_row else ""
    if not case_id:
        link = con.execute("SELECT case_id FROM whatsapp_case_links WHERE phone_hash = ? ORDER BY created_at DESC LIMIT 1", (phone_hash,)).fetchone()
        case_id = str(link["case_id"]) if link else ""
    if not case_id:
        return None
    return con.execute(
        "SELECT c.* FROM cases c WHERE c.case_id = ? AND (c.source_contact_hash = ? OR EXISTS (SELECT 1 FROM whatsapp_case_links l WHERE l.case_id = c.case_id AND l.phone_hash = ?))",
        (case_id, phone_hash, phone_hash),
    ).fetchone()


def _wa_event(con: sqlite3.Connection, row: sqlite3.Row, phone_hash: str, event_type: str, message: str, stage: str | None = None, *, details: str = "", reference: str = "") -> None:
    stamp = now_iso()
    safe_details = scrub_sensitive_text(details.strip()) if details else None
    safe_reference = scrub_sensitive_text(reference.strip()) if reference else None
    safe_msg = message
    if safe_details and safe_details.text:
        safe_msg += " Details: " + safe_details.text
    metadata = {"phone_fingerprint": phone_hash[:12], "user_reported": True}
    if safe_reference and safe_reference.text:
        metadata["reference_provided"] = safe_reference.text[:120]
    if safe_details and safe_details.redacted_types:
        metadata["redacted_categories"] = safe_details.redacted_types
    if safe_reference and safe_reference.redacted_types:
        metadata["reference_redacted_categories"] = safe_reference.redacted_types
    record_case_event(con, row["case_id"], event_type, safe_msg, stamp, actor="user", channel="whatsapp", source="inbound_webhook", metadata=metadata)
    if stage:
        con.execute("UPDATE cases SET case_stage = ?, updated_at = ? WHERE case_id = ?", (stage, stamp, row["case_id"]))
    else:
        con.execute("UPDATE cases SET updated_at = ? WHERE case_id = ?", (stamp, row["case_id"]))


def _whatsapp_case_summary(story: str, extracted: dict) -> str:
    fields = extracted.get("fields", {})
    issue = fields.get("issue_type", {}).get("value") or "payment issue"
    merchant = fields.get("merchant", {}).get("value") or ""
    amount = fields.get("amount", {}).get("value")
    bits = [f"Issue: {issue}"]
    if merchant:
        bits.append(f"App: {merchant}")
    if amount is not None and not any(c.get("field") == "amount" for c in extracted.get("conflicts", [])):
        bits.append(f"Amount: ₹{amount:g}")
    return "I understood this:\n" + "\n".join("• " + bit for bit in bits) + "\n\nReply SAVE to create the case, EDIT to rewrite your story, or CANCEL to discard it. I have not contacted the company."


def _whatsapp_create_case(con: sqlite3.Connection, phone_hash: str, story: str, session_row: sqlite3.Row) -> tuple[str, str]:
    from backend.extraction import extract_case_facts
    extracted = extract_case_facts(story)
    fields = extracted.get("fields", {})
    amount_field = fields.get("amount", {})
    amount = amount_field.get("value")
    if any(item.get("field") == "amount" for item in extracted.get("conflicts", [])):
        amount = None
    date_field = fields.get("payment_date", {})
    payment_date = date_field.get("value") or ""
    if date_field.get("needs_confirmation"):
        payment_date = ""
    issue = fields.get("issue_type", {}).get("value") or "Other payment issue"
    merchant = fields.get("merchant", {}).get("value") or ""
    payment_status = fields.get("payment_status", {}).get("value") or "unknown"
    contacted = fields.get("contacted_support", {}).get("value")
    contacted_support = None if contacted is None else bool(contacted)
    row = con.execute("SELECT owner_id FROM whatsapp_contacts WHERE phone_hash = ? AND enabled = 1", (phone_hash,)).fetchone()
    if not row:
        raise ValueError("WhatsApp consent is not active.")
    owner_id = row["owner_id"]
    resolution = build_resolution(issue, story, merchant, amount, payment_date, payment_status, contacted_support)
    resolution = add_support_context(resolution, merchant, story, amount)
    classification = resolution.get("classification", {})
    saved_issue = classification.get("issue_type") if classification.get("confidence") in {"high", "medium"} else issue
    case_id = safe_case_id()
    created = now_iso()
    con.execute(
        "INSERT INTO cases (case_id, owner_id, created_at, updated_at, issue_type, merchant, amount, payment_date, language_code, description, status, case_stage, payment_status, contacted_support, resolution_json, redaction_json, source_contact_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (case_id, owner_id, created, created, saved_issue, merchant, amount, payment_date, _language_from_text(story), story, "Received", "Needs next step", payment_status, None if contacted_support is None else int(contacted_support), json.dumps(resolution, ensure_ascii=False), "[]", phone_hash),
    )
    record_case_event(con, case_id, "created", "Case created from details shared with the BolKeResolve WhatsApp assistant. Details are user-reported; no payment system was checked.", created, actor="user", channel="whatsapp", source="inbound_webhook", metadata={"language_code": _language_from_text(story)})
    record_case_event(con, case_id, "notice", "A source-backed first-pass guidance plan was prepared. It has not been submitted to any organisation.", created, actor="system", channel="whatsapp", source="bolkeresolve")
    con.execute("INSERT OR IGNORE INTO whatsapp_case_links (phone_hash, case_id, created_at) VALUES (?, ?, ?)", (phone_hash, case_id, created))
    con.execute(
        "UPDATE whatsapp_sessions SET state='active_case', pending_story='', active_case_id=?, updated_at=? WHERE phone_hash=?",
        (case_id, created, phone_hash),
    )
    amount_text = f"₹{amount:g}" if amount is not None else "amount not provided"
    reply = (
        f"Your case {case_id} is saved.\\nIssue: {saved_issue}.\\nApp: {merchant or 'not provided'} · {amount_text}.\\n\\n"
        "No complaint has been sent. Reply STATUS to check this case; UPDATE followed by a note to record what happened; "
        "CONTACTED if you reached support; WAITING if you're awaiting a reply; REPLY followed by the response; "
        "FOLLOWUP YYYY-MM-DD to set a follow-up date; RESOLVED if the issue is resolved; NEW for another problem; or STOP to opt out."
    )
    return case_id, reply.replace("\\n", "\n")


def _whatsapp_handle_message(con: sqlite3.Connection, phone: str, phone_hash: str, message_type: str, raw_text: str, *, provider: str = "meta") -> tuple[str, str]:
    """Handle one inbound message inside the same transaction as its state change."""
    text = str(raw_text or "").strip()[:4096]
    command = text.upper().strip()
    command = {
        "START_CASE": "START", "CHECK_STATUS": "STATUS", "GET_HELP": "HELP",
        "SAVE_CASE": "SAVE", "EDIT_STORY": "EDIT", "CANCEL_CASE": "CANCEL",
        "CONTACTED_SUPPORT": "CONTACTED", "STILL_WAITING": "WAITING",
    }.get(command, command)
    if message_type not in {"text", "button", "interactive", "audio"}:
        return "", "For now, send a text message or a WhatsApp voice note. You can attach evidence after your case is created."

    # Respect common explicit opt-out phrases, even if the contact is already disabled.
    # Keep this matching deliberately specific so a story that merely mentions “stop”
    # does not unexpectedly opt the person out.
    opt_out_commands = {
        "STOP", "STOP ALL", "STOP MESSAGES", "STOP MESSAGING",
        "UNSUBSCRIBE", "OPT OUT", "OPT-OUT", "QUIT", "END",
        "REMOVE ME", "DO NOT MESSAGE ME", "DONT MESSAGE ME",
        "DON'T MESSAGE ME", "PLEASE STOP MESSAGING ME",
        "NO MORE MESSAGES", "NO MORE WHATSAPP MESSAGES",
    }
    if command in opt_out_commands:
        stamp = now_iso()
        con.execute("UPDATE whatsapp_contacts SET enabled=0, updated_at=? WHERE phone_hash=?", (stamp, phone_hash))
        con.execute("UPDATE whatsapp_sessions SET state='stopped', pending_story='', active_case_id=NULL, updated_at=? WHERE phone_hash=?", (stamp, phone_hash))
        return "", "You've opted out of BolKeResolve WhatsApp updates. We won't send future follow-up reminders to this number. Your saved case record remains available through the case's normal access controls. Reply START if you want to use this service again."

    # Consent/opt-out is checked before case linking. A previously issued LINK code
    # must never silently reactivate a sender after STOP; re-opt-in requires START.
    contact = con.execute("SELECT * FROM whatsapp_contacts WHERE phone_hash=?", (phone_hash,)).fetchone()
    if not contact or not contact["enabled"]:
        if command == "START":
            try:
                _whatsapp_upsert_contact(con, phone, phone_hash, consent=True)
            except (RuntimeError, ValueError):
                return "", "This WhatsApp service is not ready yet. Please continue on the BolKeResolve website for now."
            stamp = now_iso()
            con.execute("UPDATE whatsapp_sessions SET state='awaiting_story', pending_story='', active_case_id=NULL, updated_at=? WHERE phone_hash=?", (stamp, phone_hash))
            privacy_url = os.getenv("BOLKE_PRIVACY_POLICY_URL", "").strip()
            if not privacy_url:
                public_origin = os.getenv("BOLKE_PUBLIC_ORIGIN", "").strip().rstrip("/")
                privacy_url = f"{public_origin}/privacy.html" if public_origin.startswith("https://") else ""
            privacy_line = f"\nPrivacy notice: {privacy_url}" if privacy_url else "\nRead the Privacy Notice on our BolKeResolve website before sharing personal details."
            support_target = os.getenv("BOLKE_SUPPORT_EMAIL", "").strip() or os.getenv("BOLKE_SUPPORT_URL", "").strip()
            support_line = f"\nHelp/contact: {support_target}" if support_target else ""
            if provider == "twilio":
                consent_text = "Thanks for opting in. BolKeResolve uses the messages you share to prepare and track a payment-help case. This Twilio Sandbox test channel currently accepts text only; do not send voice notes or attachments here. We do not contact a bank/merchant or submit a complaint on your behalf. Never send an OTP, UPI PIN, password, full card/account number or ID number. Tell me what happened in text. Reply STOP to opt out."
            else:
                consent_text = "Thanks for opting in. BolKeResolve uses the messages you share to prepare and track a payment-help case. If you send a voice note, its audio is sent to our speech-to-text provider (Gnani) for transcription. We do not contact a bank/merchant or submit a complaint on your behalf. Never send an OTP, UPI PIN, password, full card/account number or ID number. Tell me what happened in text or a voice note. Keep voice notes under 30 seconds for best results (provider limit may apply); type long stories. Voice notes default to Hindi/Hinglish; send LANG EN, LANG HI, LANG MR, LANG BN, LANG GU, LANG KN, LANG ML, LANG PA, LANG TA or LANG TE to change it. Reply STOP to opt out."
            return "", consent_text + privacy_line + support_line
        if re.fullmatch(r"LINK\s+[A-HJ-NP-Z2-9]{8}", command):
            return "", "Before linking, reply START to opt in. Then resend the same LINK code within its 10-minute validity window. The code has not been used."
        return "", "Namaste! This number is not opted in. Reply START to opt in before sharing a story or linking a case. If you opted out earlier, send START again only when you want to resume."

    link_match = re.fullmatch(r"LINK\s+([A-HJ-NP-Z2-9]{8})", command)
    if link_match:
        try:
            case_id, reply = _whatsapp_link_case(con, phone, phone_hash, link_match.group(1))
        except ValueError:
            return "", "This number is already linked to another account. For privacy, sign in to the account that owns the case or unlink it first."
        return case_id or "", reply

    session = con.execute("SELECT * FROM whatsapp_sessions WHERE phone_hash=?", (phone_hash,)).fetchone()
    language_match = re.fullmatch(r"LANG(?:UAGE)?\s+(EN|EN-IN|HI|HI-IN|MR|MR-IN|BN|BN-IN|GU|GU-IN|KN|KN-IN|ML|ML-IN|PA|PA-IN|TA|TA-IN|TE|TE-IN)", command)
    if language_match:
        language_aliases = {"EN":"en-IN", "EN-IN":"en-IN", "HI":"hi-IN", "HI-IN":"hi-IN", "MR":"mr-IN", "MR-IN":"mr-IN", "BN":"bn-IN", "BN-IN":"bn-IN", "GU":"gu-IN", "GU-IN":"gu-IN", "KN":"kn-IN", "KN-IN":"kn-IN", "ML":"ml-IN", "ML-IN":"ml-IN", "PA":"pa-IN", "PA-IN":"pa-IN", "TA":"ta-IN", "TA-IN":"ta-IN", "TE":"te-IN", "TE-IN":"te-IN"}
        selected_language = language_aliases[language_match.group(1)]
        con.execute("UPDATE whatsapp_sessions SET language_code=?, updated_at=? WHERE phone_hash=?", (selected_language, now_iso(), phone_hash))
        language_display = {"en-IN":"English", "hi-IN":"Hindi / Hinglish", "mr-IN":"Marathi", "bn-IN":"Bengali", "gu-IN":"Gujarati", "kn-IN":"Kannada", "ml-IN":"Malayalam", "pa-IN":"Punjabi", "ta-IN":"Tamil", "te-IN":"Telugu"}[selected_language]
        return "", f"Voice-note language set to {language_display}. Send a voice note or tell me what happened in your own words."
    if command == "HELP":
        support_target = os.getenv("BOLKE_SUPPORT_EMAIL", "").strip() or os.getenv("BOLKE_SUPPORT_URL", "").strip()
        support_line = f"\nFor BolKeResolve support, contact: {support_target}." if support_target else ""
        if provider == "twilio":
            help_text = "Options: send a text story; SAVE / EDIT / CANCEL when reviewing a new story; STATUS; UPDATE <note>; CONTACTED; WAITING; REPLY <message>; FOLLOWUP YYYY-MM-DD; RESOLVED; NEW; LINK <one-time-code>; STOP to opt out. This Twilio Sandbox adapter is text-only; use the website for voice notes and evidence uploads. Do not send OTPs, PINs, passwords or full account/card numbers."
        else:
            help_text = "Options: send text or a short voice note; LANG EN/HI/MR/BN/GU/KN/ML/PA/TA/TE to choose voice-note language; SAVE / EDIT / CANCEL when reviewing a new story; STATUS; UPDATE <note>; CONTACTED; WAITING; REPLY <message>; FOLLOWUP YYYY-MM-DD; RESOLVED; NEW; LINK <one-time-code>; STOP to opt out.\nVoice notes are transcribed by Gnani when configured. Do not send OTPs, PINs, passwords or full account/card numbers. For evidence uploads, open the website and the case workspace."
        return str(session["active_case_id"] or "") if session else "", help_text + support_line
    if command == "START":
        stamp = now_iso()
        con.execute("UPDATE whatsapp_contacts SET enabled=1, consent_at=?, updated_at=? WHERE phone_hash=?", (stamp, stamp, phone_hash))
        con.execute("UPDATE whatsapp_sessions SET state='awaiting_story', pending_story='', active_case_id=NULL, updated_at=? WHERE phone_hash=?", (stamp, phone_hash))
        return "", "You're ready to begin. Tell me what happened in your own words. Don't include OTPs, UPI PINs, passwords or full card details."
    if session and session["state"] == "awaiting_story":
        if command == "STATUS":
            return "", "You don't have an active case linked here yet. Tell me what happened to start one, or send LINK <one-time-code> to connect a case from the website."
        safe_story = scrub_sensitive_text(text)
        if len(safe_story.text.strip()) < 8:
            return "", "Tell me a little more about the problem so I can prepare a useful case. You can mention the app, amount and what went wrong if you remember them."
        stamp = now_iso()
        con.execute("UPDATE whatsapp_sessions SET state='awaiting_confirmation', pending_story=?, updated_at=? WHERE phone_hash=?", (safe_story.text[:5000], stamp, phone_hash))
        from backend.extraction import extract_case_facts
        return "", _whatsapp_case_summary(safe_story.text, extract_case_facts(safe_story.text))
    if session and session["state"] == "awaiting_confirmation":
        if command in {"CANCEL", "NO", "STOPCASE"}:
            stamp = now_iso()
            con.execute("UPDATE whatsapp_sessions SET state='idle', pending_story='', updated_at=? WHERE phone_hash=?", (stamp, phone_hash))
            return "", "No case was created. Your draft story has been discarded. Send NEW or START whenever you're ready."
        if command == "EDIT":
            stamp = now_iso()
            con.execute("UPDATE whatsapp_sessions SET state='awaiting_story', pending_story='', updated_at=? WHERE phone_hash=?", (stamp, phone_hash))
            return "", "Please send the corrected story as one message. You can then review it before saving."
        if command in {"SAVE", "YES", "CONFIRM"}:
            case_id, reply = _whatsapp_create_case(con, phone_hash, session["pending_story"], session)
            return case_id, reply
        return "", "Please reply SAVE to create the case, EDIT to change the story, or CANCEL to discard it."

    if command == "NEW":
        stamp = now_iso()
        con.execute("UPDATE whatsapp_sessions SET state='awaiting_story', pending_story='', active_case_id=NULL, updated_at=? WHERE phone_hash=?", (stamp, phone_hash))
        return "", "Let's start a new case. Tell me what happened in your own words."

    # Refresh after any pairing/new-case transitions. All case updates must be tied
    # to a case associated with this verified WhatsApp sender.
    session = con.execute("SELECT * FROM whatsapp_sessions WHERE phone_hash=?", (phone_hash,)).fetchone()
    row = _wa_case_row(con, phone_hash, session)
    if command == "STATUS":
        if not row:
            return "", "You don't have an active case linked here yet. Send NEW to describe a problem or LINK <one-time-code> to connect a case from the website."
        followup = con.execute("SELECT due_date, completed FROM case_followups WHERE case_id=?", (row["case_id"],)).fetchone()
        due = f" Follow-up date: {followup['due_date']}." if followup and followup["due_date"] and not followup["completed"] else " No active follow-up date is set."
        return row["case_id"], f"Case {row['case_id']} · {row['issue_type']} · Status: {row['case_stage']}.{due} This status is based on your saved updates, not a live check with the organisation. Reply HELP for options."
    if not row:
        return "", "Your opt-in is saved. Send NEW to describe a payment problem, or LINK <one-time-code> to connect a case you've already created on the website."

    stamp = now_iso()
    if command.startswith("UPDATE ") and len(text[7:].strip()) >= 3:
        details = text[7:].strip()[:1000]
        safe_details = scrub_sensitive_text(details)
        record_case_event(con, row["case_id"], "whatsapp_update", "The user added a WhatsApp case update: " + safe_details.text, stamp, actor="user", channel="whatsapp", source="inbound_webhook", metadata={"phone_fingerprint": phone_hash[:12], "redacted_categories": safe_details.redacted_types})
        con.execute("UPDATE cases SET updated_at=? WHERE case_id=?", (stamp, row["case_id"]))
        return row["case_id"], f"Update saved to case {row['case_id']}. Your timeline now includes this user-reported note. Reply STATUS to check progress."
    if command == "CONTACTED":
        _wa_event(con, row, phone_hash, "contacted_support", "The user reported contacting the organisation's support channel.", "Contacted support")
        return row["case_id"], "I've recorded that you contacted support. This does not mean BolKeResolve sent a message. Reply UPDATE <note> to add a reference number or details."
    if command == "WAITING":
        _wa_event(con, row, phone_hash, "still_waiting", "The user reported that they are waiting for a response.", "Awaiting response")
        return row["case_id"], "I've updated your case to 'Awaiting response' based on your report. Reply FOLLOWUP YYYY-MM-DD to set a reminder date."
    if command.startswith("REPLY"):
        details = text[5:].strip()[:1000]
        _wa_event(con, row, phone_hash, "response_received", "The user reported receiving a reply from the organisation.", "Follow-up needed", details=details)
        return row["case_id"], "I've recorded that you received a reply. Review it and decide the next step. Add a reference with UPDATE <note> if useful."
    if command in {"RESOLVED", "REFUND RECEIVED"}:
        _wa_event(con, row, phone_hash, "resolved", "The user marked this issue resolved. This is user-reported and not independently verified.", "Resolved (user-reported)")
        return row["case_id"], "Marked as resolved (your report). BolKeResolve hasn't independently checked the refund. You can send NEW to start another case."
    if command in {"NOT RESOLVED", "STILL NOT RESOLVED"}:
        _wa_event(con, row, phone_hash, "not_resolved", "The user reported that the problem is not resolved.", "Follow-up needed")
        return row["case_id"], "I've marked the case as not resolved and needing a follow-up. Reply STATUS to review the next step."
    if command.startswith("FOLLOWUP "):
        raw_date = text[9:].strip()
        try:
            parsed_due = date.fromisoformat(raw_date)
        except ValueError:
            return row["case_id"], "Please send the date as FOLLOWUP YYYY-MM-DD, for example FOLLOWUP 2026-10-25."
        safe_note = scrub_sensitive_text("WhatsApp follow-up scheduled by the user")
        existing = con.execute("SELECT created_at FROM case_followups WHERE case_id=?", (row["case_id"],)).fetchone()
        created_at = existing["created_at"] if existing else stamp
        con.execute(
            "INSERT INTO case_followups (case_id, due_date, note, completed, created_at, updated_at, reminder_sent_for) VALUES (?, ?, ?, 0, ?, ?, '') "
            "ON CONFLICT(case_id) DO UPDATE SET due_date=excluded.due_date, note=excluded.note, completed=0, updated_at=excluded.updated_at, reminder_sent_for=''",
            (row["case_id"], parsed_due.isoformat(), safe_note.text, created_at, stamp),
        )
        con.execute("UPDATE cases SET updated_at=? WHERE case_id=?", (stamp, row["case_id"]))
        record_case_event(con, row["case_id"], "followup_scheduled", f"The user scheduled a follow-up for {parsed_due.isoformat()} via WhatsApp. A reminder is sent only if the WhatsApp integration and approved template are configured.", stamp, actor="user", channel="whatsapp", source="inbound_webhook", metadata={"due_date": parsed_due.isoformat()})
        return row["case_id"], f"Follow-up date saved as {parsed_due.isoformat()}. If WhatsApp reminders are configured, consent is active, and the approved reminder template is set up, you'll receive a reminder when due."

    safe_details = scrub_sensitive_text(text)
    record_case_event(con, row["case_id"], "whatsapp_update", "The user sent an update through WhatsApp: " + safe_details.text, stamp, actor="user", channel="whatsapp", source="inbound_webhook", metadata={"phone_fingerprint": phone_hash[:12], "redacted_categories": safe_details.redacted_types})
    con.execute("UPDATE cases SET updated_at=? WHERE case_id=?", (stamp, row["case_id"]))
    return row["case_id"], f"I've added that message to case {row['case_id']} as a user-reported update. If this is a separate problem, reply NEW."


def process_whatsapp_status_updates(status_updates: list[dict]) -> int:
    """Persist provider receipts for tracked messages without treating API acceptance as delivery."""
    processed = 0
    priority = {"accepted": 0, "sent": 1, "delivered": 2, "read": 3, "failed": -1}
    event_for = {
        "sent": ("whatsapp_sent", "Meta reported that the WhatsApp message was sent."),
        "delivered": ("whatsapp_delivered", "Meta reported that the WhatsApp message was delivered."),
        "read": ("whatsapp_read", "Meta reported that the WhatsApp message was read."),
        "failed": ("whatsapp_delivery_failed", "Meta reported that the WhatsApp message could not be delivered."),
    }
    for update in status_updates:
        message_id = str(update.get("message_id", ""))[:180]
        next_status = str(update.get("status", "")).lower()
        if not message_id or next_status not in event_for:
            continue
        stamp = now_iso()
        with get_db() as con:
            row = con.execute("SELECT message_id, case_id, purpose, status FROM whatsapp_outbound_messages WHERE message_id=?", (message_id,)).fetchone()
            if not row:
                continue
            current = row["status"]
            # Receipts can arrive late or be retried; never move a known state backwards.
            if current == next_status or current in {"read", "failed"}:
                continue
            if next_status != "failed" and priority.get(next_status, -2) <= priority.get(current, -2):
                continue
            error_code = str(update.get("error_code", ""))[:40] if next_status == "failed" else ""
            con.execute("UPDATE whatsapp_outbound_messages SET status=?, updated_at=?, error_code=? WHERE message_id=?", (next_status, stamp, error_code, message_id))
            event_type, message = event_for[next_status]
            metadata = {"provider": "meta_whatsapp_cloud_api", "provider_status": next_status, "message_id": message_id, "purpose": row["purpose"]}
            if error_code:
                metadata["provider_error_code"] = error_code
            record_case_event(con, row["case_id"], event_type, message, stamp, actor="system", channel="whatsapp", source="provider_status_webhook", metadata=metadata)
            processed += 1
    return processed


def enforce_whatsapp_audio_quota(phone_hash: str, limit: int = 5, window_seconds: int = 60) -> None:
    """Limit paid STT calls per opted-in sender using persistent timestamps."""
    stamp = int(time.time())
    with get_db() as con:
        con.execute("DELETE FROM whatsapp_audio_usage WHERE created_at < ?", (stamp - window_seconds,))
        count = con.execute("SELECT COUNT(*) FROM whatsapp_audio_usage WHERE phone_hash=? AND created_at>=?", (phone_hash, stamp - window_seconds)).fetchone()[0]
        if count >= limit:
            raise HTTPException(status_code=429, detail="Too many voice notes in a short time. Please wait a minute or send your story as text.")
        con.execute("INSERT INTO whatsapp_audio_usage (phone_hash, created_at) VALUES (?, ?)", (phone_hash, stamp))


async def transcribe_whatsapp_voice_note(request: Request, message: whatsapp_service.WhatsAppMessage, phone_hash: str) -> str:
    """Download and transcribe a voice note through the existing Gnani speech workflow."""
    enforce_whatsapp_audio_quota(phone_hash, int(os.getenv("BOLKE_WHATSAPP_STT_LIMIT_PER_MINUTE", "5")))
    content, mime_type = await whatsapp_service.download_audio_media(message.media_id)
    extension_by_mime = {"audio/ogg": ".ogg", "audio/opus": ".ogg", "audio/mpeg": ".mp3", "audio/mp4": ".m4a", "audio/aac": ".aac", "audio/amr": ".amr", "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/flac": ".flac"}
    extension = extension_by_mime.get(mime_type, ".ogg")
    upload = UploadFile(filename="whatsapp-voice-note" + extension, file=io.BytesIO(content), headers=Headers({"content-type": mime_type}))
    with get_db() as con:
        row = con.execute("SELECT language_code FROM whatsapp_sessions WHERE phone_hash=?", (phone_hash,)).fetchone()
    selected_language = str(row["language_code"] if row else "hi-IN")
    if selected_language not in LANGUAGES:
        selected_language = "hi-IN"
    result = await transcribe_audio(request, upload, language_code=selected_language)
    return str(result.get("transcript", "")).strip()


@app.get("/api/webhooks/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    """Meta's one-time webhook subscription verification endpoint."""
    expected = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()
    mode = request.query_params.get("hub.mode", "")
    supplied = request.query_params.get("hub.verify_token", "")
    challenge = request.query_params.get("hub.challenge", "")
    if not expected:
        raise HTTPException(status_code=503, detail="WhatsApp webhook verification is not configured.")
    if mode == "subscribe" and challenge and hmac.compare_digest(supplied, expected):
        return PlainTextResponse(challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Webhook verification failed.")


async def _process_channel_inbound_messages(
    inbound_messages,
    request: Request,
    *,
    provider: str,
    lease_seconds: int,
) -> tuple[int, int]:
    """Run normalized inbound messages through the single existing case engine.

    Provider adapters authenticate and normalize transport payloads before this
    function is called. Consent, deduplication, case state, privacy redaction and
    replies remain shared across providers.
    """
    failures = 0
    processed = 0
    expected_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip() if provider == "meta" else ""
    for message in inbound_messages:
        if provider == "meta" and message.phone_number_id and message.phone_number_id != expected_phone_id:
            logger.warning("Ignoring Meta webhook for an unconfigured phone number ID")
            continue
        message_db_id = messaging_service.storage_message_id(provider, message.message_id)
        try:
            phone_hash = whatsapp_service.phone_fingerprint(message.sender)
            reply_text = ""
            case_id = ""
            should_process_message = False
            current_time = int(time.time())
            lease_until = current_time + lease_seconds
            with get_db() as con:
                existing = con.execute("SELECT * FROM whatsapp_webhook_messages WHERE message_id=?", (message_db_id,)).fetchone()
                if existing and existing["status"] == "sent":
                    continue
                if existing and existing["status"] in {"processing", "sending"} and int(existing["lease_until"] or 0) > current_time:
                    failures += 1
                    continue
                if not existing:
                    con.execute(
                        "INSERT INTO whatsapp_webhook_messages (message_id, phone_hash, reply_text, case_id, status, created_at, reply_sent_at, lease_until, attempts, last_error_type, provider) VALUES (?, ?, '', '', 'processing', ?, '', ?, 1, '', ?)",
                        (message_db_id, phone_hash, now_iso(), lease_until, provider),
                    )
                    should_process_message = True
                elif existing["status"] == "ready" or (existing["status"] == "sending" and int(existing["lease_until"] or 0) <= current_time):
                    cur = con.execute(
                        "UPDATE whatsapp_webhook_messages SET status='sending', lease_until=?, attempts=attempts+1, last_error_type='' WHERE message_id=? AND (status='ready' OR (status='sending' AND lease_until<=?) )",
                        (lease_until, message_db_id, current_time),
                    )
                    if cur.rowcount != 1:
                        failures += 1
                        continue
                    reply_text = existing["reply_text"]
                    case_id = existing["case_id"]
                elif existing["status"] == "processing" and int(existing["lease_until"] or 0) <= current_time:
                    cur = con.execute(
                        "UPDATE whatsapp_webhook_messages SET status='processing', lease_until=?, attempts=attempts+1, last_error_type='' WHERE message_id=? AND status='processing' AND lease_until<=?",
                        (lease_until, message_db_id, current_time),
                    )
                    if cur.rowcount != 1:
                        failures += 1
                        continue
                    should_process_message = True
                else:
                    failures += 1
                    continue

            if should_process_message:
                effective_type = message.message_type
                effective_text = message.text
                # Voice-note transcription is currently supported by the direct Meta
                # media path. Twilio Sandbox phase 1 intentionally supports text only.
                if message.message_type == "audio" and provider == "meta":
                    with get_db() as con:
                        contact = con.execute("SELECT enabled FROM whatsapp_contacts WHERE phone_hash=?", (phone_hash,)).fetchone()
                    if contact and contact["enabled"] and message.media_id:
                        try:
                            effective_text = await transcribe_whatsapp_voice_note(request, message, phone_hash)
                            effective_type = "text"
                            if not effective_text:
                                raise HTTPException(status_code=502, detail="We couldn't hear enough to transcribe that voice note. Please try again or type your story.")
                        except HTTPException as audio_error:
                            effective_type = "text"
                            effective_text = ""
                            reply_text = audio_error.detail if audio_error.status_code in {429, 502} else "I couldn't process that voice note. Please try again or type your story."
                        except (RuntimeError, ValueError) as audio_error:
                            logger.warning("WhatsApp voice-note processing failed (%s)", type(audio_error).__name__)
                            effective_type = "text"
                            effective_text = ""
                            reply_text = "I couldn't process that voice note right now. Please try again or type your story instead."
                    else:
                        effective_type = "audio"
                        effective_text = ""
                elif message.message_type == "unsupported_media":
                    # Respect STOP/START and the consent gate even for unsupported media.
                    with get_db() as con:
                        contact = con.execute("SELECT enabled FROM whatsapp_contacts WHERE phone_hash=?", (phone_hash,)).fetchone()
                    if contact and contact["enabled"]:
                        reply_text = "This WhatsApp test channel currently accepts text messages only. Please type your story; you can upload evidence on the BolKeResolve website after creating a case."
                    else:
                        effective_type = "text"
                        effective_text = ""
                if not reply_text:
                    with get_db() as con:
                        case_id, reply_text = _whatsapp_handle_message(con, message.sender, phone_hash, effective_type, effective_text, provider=provider)
                        con.execute(
                            "UPDATE whatsapp_webhook_messages SET reply_text=?, case_id=?, status='sending', lease_until=?, last_error_type='' WHERE message_id=? AND status='processing'",
                            (reply_text, case_id, int(time.time()) + lease_seconds, message_db_id),
                        )
                else:
                    with get_db() as con:
                        con.execute(
                            "UPDATE whatsapp_webhook_messages SET reply_text=?, case_id=?, status='sending', lease_until=?, last_error_type='' WHERE message_id=? AND status='processing'",
                            (reply_text, case_id, int(time.time()) + lease_seconds, message_db_id),
                        )

            send_result = None
            if reply_text:
                send_result = await messaging_service.send_reply(provider, message.sender, reply_text)
            stamp = now_iso()
            with get_db() as con:
                if case_id and isinstance(send_result, dict) and send_result.get("message_id"):
                    outbound_id = messaging_service.storage_message_id(provider, str(send_result["message_id"])[:180])
                    con.execute(
                        "INSERT OR IGNORE INTO whatsapp_outbound_messages (message_id, case_id, purpose, status, created_at, updated_at, error_code, provider) VALUES (?, ?, 'conversation_reply', 'accepted', ?, ?, '', ?)",
                        (outbound_id, case_id, stamp, stamp, provider),
                    )
                con.execute("UPDATE whatsapp_webhook_messages SET status='sent', reply_sent_at=?, lease_until=0, last_error_type='' WHERE message_id=?", (stamp, message_db_id))
            processed += 1
        except Exception as exc:
            failures += 1
            try:
                with get_db() as con:
                    row = con.execute("SELECT status FROM whatsapp_webhook_messages WHERE message_id=?", (message_db_id,)).fetchone()
                    if row:
                        next_status = "processing" if row["status"] == "processing" else "ready"
                        con.execute(
                            "UPDATE whatsapp_webhook_messages SET status=?, lease_until=0, last_error_type=? WHERE message_id=?",
                            (next_status, type(exc).__name__[:80], message_db_id),
                        )
            except Exception:
                logger.warning("Could not release failed %s webhook claim", provider)
            logger.warning("%s WhatsApp webhook message processing failed (%s)", provider, type(exc).__name__)
    return processed, failures


@app.post("/api/webhooks/whatsapp")
async def receive_whatsapp_webhook(request: Request):
    """Accept signed Meta events, then delegate to the shared case/message engine."""
    app_secret = os.getenv("WHATSAPP_APP_SECRET", "").strip()
    if not app_secret or not whatsapp_service.config_status()["cloud_api_ready"]:
        raise HTTPException(status_code=503, detail="WhatsApp messaging is not configured for this installation.")
    raw_body = await request.body()
    if len(raw_body) > 1024 * 1024:
        raise HTTPException(status_code=413, detail="Webhook request is too large.")
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not whatsapp_service.verify_webhook_signature(raw_body, signature, app_secret):
        raise HTTPException(status_code=401, detail="Webhook signature is invalid.")
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="Webhook body must be valid JSON.")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook body must be a JSON object.")
    inbound_messages = whatsapp_service.parse_inbound_messages(payload)
    status_updates = whatsapp_service.parse_status_updates(payload)
    try:
        lease_seconds = int(os.getenv("WHATSAPP_WEBHOOK_LEASE_SECONDS", "180"))
    except ValueError:
        lease_seconds = 180
    lease_seconds = max(30, min(lease_seconds, 600))
    statuses_processed = process_whatsapp_status_updates(status_updates)
    processed, failures = await _process_channel_inbound_messages(
        inbound_messages, request, provider="meta", lease_seconds=lease_seconds,
    )
    if failures:
        raise HTTPException(status_code=503, detail="One or more messages could not be processed.")
    return {"ok": True, "provider": "meta", "received": len(inbound_messages), "processed": processed, "statuses_received": len(status_updates), "statuses_processed": statuses_processed}


@app.post("/api/webhooks/twilio/whatsapp")
async def receive_twilio_whatsapp_webhook(request: Request):
    """Receive Twilio Sandbox inbound messages; SDK signature validation is mandatory."""
    config = twilio_service.config_status()
    meta_config = whatsapp_service.config_status()
    if not config["ready_for_sandbox_testing"] or not meta_config["persistent_identity_ready"]:
        raise HTTPException(status_code=503, detail="Twilio webhook or encrypted contact storage is not configured.")
    raw_body = await request.body()
    if len(raw_body) > 1024 * 1024:
        raise HTTPException(status_code=413, detail="Webhook request is too large.")
    try:
        form = await request.form()
    except Exception:
        raise HTTPException(status_code=400, detail="Twilio webhook must use form-encoded data.")
    params = {key: str(value) for key, value in form.items()}
    signature = request.headers.get("X-Twilio-Signature", "")
    canonical_url = twilio_service.webhook_url_for_request(request)
    if not twilio_service.verify_webhook_signature(canonical_url, params, signature):
        raise HTTPException(status_code=401, detail="Twilio webhook signature is invalid.")
    configured_sender = os.getenv("TWILIO_WHATSAPP_FROM", "").strip()
    posted_to = str(form.get("To", "") or "").strip()
    if configured_sender and posted_to and configured_sender != posted_to:
        raise HTTPException(status_code=400, detail="Twilio webhook destination does not match the configured sender.")
    message = twilio_service.parse_inbound_form(form)
    if message is None:
        # Valid Twilio event with no user message (for example, a callback); acknowledge.
        return Response(content="<Response></Response>", media_type="application/xml", status_code=200)
    try:
        lease_seconds = int(os.getenv("WHATSAPP_WEBHOOK_LEASE_SECONDS", "180"))
    except ValueError:
        lease_seconds = 180
    lease_seconds = max(30, min(lease_seconds, 600))
    processed, failures = await _process_channel_inbound_messages(
        [message], request, provider="twilio", lease_seconds=lease_seconds,
    )
    if failures:
        raise HTTPException(status_code=503, detail="Twilio inbound message could not be processed; please retry.")
    # Outbound replies are sent with the REST API; return empty valid TwiML.
    return Response(content="<Response></Response>", media_type="application/xml", status_code=200)


def process_twilio_status_event(status_event: dict[str, str]) -> bool:
    """Apply a Twilio delivery callback without allowing stale statuses to downgrade it."""
    raw_id = str(status_event.get("message_id", "")).strip()
    status = str(status_event.get("status", "")).strip().lower()
    event_code = str(status_event.get("error_code", "")).strip()[:40]
    if not raw_id or status not in {"accepted", "queued", "sending", "sent", "delivered", "read", "failed", "undelivered"}:
        return False
    normalized = "failed" if status == "undelivered" else status
    db_id = messaging_service.storage_message_id("twilio", raw_id)
    rank = {"accepted": 0, "queued": 1, "sending": 2, "sent": 3, "failed": 4, "delivered": 5, "read": 6}
    event_map = {
        "sent": ("whatsapp_sent", "Twilio reported that the WhatsApp message was sent."),
        "delivered": ("whatsapp_delivered", "Twilio reported that the WhatsApp message was delivered."),
        "read": ("whatsapp_read", "Twilio reported that the WhatsApp message was read."),
        "failed": ("whatsapp_delivery_failed", "Twilio reported that the WhatsApp message could not be delivered."),
    }
    stamp = now_iso()
    with get_db() as con:
        row = con.execute("SELECT message_id, case_id, status FROM whatsapp_outbound_messages WHERE message_id=?", (db_id,)).fetchone()
        if not row:
            return False
        old_status = str(row["status"] or "accepted").lower()
        if old_status in rank and normalized in rank and rank[normalized] < rank[old_status]:
            return True
        if normalized == old_status:
            return True
        con.execute(
            "UPDATE whatsapp_outbound_messages SET status=?, updated_at=?, error_code=? WHERE message_id=?",
            (normalized, stamp, event_code, db_id),
        )
        mapped = event_map.get(normalized)
        if mapped:
            event_type, message = mapped
            record_case_event(
                con, row["case_id"], event_type, message, stamp, actor="system", channel="whatsapp",
                source="provider_status_webhook",
                metadata={"provider": "twilio", "provider_status": normalized, "message_id": raw_id, "error_code": event_code},
            )
    return True


@app.post("/api/webhooks/twilio/whatsapp/status")
async def receive_twilio_whatsapp_status(request: Request):
    """Receive Twilio delivery status callbacks and attach known case-linked IDs."""
    config = twilio_service.config_status()
    if not config["ready_for_sandbox_testing"]:
        raise HTTPException(status_code=503, detail="Twilio webhook is not configured for sandbox testing.")
    raw_body = await request.body()
    if len(raw_body) > 1024 * 1024:
        raise HTTPException(status_code=413, detail="Webhook request is too large.")
    try:
        form = await request.form()
    except Exception:
        raise HTTPException(status_code=400, detail="Twilio callback must use form-encoded data.")
    params = {key: str(value) for key, value in form.items()}
    signature = request.headers.get("X-Twilio-Signature", "")
    canonical_url = twilio_service.webhook_url_for_request(request, status_callback=True)
    if not twilio_service.verify_webhook_signature(canonical_url, params, signature):
        raise HTTPException(status_code=401, detail="Twilio callback signature is invalid.")
    event = twilio_service.parse_status_form(form)
    # WhatsApp read events may arrive as EventType=READ while MessageStatus remains delivered.
    if str(form.get("EventType", "") or "").upper() == "READ":
        event["status"] = "read"
    process_twilio_status_event(event)
    return Response(content="<Response></Response>", media_type="application/xml", status_code=200)


def _inbound_addresses_from_payload(payload: dict) -> list[str]:
    pieces = []
    for key in ("To", "to", "Cc", "cc"):
        value = payload.get(key)
        if isinstance(value, str):
            pieces.append(value[:2048])
    for key in ("ToFull", "CcFull", "Recipients"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value[:30]:
                if isinstance(item, dict):
                    pieces.append(str(item.get("Email") or item.get("email") or "")[:2048])
                elif isinstance(item, str):
                    pieces.append(item[:2048])
    addresses = []
    for _name, address in getaddresses(pieces):
        normal = address.strip().lower()
        if normal and normal not in addresses:
            addresses.append(normal)
    return addresses[:60]


def _inbound_alias_from_address(address: str, domain: str) -> str:
    try:
        local, actual_domain = address.rsplit("@", 1)
    except ValueError:
        return ""
    if actual_domain.lower().rstrip(".") != domain.lower().rstrip("."):
        return ""
    match = re.fullmatch(r"br-([a-f0-9]{60})", local)
    return match.group(1) if match else ""


def _inbound_message_public_view(row: sqlite3.Row, fernet: Fernet) -> dict:
    item = dict(row)
    try:
        subject = fernet.decrypt(str(item.pop("subject_ciphertext", "")).encode("ascii")).decode("utf-8") if item.get("subject_ciphertext") else "(No subject)"
        body = fernet.decrypt(str(item.pop("body_ciphertext", "")).encode("ascii")).decode("utf-8") if item.get("body_ciphertext") else ""
    except (InvalidToken, UnicodeDecodeError, ValueError):
        subject, body = "Unable to decrypt message", "The encrypted content could not be opened. Ask the operator to check the stable inbox encryption key."
    try:
        attachments = json.loads(item.pop("attachments_json", "[]") or "[]")
    except (TypeError, json.JSONDecodeError):
        attachments = []
    return {
        "inbound_id": item["inbound_id"],
        "sender_domain": item.get("sender_domain", ""),
        "sender_identity_verified": False,
        "subject": subject,
        "body": body,
        "received_at": item.get("received_at", ""),
        "status": item.get("status", "pending_review"),
        "attachments": attachments,
        "notice": "Email text is untrusted. Sender identity and statements are not independently verified. Attachments are listed but not imported.",
    }


@app.post("/api/webhooks/inbound-email")
async def receive_inbound_case_email(request: Request):
    """Receive provider-parsed inbound mail addressed to a random case-specific alias.

    Configure the provider to POST to this HTTPS endpoint using the bearer token or
    HTTP Basic credentials configured server-side. Email body/subject are scrubbed,
    encrypted at rest, and retained only while awaiting user review.
    """
    capability = inbound_email_capability()
    if not capability["enabled"]:
        raise HTTPException(status_code=503, detail="Case Inbox Bridge is not configured for this deployment.")
    if not _inbound_webhook_authorized(request):
        raise HTTPException(status_code=401, detail="Webhook authentication failed.")
    try:
        content_length = int(request.headers.get("content-length", "0") or "0")
    except ValueError:
        content_length = 0
    if content_length > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Inbound email payload is too large. Remove large attachments and forward the text only.")
    raw = await request.body()
    if len(raw) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Inbound email payload is too large. Remove large attachments and forward the text only.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Expected a provider-parsed inbound email JSON payload.") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Inbound email payload must be a JSON object.")

    domain = str(os.getenv("BOLKE_INBOUND_EMAIL_DOMAIN", "")).strip().lower().rstrip(".")
    token = ""
    for address in _inbound_addresses_from_payload(payload):
        candidate = _inbound_alias_from_address(address, domain)
        if candidate:
            token = candidate
            break
    if not token:
        # Don't disclose whether an address matches an active case inbox; accept provider
        # delivery to prevent retries and keep aliases resistant to enumeration.
        return {"ok": True, "accepted": False, "reason": "No active case alias matched."}

    fernet = inbound_email_fernet()
    body = _safe_email_body(payload)
    if not body:
        body = "(This email did not include a readable text body. Open the original email and paste the relevant wording into the case.)"
    subject_result = scrub_sensitive_text(str(payload.get("Subject") or payload.get("subject") or "(No subject)")[:1000]).text
    subject = re.sub(r"\s+", " ", subject_result).strip()[:180] or "(No subject)"
    from_value = str(payload.get("From") or payload.get("from") or "")[:320]
    parsed_senders = getaddresses([from_value])
    sender_address = next((addr.strip().lower() for _, addr in parsed_senders if "@" in addr), "")
    sender_domain = sender_address.rsplit("@", 1)[-1][:253] if sender_address else ""

    attachment_items = payload.get("Attachments") or payload.get("attachments") or []
    safe_attachments = []
    if isinstance(attachment_items, list):
        for attachment in attachment_items[:10]:
            if not isinstance(attachment, dict):
                continue
            name = Path(str(attachment.get("Name") or attachment.get("name") or "attachment")[:512].replace("\\", "/")).name
            size_bytes = _safe_nonnegative_size(attachment.get("ContentLength") or attachment.get("size_bytes") or 0)
            safe_attachments.append({
                "name": scrub_sensitive_text(name).text[:120] or "attachment",
                "content_type": str(attachment.get("ContentType") or attachment.get("content_type") or "unknown")[:100],
                "size_bytes": size_bytes,
                "imported": False,
            })

    provider_id = str(payload.get("MessageID") or payload.get("MessageId") or payload.get("message_id") or "").strip()[:240]
    if not provider_id:
        provider_id = "sha256:" + hashlib.sha256(raw).hexdigest()
    stamp = now_iso()
    inbound_id = uuid.uuid4().hex
    with get_db() as con:
        _expire_inbound_email(con)
        inbox = con.execute("SELECT case_id FROM case_inboxes WHERE alias_hash=? AND enabled=1", (_inbound_alias_hash(token),)).fetchone()
        if not inbox:
            return {"ok": True, "accepted": False, "reason": "No active case alias matched."}
        case_id = inbox["case_id"]
        pending_count = con.execute("SELECT COUNT(*) FROM inbound_email_messages WHERE case_id=? AND status='pending_review'", (case_id,)).fetchone()[0]
        if pending_count >= 10:
            raise HTTPException(status_code=429, detail="This case already has 10 replies awaiting review. Open the case and review or discard them before forwarding more.")
        already = con.execute("SELECT inbound_id FROM inbound_email_messages WHERE provider_message_id=?", (provider_id,)).fetchone()
        if already:
            return {"ok": True, "accepted": True, "duplicate": True}
        try:
            con.execute(
                "INSERT INTO inbound_email_messages (inbound_id, case_id, provider_message_id, sender_domain, subject_ciphertext, body_ciphertext, received_at, status, attachments_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_review', ?, ?)",
                (inbound_id, case_id, provider_id, sender_domain, fernet.encrypt(subject.encode("utf-8")).decode("ascii"), fernet.encrypt(body.encode("utf-8")).decode("ascii"), stamp, json.dumps(safe_attachments, ensure_ascii=False), stamp),
            )
        except sqlite3.IntegrityError:
            return {"ok": True, "accepted": True, "duplicate": True}
        con.execute("UPDATE case_inboxes SET last_received_at=?, updated_at=? WHERE case_id=?", (stamp, stamp, case_id))
        con.execute("UPDATE cases SET updated_at=?, status=? WHERE case_id=?", (stamp, "Reply awaiting review", case_id))
        record_case_event(
            con, case_id, "inbound_email_received",
            "A forwarded email arrived in this case inbox. Its sender and statements are not independently verified; review it before using it.",
            stamp, actor="system", channel="email", source="inbound_email_webhook",
            metadata={"inbound_message_id": inbound_id, "attachments_count": len(safe_attachments), "review_required": True, "sender_identity_verified": False},
        )
    return {"ok": True, "accepted": True, "pending_review": True}


@app.get("/api/cases/{case_id}/inbox")
def get_case_inbox(case_id: str):
    normalized_id = case_id.upper()
    with get_db() as con:
        require_case_access(con, normalized_id)
        _expire_inbound_email(con, normalized_id)
        capability = inbound_email_capability()
        inbox = con.execute("SELECT * FROM case_inboxes WHERE case_id=? AND enabled=1", (normalized_id,)).fetchone()
        address = ""
        messages = []
        if capability["enabled"]:
            fernet = inbound_email_fernet()
            if inbox:
                try:
                    token = fernet.decrypt(inbox["alias_ciphertext"].encode("ascii")).decode("utf-8")
                    address = f"br-{token}@{os.getenv('BOLKE_INBOUND_EMAIL_DOMAIN','').strip().lower().rstrip('.')}"
                except (InvalidToken, UnicodeDecodeError, ValueError):
                    raise HTTPException(status_code=503, detail="The case inbox cannot be opened with the current encryption key. Restore the configured key or rotate the inbox.")
            rows = con.execute("SELECT * FROM inbound_email_messages WHERE case_id=? AND status='pending_review' ORDER BY received_at DESC LIMIT 10", (normalized_id,)).fetchall()
            messages = [_inbound_message_public_view(row, fernet) for row in rows]
        return {
            **capability,
            "address": address,
            "created_at": inbox["created_at"] if inbox else "",
            "last_received_at": inbox["last_received_at"] if inbox else "",
            "pending_count": len(messages),
            "messages": messages,
            "retention_days": inbound_email_retention_days(),
        }


@app.post("/api/cases/{case_id}/inbox", status_code=201)
def create_case_inbox(case_id: str):
    normalized_id = case_id.upper()
    capability = inbound_email_capability()
    if not capability["enabled"]:
        raise HTTPException(status_code=503, detail="Case Inbox Bridge is optional and is not configured. Set the inbound email domain, encryption key and webhook authentication on the server first.")
    fernet = inbound_email_fernet()
    with get_db() as con:
        require_case_access(con, normalized_id)
        existing = con.execute("SELECT * FROM case_inboxes WHERE case_id=? AND enabled=1", (normalized_id,)).fetchone()
        if existing:
            try:
                token = fernet.decrypt(existing["alias_ciphertext"].encode("ascii")).decode("utf-8")
            except (InvalidToken, UnicodeDecodeError, ValueError) as exc:
                raise HTTPException(status_code=503, detail="The existing case inbox cannot be decrypted. Rotate it after checking the configured key.") from exc
            return {"enabled": True, "created": False, "address": f"br-{token}@{os.getenv('BOLKE_INBOUND_EMAIL_DOMAIN','').strip().lower().rstrip('.')}", "notice": capability["notice"]}
        token = secrets.token_hex(30)
        stamp = now_iso()
        con.execute(
            "INSERT INTO case_inboxes (case_id, alias_hash, alias_ciphertext, enabled, created_at, updated_at) VALUES (?, ?, ?, 1, ?, ?)",
            (normalized_id, _inbound_alias_hash(token), fernet.encrypt(token.encode("utf-8")).decode("ascii"), stamp, stamp),
        )
        record_case_event(con, normalized_id, "case_inbox_created", "A private case-specific email forwarding address was created. It accepts forwarded replies for manual review; it does not send email or contact a merchant.", stamp, actor="user", channel="web", source="case_inbox_setup", metadata={"inbound_email_enabled": True})
    address = f"br-{token}@{os.getenv('BOLKE_INBOUND_EMAIL_DOMAIN','').strip().lower().rstrip('.')}"
    return {"enabled": True, "created": True, "address": address, "notice": capability["notice"]}


@app.post("/api/cases/{case_id}/inbox/rotate")
def rotate_case_inbox(case_id: str):
    normalized_id = case_id.upper()
    if not inbound_email_capability()["enabled"]:
        raise HTTPException(status_code=503, detail="Case Inbox Bridge is not configured.")
    fernet = inbound_email_fernet()
    token = secrets.token_hex(30)
    stamp = now_iso()
    with get_db() as con:
        require_case_access(con, normalized_id)
        existing = con.execute("SELECT case_id FROM case_inboxes WHERE case_id=? AND enabled=1", (normalized_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Create a case inbox first.")
        con.execute("UPDATE case_inboxes SET alias_hash=?, alias_ciphertext=?, updated_at=? WHERE case_id=?", (_inbound_alias_hash(token), fernet.encrypt(token.encode("utf-8")).decode("ascii"), stamp, normalized_id))
        record_case_event(con, normalized_id, "case_inbox_rotated", "The case inbox address was rotated. The previous forwarding address no longer routes to this case.", stamp, actor="user", channel="web", source="case_inbox_setup", metadata={"inbound_email_enabled": True})
    domain = os.getenv("BOLKE_INBOUND_EMAIL_DOMAIN", "").strip().lower().rstrip(".")
    return {"enabled": True, "rotated": True, "address": f"br-{token}@{domain}", "notice": "The previous address has been disabled. Update forwarding rules and keep this address private."}


@app.post("/api/cases/{case_id}/inbox/messages/{inbound_id}/preview")
def preview_inbound_email_message(case_id: str, inbound_id: str):
    normalized_id = case_id.upper()
    fernet = inbound_email_fernet()
    with get_db() as con:
        require_case_access(con, normalized_id)
        row = con.execute("SELECT body_ciphertext FROM inbound_email_messages WHERE case_id=? AND inbound_id=? AND status='pending_review'", (normalized_id, inbound_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="This forwarded reply is no longer waiting for review.")
        try:
            text = fernet.decrypt(row["body_ciphertext"].encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail="This message could not be decrypted. Check the configured stable inbox encryption key.") from exc
    safe_text = scrub_sensitive_text(text)
    result = review_support_reply(safe_text.text)
    return {
        "inbound_id": inbound_id,
        "review": result,
        "raw_message_saved_encrypted_until_review": True,
        "redacted_categories": sorted(set(safe_text.redacted_types)),
        "notice": "This is a first-pass interpretation, not proof of what the organisation did. The encrypted inbox copy remains pending until you confirm or discard it.",
    }


@app.post("/api/cases/{case_id}/inbox/messages/{inbound_id}/confirm", status_code=201)
def confirm_inbound_email_message(case_id: str, inbound_id: str, request: InboundEmailConfirmRequest):
    if not request.confirmed:
        raise HTTPException(status_code=400, detail="Confirm that you reviewed the original email before saving its interpretation.")
    normalized_id = case_id.upper()
    fernet = inbound_email_fernet()
    stamp = now_iso()
    clean_reference = scrub_sensitive_text(request.reference.strip()) if request.reference.strip() else None
    with get_db() as con:
        require_case_access(con, normalized_id)
        row = con.execute("SELECT body_ciphertext FROM inbound_email_messages WHERE case_id=? AND inbound_id=? AND status='pending_review'", (normalized_id, inbound_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="This forwarded reply is no longer waiting for review.")
        try:
            original_text = fernet.decrypt(row["body_ciphertext"].encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail="This message could not be decrypted. Check the configured stable inbox encryption key.") from exc
        safe_text = scrub_sensitive_text(original_text)
        result = review_support_reply(safe_text.text)
        message = (
            f"The user reviewed a forwarded email. First-pass category: {result['label']}. Suggested next action: {result['next_step']} "
            "The forwarded email's sender identity and claims were not independently verified. The encrypted raw body was cleared after this confirmation."
        )
        metadata = {
            "reply_review_category": result["category"], "reply_review_label": result["label"],
            "reply_review_engine": result["engine"], "reply_interpretation_confirmed": True,
            "raw_reply_retained": False, "inbound_message_id": inbound_id,
            "sender_identity_verified": False,
            "redacted_categories": sorted(set(safe_text.redacted_types)),
        }
        if clean_reference and clean_reference.text:
            metadata["reference_provided"] = clean_reference.text[:120]
            message += " A user-supplied reference was recorded privately."
        con.execute("UPDATE inbound_email_messages SET body_ciphertext='', subject_ciphertext='', attachments_json='[]', status='confirmed', reviewed_at=? WHERE case_id=? AND inbound_id=?", (stamp, normalized_id, inbound_id))
        reply_stage = stage_for_reply_category(result["category"])
        con.execute("UPDATE cases SET case_stage=?, updated_at=?, status=? WHERE case_id=?", (reply_stage, stamp, "Forwarded reply reviewed", normalized_id))
        record_case_event(con, normalized_id, "response_received", message, stamp, actor="user", channel="email", source="user_confirmed_inbound_email_review", metadata=metadata)
        return {"ok": True, "review": result, "raw_message_retained": False, "case": case_bundle(con, normalized_id)}


@app.delete("/api/cases/{case_id}/inbox/messages/{inbound_id}")
def discard_inbound_email_message(case_id: str, inbound_id: str):
    normalized_id = case_id.upper()
    stamp = now_iso()
    with get_db() as con:
        require_case_access(con, normalized_id)
        row = con.execute("SELECT inbound_id FROM inbound_email_messages WHERE case_id=? AND inbound_id=? AND status='pending_review'", (normalized_id, inbound_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="This forwarded reply is no longer waiting for review.")
        con.execute("UPDATE inbound_email_messages SET subject_ciphertext='', body_ciphertext='', attachments_json='[]', status='discarded', reviewed_at=? WHERE case_id=? AND inbound_id=?", (stamp, normalized_id, inbound_id))
        record_case_event(con, normalized_id, "inbound_email_discarded", "The user discarded a forwarded email. Its encrypted content and attachment metadata were cleared without changing the recommended plan.", stamp, actor="user", channel="web", source="case_inbox_discard", metadata={"inbound_message_id": inbound_id, "raw_reply_retained": False})
        return {"ok": True, "discarded": True, "raw_message_retained": False}


@app.get("/api/support-directory")
def support_directory_lookup(merchant: str = "", description: str = "", issue_type: str = "") -> dict:
    """Return official-route suggestions and a carefully caveated NCH snapshot match."""
    safe_merchant = scrub_sensitive_text(str(merchant or "")[:100]).text
    safe_description = scrub_sensitive_text(str(description or "")[:1000]).text
    safe_issue = scrub_sensitive_text(str(issue_type or "")[:80]).text
    return {
        "merchant": safe_merchant,
        "reviewed_on": NCH_CONVERGENCE_REVIEWED_ON,
        "source_url": NCH_CONVERGENCE_DIRECTORY_URL,
        "destinations": find_support_destinations(safe_merchant, safe_description, safe_issue),
        "nch_directory_match": find_nch_convergence_match(safe_merchant),
        "notice": "Directory matching uses a small reviewed snapshot, not a live government API. A match does not mean a complaint was filed or BolKeResolve is an NCH partner.",
    }


@app.post("/share-target", response_class=HTMLResponse)
async def receive_pwa_share(request: Request):
    """Receive a Web Share Target POST into a short-lived encrypted staging area.

    Nothing is attached to a case until the user reviews the preview and chooses an action.
    This route is for supported installed PWAs; manual upload remains the fallback.
    """
    try:
        share_limit = max(3, min(60, int(os.getenv("BOLKE_SHARE_TARGET_LIMIT_PER_MINUTE", "12"))))
    except (ValueError, OverflowError):
        share_limit = 12
    # Unlike a normal case mutation, this route must accept a browser share-sheet POST
    # that can originate from another app. Rate-limit it and keep the staged content
    # encrypted rather than trying to treat it as a same-origin case mutation.
    enforce_public_preview_rate_limit(request, "share-target", share_limit)
    content_length = request.headers.get("content-length", "")
    if content_length.isdigit() and int(content_length) > MAX_EVIDENCE_BYTES + 220_000:
        raise HTTPException(status_code=413, detail="Shared item is too large. Share one file up to 8 MB, or use the regular upload flow.")
    capability = share_intake_capability()
    if not capability["enabled"]:
        return HTMLResponse(
            "<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Share intake unavailable</title><main style='font:16px system-ui;max-width:620px;margin:12vh auto;padding:24px;color:#103a35'>"
            "<h1>Share-to-Case is not configured yet</h1><p>This deployment cannot safely stage a shared item because its encryption key is not configured. "
            "Open BolKeResolve and use the normal evidence upload instead.</p><p><a href='/'>Back to BolKeResolve</a></p></main>",
            status_code=503,
            headers={"Cache-Control": "no-store"},
        )
    try:
        form = await request.form(max_files=2, max_fields=8, max_part_size=220_000)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The shared item could not be read. Try sharing it again or use normal upload.") from exc
    title = str(form.get("title") or "").strip()[:500]
    text = str(form.get("text") or "").strip()[:8000]
    url_value = str(form.get("url") or "").strip()[:3000]
    safe_title = _safe_shared_text(title)[:180]
    safe_text = _safe_shared_text(text)[:6000]
    safe_url = ""
    if url_value:
        try:
            parsed = urlsplit(url_value)
            if parsed.scheme.lower() == "https" and parsed.hostname and not parsed.username and not parsed.password:
                safe_url = url_value
        except ValueError:
            safe_url = ""
    files = [item for item in (form.getlist("shared_file") + form.getlist("files")) if isinstance(item, StarletteUploadFile)]
    if len(files) > 1:
        await form.close()
        raise HTTPException(status_code=413, detail="Share one file at a time. You can add other files from the case screen.")
    filename = ""
    mime_type = ""
    file_bytes: bytes | None = None
    if files:
        upload = files[0]
        filename = _safe_shared_filename(upload.filename or "shared-file")
        file_bytes = await upload.read(MAX_EVIDENCE_BYTES + 1)
        try:
            _, mime_type = _validate_shared_evidence(filename, file_bytes)
        except HTTPException:
            await form.close()
            raise
    # The payload has been copied into bounded memory; close multipart temp files now.
    try:
        await form.close()
    except Exception:
        pass
    if not (safe_title or safe_text or safe_url or file_bytes):
        raise HTTPException(status_code=400, detail="Nothing shareable was received. Try sharing a screenshot, PDF, text or HTTPS link.")
    fernet = share_intake_fernet()
    token = secrets.token_urlsafe(32)
    now = now_iso()
    expiry = int(time.time()) + share_intake_retention_minutes() * 60
    encrypt_text = lambda value: fernet.encrypt(value.encode("utf-8")).decode("ascii") if value else ""
    with get_db() as con:
        _expire_shared_intakes(con)
        pending_count = con.execute("SELECT COUNT(*) FROM pending_share_intakes WHERE consumed_at='' AND expires_at>=?", (int(time.time()),)).fetchone()[0]
        if pending_count >= 500:
            raise HTTPException(status_code=429, detail="Share intake is temporarily busy. Please use the normal upload flow and try again later.")
        con.execute(
            "INSERT INTO pending_share_intakes (token_hash,title_ciphertext,text_ciphertext,url_ciphertext,filename_ciphertext,mime_type,file_ciphertext,size_bytes,created_at,expires_at,consumed_at) VALUES (?,?,?,?,?,?,?,?,?,?, '')",
            (hashlib.sha256(token.encode("utf-8")).hexdigest(), encrypt_text(safe_title), encrypt_text(safe_text), encrypt_text(safe_url), encrypt_text(filename), mime_type, fernet.encrypt(file_bytes) if file_bytes else None, len(file_bytes or b""), now, expiry),
        )
    response = RedirectResponse(url=f"/#shared_intake={quote(token, safe='')}", status_code=303)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/api/shared-intake/preview")
def preview_shared_intake(request: Request, x_share_intake_token: str = Header(default="", alias="X-Share-Intake-Token")) -> dict:
    if AUTH_REQUIRED:
        enforce_public_preview_rate_limit(request, "shared-intake-preview", 20)
    token = x_share_intake_token.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{30,100}", token):
        raise HTTPException(status_code=404, detail="This shared item is unavailable or has expired.")
    fernet = share_intake_fernet()
    with get_db() as con:
        row = _shared_intake_row(con, token)
        title = _decrypt_share_value(fernet, row["title_ciphertext"])
        text = _decrypt_share_value(fernet, row["text_ciphertext"])
        source_url = _decrypt_share_value(fernet, row["url_ciphertext"])
        filename = _decrypt_share_value(fernet, row["filename_ciphertext"])
        domain = ""
        try:
            parsed = urlsplit(source_url)
            if parsed.scheme == "https" and parsed.hostname:
                domain = parsed.hostname[:253]
        except ValueError:
            domain = ""
        return {
            "title": title,
            "text": _safe_shared_text(text)[:6000],
            "source_domain": domain,
            "has_file": bool(row["file_ciphertext"]),
            "filename": filename,
            "mime_type": row["mime_type"],
            "size_bytes": int(row["size_bytes"] or 0),
            "expires_in_seconds": max(0, int(row["expires_at"]) - int(time.time())),
            "notice": "Review this shared item. It has not been added to a case, and the sender/source is not independently verified.",
        }


@app.post("/api/shared-intake/attach")
def attach_shared_intake(body: SharedIntakeAttachRequest, x_share_intake_token: str = Header(default="", alias="X-Share-Intake-Token")) -> dict:
    """Attach a reviewed shared item using a fixed URL; values stay in header/body, not path/query."""
    token = x_share_intake_token.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{30,100}", token):
        raise HTTPException(status_code=404, detail="This shared item is unavailable or has expired.")
    normalized_id = body.case_id.strip().upper()
    include_context = body.include_context
    fernet = share_intake_fernet()
    stored_path: Path | None = None
    with get_db() as con:
        row = _shared_intake_row(con, token)
        require_case_access(con, normalized_id)
        title = _decrypt_share_value(fernet, row["title_ciphertext"])
        text = _safe_shared_text(_decrypt_share_value(fernet, row["text_ciphertext"]))[:6000]
        source_url = _decrypt_share_value(fernet, row["url_ciphertext"])
        filename = _safe_shared_filename(_decrypt_share_value(fernet, row["filename_ciphertext"])) if row["filename_ciphertext"] else ""
        source_domain = ""
        try:
            parsed = urlsplit(source_url)
            if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password:
                source_domain = parsed.hostname[:253]
        except ValueError:
            source_domain = ""
        file_bytes = fernet.decrypt(row["file_ciphertext"]) if row["file_ciphertext"] else None
        mime = ""
        if file_bytes:
            ext, mime = _validate_shared_evidence(filename, file_bytes)
            usage = con.execute("SELECT COUNT(*) AS file_count, COALESCE(SUM(size_bytes),0) AS bytes_used FROM evidence WHERE case_id=?", (normalized_id,)).fetchone()
            if usage["file_count"] >= 10:
                raise HTTPException(status_code=413, detail="This case already has the maximum of 10 evidence files. The shared item remains available until it expires.")
            if usage["bytes_used"] + len(file_bytes) > 40 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="This case has reached its 40 MB evidence limit. The shared item remains available until it expires.")
        evidence_id = ""
        created = now_iso()
        try:
            if file_bytes:
                evidence_id = uuid.uuid4().hex
                stored_name = evidence_id + ext
                stored_path = UPLOAD_DIR / stored_name
                stored_path.write_bytes(file_bytes)
                safe_name = scrub_sensitive_text(filename).text[:180] or "shared-file"
                con.execute(
                    "INSERT INTO evidence (evidence_id, case_id, original_name, stored_name, mime_type, size_bytes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (evidence_id, normalized_id, safe_name, stored_name, mime, len(file_bytes), created),
                )
            message = "A shared item was added to this case by you. The source and its claims have not been independently verified."
            if title:
                message += f" Item: {title[:160]}."
            if source_domain:
                message += f" Source domain: {source_domain}."
            if include_context and text:
                message += f" Shared text you chose to include: {text[:800]}"
            if file_bytes:
                message += f" Saved file: {filename[:160]}."
            record_case_event(
                con, normalized_id, "shared_item_added", message, created,
                actor="user", channel="share_target", source="user_confirmed_share",
                metadata={"title": title[:180], "source_domain": source_domain, "shared_text_included": bool(include_context and text), "evidence_id": evidence_id or None, "file_authenticity_verified": False},
            )
            con.execute("UPDATE cases SET updated_at=?, status=? WHERE case_id=?", (created, "Shared item added", normalized_id))
            con.execute("UPDATE pending_share_intakes SET title_ciphertext='',text_ciphertext='',url_ciphertext='',filename_ciphertext='',mime_type='',file_ciphertext=NULL,size_bytes=0,consumed_at=? WHERE token_hash=?", (created, hashlib.sha256(token.encode("utf-8")).hexdigest()))
            result = case_bundle(con, normalized_id)
        except Exception:
            if stored_path and stored_path.exists():
                try:
                    stored_path.unlink()
                except OSError:
                    logger.warning("Unable to clean up a staged share file after a failed attach")
            raise
    return {"ok": True, "attached": True, "evidence_id": evidence_id or None, "case": result, "raw_share_content_retained": False}


@app.delete("/api/shared-intake/discard")
def discard_shared_intake(x_share_intake_token: str = Header(default="", alias="X-Share-Intake-Token")) -> dict:
    token = x_share_intake_token.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{30,100}", token):
        raise HTTPException(status_code=404, detail="This shared item is unavailable or has expired.")
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with get_db() as con:
        row = con.execute("SELECT token_hash FROM pending_share_intakes WHERE token_hash=? AND consumed_at=''", (token_hash,)).fetchone()
        if not row:
            return {"ok": True, "discarded": True}
        con.execute("DELETE FROM pending_share_intakes WHERE token_hash=?", (token_hash,))
    return {"ok": True, "discarded": True}


@app.get("/api/config")
def public_config(request: Request) -> dict:
    # Public display settings only. Never expose tokens or private provider credentials.
    # Match the actual transcription endpoint: authenticated users may use configured
    # voice in production; BOLKE_PUBLIC_VOICE_ENABLED gates only anonymous requests.
    session_token = request.cookies.get(SESSION_COOKIE_NAME, "")
    authenticated_user = bool(lookup_session_user(session_token)) if session_token else False
    public_voice_enabled = os.getenv("BOLKE_PUBLIC_VOICE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    voice_provider_ready = bool(os.getenv("GNANI_API_KEY", "").strip())
    guided_voice_enabled = voice_provider_ready and (not AUTH_REQUIRED or authenticated_user or public_voice_enabled)
    config = whatsapp_service.config_status()
    twilio_config = twilio_service.config_status()
    twilio_common_gates = bool(config["persistent_identity_ready"] and config["privacy_policy_configured"] and config["support_escalation_configured"])
    return {
        "whatsapp_business_number": config["business_number"],
        "whatsapp_cloud_api_ready": config["cloud_api_ready"],
        "whatsapp_privacy_policy_configured": config["privacy_policy_configured"],
        "whatsapp_support_escalation_configured": config["support_escalation_configured"],
        "whatsapp_reminder_template_configured": bool(os.getenv("WHATSAPP_REMINDER_TEMPLATE_NAME", "").strip()),
        "whatsapp_provider_preference": messaging_service.selected_provider(),
        "twilio_whatsapp_configured": bool(twilio_config["ready_for_sandbox_testing"] and twilio_common_gates),
        "twilio_webhook_url_configured": bool(twilio_config["webhook_url_configured"]),
        "auth_required": AUTH_REQUIRED,
        "accounts_enabled": AUTH_ENABLED,
        "email_verification_required": EMAIL_VERIFICATION_REQUIRED,
        "auth_email_delivery_configured": bool(auth_email_delivery_capability()["configured"]),
        "auth_email_delivery_provider": auth_email_delivery_capability()["provider"],
        "guided_voice_enabled": guided_voice_enabled,
        "multilingual_guidance_available": agent_assist.configured(),
        "visual_evidence_ai_available": agent_assist.configured(),
        "case_interpretation_ai_available": agent_assist.configured(),
        "gnani_tts_model": os.getenv("GNANI_TTS_MODEL", "timbre-v2.5").strip(),
        "case_inbox_bridge_available": bool(inbound_email_capability()["enabled"]),
        "share_target_available": bool(share_intake_capability()["enabled"]),
        "official_route_directory_reviewed_on": NCH_CONVERGENCE_REVIEWED_ON,
        "resolution_rulebook_version": RULEBOOK_VERSION,
        "resolution_rulebook_reviewed_on": RULEBOOK_REVIEWED_ON,
        "environment": DEPLOYMENT_ENV,
    }


@app.get("/api/health")
def health() -> dict:
    database_ready = False
    try:
        with get_db() as con:
            con.execute("SELECT 1").fetchone()
        database_ready = True
    except sqlite3.Error:
        database_ready = False
    return {
        "ok": database_ready,
        "database_ready": database_ready,
        "app": "BolKeResolve",
        # Expose product capability, not vendor names or account configuration details.
        "voice_input_configured": bool(os.getenv("GNANI_API_KEY", "").strip()),
        "read_aloud_configured": bool(os.getenv("GNANI_API_KEY", "").strip()),
        "supported_speech_languages": sorted(LANGUAGES.keys()),
        "language_recognition_option_available": True,
        "supported_read_aloud_languages": sorted(TTS_VOICES_BY_LANGUAGE.keys()),
        "external_payment_verification": False,
        "merchant_contact": False,
        "resolution_engine": "deterministic official-source playbooks v1",
        "resolution_engine_ready": True,
        "resolution_rulebook_version": RULEBOOK_VERSION,
        "resolution_rulebook_reviewed_on": RULEBOOK_REVIEWED_ON,
        "share_target_available": bool(share_intake_capability()["enabled"]),
        "mode": "production-auth-protected" if AUTH_REQUIRED else "local-development-only",
        "authentication_required": AUTH_REQUIRED,
        "accounts_enabled": AUTH_ENABLED,
    }


def looks_like_english_rendered_in_devanagari(text: str) -> bool:
    """Recognise a common ASR failure mode: English speech emitted as Hindi-script phonetics."""
    if not re.search(r"[\u0900-\u097f]", text or ""):
        return False
    tokens = set(re.findall(r"[\u0900-\u097f]+", (text or "").lower()))
    markers = {"आई", "आइ", "हेव", "हैव", "नॉट", "नोट", "गॉट", "गोट", "दी", "द", "फ्रॉम", "फ्राम", "बैक", "प्लीज", "प्लीज़", "माई", "हैज़", "हैज", "बीन", "डेज़", "डेज", "कैन", "यू", "व्हाट", "वॉट", "ऑर्डर", "फूड", "कैंसल", "कस्टमर", "सपोर्ट", "कॉन्टैक्ट", "कॉन्टैक्टेड", "रिफंड"}
    return len(tokens & markers) >= 3


def transliterate_english_phonetics(text: str) -> str:
    """Turn common English-as-Devanagari ASR output into readable English tokens.

    This is a conservative presentation fallback, not machine translation. Unknown
    Indic words are preserved verbatim so merchant names or genuine Hindi are not lost.
    """
    token_map = {
        "आई": "I", "आइ": "I", "हेव": "have", "हैव": "have", "नॉट": "not", "नोट": "not",
        "गॉट": "got", "गोट": "got", "दी": "the", "द": "the", "फ्रॉम": "from", "फ्राम": "from",
        "बैक": "back", "प्लीज": "please", "प्लीज़": "please", "माई": "my", "हैज़": "has", "हैज": "has",
        "बीन": "been", "डेज़": "days", "डेज": "days", "कैन": "can", "यू": "you", "व्हाट": "what",
        "वॉट": "what", "ऑर्डर": "order", "फूड": "food", "कैंसल": "cancelled", "कस्टमर": "customer",
        "सपोर्ट": "support", "कॉन्टैक्ट": "contact", "कॉन्टैक्टेड": "contacted", "रिफंड": "refund",
        "ऑफ": "of", "जोमैटो": "Zomato", "ज़ोमैटो": "Zomato", "जमैटो": "Zomato", "जॉमैटो": "Zomato",
        "दट": "that", "दैट": "that", "दे": "they", "लाइक": "like", "गिव": "give", "मी": "me",
        "इन": "in", "दिस": "this", "इशू": "issue", "बेस्ट": "best", "पॉसिबल": "possible",
        "मोर": "more", "देन": "than", "सेवन": "seven", "थ्री": "three", "इट": "it", "बट": "but",
        "वाज़": "was", "वाज": "was", "ऑर्डर्स": "orders", "नाहीं": "not", "फूड": "food",
        "रिसीव्ड": "received", "रीसीव्ड": "received", "रिसीव": "receive", "ऑलरेडी": "already",
        "कॉल": "call", "किया": "did", "हेल्प": "help", "टू": "to", "इनफॉर्म": "inform",
    }
    if not looks_like_english_rendered_in_devanagari(text):
        return text
    parts = re.findall(r"[\u0900-\u097f]+|[A-Za-z]+(?:['’][A-Za-z]+)?|\d+(?:[.,]\d+)?|[^\w\s]+|\s+", text)
    converted = []
    for part in parts:
        key = part.lower()
        if key in token_map:
            converted.append(token_map[key])
        else:
            converted.append(part)
    result = "".join(converted)
    # Keep spacing natural where token replacement changed word lengths; punctuation remains.
    return re.sub(r"[ \t]{2,}", " ", result).strip()


def looks_like_hindi_mislabelled_as_marathi(text: str) -> bool:
    """Small conservative lexical check for a Hindi sentence sent under Marathi locale."""
    lower = (text or "").lower()
    hindi_markers = ("मुझे", "मेरा", "मेरी", "मेरे", "नहीं आया", "नहीं मिला", "नहीं है", "कर दिया", "हो गया", "बताइए", "किया है")
    marathi_markers = ("मला", "माझा", "माझी", "माझे", "नाही", "आहे", "झाले", "केले", "परतावा")
    return sum(token in lower for token in hindi_markers) >= 2 and not any(token in lower for token in marathi_markers)


@app.post("/api/voice/transcribe")
async def transcribe_audio(
    request: Request,
    audio_file: UploadFile = File(...),
    language_code: str = Form("auto"),
):
    """Transcribe uploaded audio; auto mode asks Prisma REST to detect among supported locales."""
    requested_language = (language_code or "auto").strip()
    auto_mode = requested_language.lower() in {"auto", "auto-detect", "detect"}
    if not auto_mode and requested_language not in LANGUAGES:
        raise HTTPException(status_code=400, detail="Choose Auto-detect or a supported speech language.")

    key = check_gnani_key()
    session_token = request.cookies.get(SESSION_COOKIE_NAME, "")
    anonymous_in_production = AUTH_REQUIRED and not lookup_session_user(session_token)
    if anonymous_in_production:
        if os.getenv("BOLKE_PUBLIC_VOICE_ENABLED", "false").strip().lower() not in {"1", "true", "yes", "on"}:
            raise HTTPException(status_code=401, detail="Sign in to use voice input, or type your story. Public voice input has not been enabled on this site.")
        enforce_voice_rate_limit(request, "stt-public", int(os.getenv("BOLKE_PUBLIC_STT_LIMIT_PER_MINUTE", "3")))
    else:
        enforce_voice_rate_limit(request, "stt", int(os.getenv("BOLKE_STT_LIMIT_PER_MINUTE", "8")))
    content = await audio_file.read(MAX_AUDIO_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The recording is empty.")
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio must be 12 MB or smaller.")
    suffix = Path(audio_file.filename or "recording.wav").suffix.lower()
    if suffix not in {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"}:
        raise HTTPException(
            status_code=415,
            detail=f"Please use a WAV, MP3, OGG, FLAC, AAC or M4A recording. This file type is not supported. You can type your complaint instead.",
        )

    # Prisma v3.0's documented Auto-LID contract is language_code=indic-auto
    # together with model=prisma-v3.0. A locale list without the model selector
    # can silently fall back to older behavior and make users pin a language.
    configured_model = os.getenv("GNANI_STT_MODEL", "prisma-v3.0").strip() or "prisma-v3.0"
    provider_model = "prisma-v3.0" if auto_mode else configured_model
    provider_language = "indic-auto" if auto_mode else requested_language
    request_id = "bk-" + uuid.uuid4().hex[:20]
    files = {"audio_file": (Path(audio_file.filename or "recording.wav").name, content, audio_file.content_type or "audio/wav")}
    # Code-mix mode keeps English words in Latin script when people switch between
    # English and Indian languages. Prisma v2.5 continues to receive transcribe.
    output_format = "codemix" if provider_model == "prisma-v3.0" else "transcribe"
    data = {"language_code": provider_language, "model": provider_model, "format": output_format}
    headers = {"X-API-Key-ID": key, "X-API-Request-ID": request_id}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(50.0, connect=10.0)) as client:
            resp = await client.post(
                "https://api.vachana.ai/stt/v3",
                headers=headers,
                data=data,
                files=files,
            )
    except httpx.RequestError as exc:
        logger.warning("Gnani STT connection failed request_id=%s error=%s", request_id, type(exc).__name__)
        raise HTTPException(status_code=502, detail="We couldn't process that recording right now. Please retry or type your complaint instead.")

    if resp.status_code >= 400:
        provider_payload = {}
        try:
            raw_payload = resp.json()
            if isinstance(raw_payload, dict):
                provider_payload = raw_payload
        except (ValueError, json.JSONDecodeError):
            provider_payload = {}
        error_obj = provider_payload.get("error", {})
        if isinstance(error_obj, dict):
            provider_error_type = str(error_obj.get("type", "") or error_obj.get("code", "")).upper()
            provider_message = str(error_obj.get("message", "") or "")
        else:
            provider_error_type = str(error_obj).upper()
            provider_message = str(provider_payload.get("message", "") or "")
        # Only log a short, scrubbed message; do not print headers, credentials or the raw response.
        provider_message = re.sub(r"(?i)(api[_ -]?key|authorization|bearer|token)\s*[:=]?\s*[^ ,;]+", r"\1=[redacted]", provider_message)
        provider_message = re.sub(r"[\r\n\t]+", " ", provider_message).strip()[:180]
        logger.warning(
            "Gnani STT rejected request_id=%s status=%s error_type=%s message=%s language_mode=%s",
            request_id, resp.status_code, provider_error_type[:60], provider_message, "auto" if auto_mode else requested_language,
        )
        if resp.status_code == 429:
            detail = "Voice input is busy right now. Wait a moment, then try again or type your complaint."
        elif resp.status_code in {401, 403}:
            detail = "Voice input is temporarily unavailable. You can continue by typing your complaint."
        elif resp.status_code >= 500:
            detail = "Voice input is having a temporary problem. Please retry or type your complaint instead."
        elif auto_mode and ("LANGUAGE" in provider_error_type or "language" in provider_message.lower() or "MODEL" in provider_error_type):
            detail = "Automatic speech-language detection is unavailable for this API key/model. Enable Prisma v3.0 access, then retry. Your recording is still available; you can also choose a language temporarily or type your complaint."
        else:
            # Provider response detail is logged for debugging but never shown to end users.
            detail = "We couldn't get clear words from that recording. Try again, choose a language, or type your complaint instead."
        raise HTTPException(status_code=502, detail=detail)

    try:
        payload = resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="We couldn't process that recording. Please retry or type your complaint instead.")

    # If the auto-detected text strongly resembles English rendered phonetically in
    # Devanagari, retry once with a pinned English hint. Keep the same Prisma model.
    retry_language = None
    first_transcript = str(payload.get("transcript") or "")
    if auto_mode and payload.get("success", False) and first_transcript and looks_like_english_rendered_in_devanagari(first_transcript):
        retry_language = "en-IN"
    elif requested_language == "mr-IN" and payload.get("success", False) and first_transcript and looks_like_hindi_mislabelled_as_marathi(first_transcript):
        retry_language = "hi-IN"
    if retry_language:
        try:
            retry_files = {"audio_file": (Path(audio_file.filename or "recording.wav").name, content, audio_file.content_type or "audio/wav")}
            async with httpx.AsyncClient(timeout=httpx.Timeout(50.0, connect=10.0)) as retry_client:
                retry_resp = await retry_client.post(
                    "https://api.vachana.ai/stt/v3",
                    headers={"X-API-Key-ID": key, "X-API-Request-ID": request_id + "-retry"},
                    data={"language_code": retry_language, "model": provider_model, "format": output_format},
                    files=retry_files,
                )
            if retry_resp.status_code == 200:
                retry_payload = retry_resp.json()
                if retry_payload.get("success", False) and retry_payload.get("transcript"):
                    payload = retry_payload
                    provider_language = retry_language
        except (httpx.RequestError, ValueError, json.JSONDecodeError):
            # Keep the first valid transcript. A retry is opportunistic, never required.
            pass

    if not payload.get("success", False) or not payload.get("transcript"):
        error_type = str(payload.get("error", {}).get("type", "")).upper() if isinstance(payload.get("error"), dict) else ""
        if "RATE_LIMIT" in error_type:
            detail = "Voice input is busy right now. Wait a moment, then try again or type your complaint."
        elif "INVALID_REQUEST" in error_type:
            detail = "We couldn't process that recording. Try a clear clip up to 60 seconds long, or type your complaint instead."
        else:
            detail = "We couldn't hear enough to transcribe that clip. Try again in a quieter place, or type your complaint instead."
        raise HTTPException(status_code=502, detail=detail)

    raw_transcript = str(payload["transcript"])
    if looks_like_english_rendered_in_devanagari(raw_transcript):
        raw_transcript = transliterate_english_phonetics(raw_transcript)
    scrubbed = scrub_sensitive_text(raw_transcript)
    extracted_facts = extract_case_facts(scrubbed.text)
    # Keep the public response independent of the upstream speech vendor. Provider
    # diagnostics remain in sanitized server logs, while the browser receives only
    # the transcript, suggestions, and data needed for its workflow.
    return {
        "transcript": scrubbed.text,
        "redacted_types": scrubbed.redacted_types,
        "extracted_facts": extracted_facts,
        "detected_language_code": str(payload.get("detected_language_code") or "")[:15],
        "note": "Your words are ready. Review the transcript and suggested details before saving.",
    }


@app.post("/api/voice/speak")
async def speak_text(payload: SpeakRequest, http_request: Request):
    """Speak guidance in the language of the supplied text using the configured Timbre model."""
    tts_model = os.getenv("GNANI_TTS_MODEL", "timbre-v2.5").strip() or "timbre-v2.5"
    language_code = payload.language_code
    if tts_model == "timbre-v3.0":
        if language_code not in LANGUAGES:
            # Hinglish uses the dedicated v2.5 Poorvi voice; v3.0 exposes the ten Indic locales.
            if language_code == "hi-en":
                tts_model = "timbre-v2.5"
            else:
                raise HTTPException(status_code=400, detail="Choose one of the supported Indian languages for Timbre v3.0.")
        else:
            voice = payload.voice.strip() or os.getenv("GNANI_TTS_V3_VOICE", "Chetana").strip() or "Chetana"
            if voice not in {"Shivani", "Lakshmi", "Kalpana", "Chetana", "Vasudha", "Riyaa", "Tarika", "Avinash", "Shubham", "Prakash", "Devansh", "Yashraj", "Harshad"}:
                raise HTTPException(status_code=400, detail="Choose a supported Timbre v3.0 voice.")
    if tts_model == "timbre-v2.5":
        if language_code not in TTS_VOICES_BY_LANGUAGE:
            raise HTTPException(status_code=400, detail="Choose a supported text-to-speech language code, including hi-en for Hinglish.")
        voice = payload.voice.strip() or TTS_DEFAULT_VOICE[language_code]
        if voice not in TTS_VOICES_BY_LANGUAGE[language_code]:
            raise HTTPException(status_code=400, detail=f"Voice {voice!r} is not in the Timbre v2.5 catalog for {language_code}.")
    key = check_gnani_key()
    enforce_voice_rate_limit(http_request, "tts", int(os.getenv("BOLKE_TTS_LIMIT_PER_MINUTE", "20")))
    safe_speech_text = scrub_sensitive_text(payload.text).text
    provider_payload = {
        "text": safe_speech_text,
        "voice": voice,
        "model": tts_model,
        "language": language_code,
        "speed": 1.0,
        "audio_config": {
            "encoding": "linear_pcm",
            "container": "wav",
            "num_channels": 1,
            "sample_rate": 48000,
            "sample_width": 2,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(50.0, connect=10.0)) as client:
            resp = await client.post(
                "https://api.vachana.ai/api/v1/tts/inference",
                headers={"X-API-Key-ID": key, "Content-Type": "application/json"},
                json=provider_payload,
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Read-aloud is temporarily unavailable. You can still read or copy the message.") from exc
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail="Read-aloud is temporarily unavailable. You can still read or copy the message.")
    content_type = resp.headers.get("content-type", "audio/wav")
    if "json" in content_type.lower() or not resp.content:
        raise HTTPException(status_code=502, detail="Read-aloud could not be prepared. You can still read or copy the message.")
    return Response(content=resp.content, media_type="audio/wav", headers={"Cache-Control": "no-store"})


@app.post("/api/extraction/preview")
def preview_extraction(request: ExtractPreviewRequest, http_request: Request):
    """Extract reviewable suggestions from typed or transcribed text, without saving a case.

    This endpoint is public by design so visitors can get a first result before registration.
    """
    if AUTH_REQUIRED:
        enforce_public_preview_rate_limit(http_request, "extraction-preview", int(os.getenv("BOLKE_PUBLIC_PREVIEW_LIMIT_PER_MINUTE", "25")))
    safe_description = scrub_sensitive_text(request.description.strip())
    facts = extract_case_facts(safe_description.text)
    return {
        "extracted_facts": facts,
        "redacted_types": sorted(set(safe_description.redacted_types)),
        "notice": "Suggestions are based on your words. Review them before saving.",
    }


@app.post("/api/resolution/preview")
def preview_resolution(request: ResolutionPreviewRequest, http_request: Request):
    """Return a deterministic, cited next-step plan before the user saves a case.

    Anonymous previews are allowed; persisting or viewing a private case still requires auth
    whenever production authentication is enabled.
    """
    if AUTH_REQUIRED:
        enforce_public_preview_rate_limit(http_request, "resolution-preview", int(os.getenv("BOLKE_PUBLIC_PREVIEW_LIMIT_PER_MINUTE", "25")))
    validate_payment_date(request.payment_date)
    safe_description = scrub_sensitive_text(request.description)
    safe_merchant = scrub_sensitive_text(request.merchant)
    safe_issue_type = scrub_sensitive_text(request.issue_type)
    redacted_types = sorted(set(safe_description.redacted_types + safe_merchant.redacted_types + safe_issue_type.redacted_types))
    result = build_resolution(
        issue_type=safe_issue_type.text, description=safe_description.text, merchant=safe_merchant.text,
        amount=request.amount, payment_date=request.payment_date, payment_status=request.payment_status,
        contacted_support=request.contacted_support,
    )
    result = add_support_context(result, safe_merchant.text, safe_description.text, request.amount)
    if redacted_types:
        result["privacy_notice"] = {
            "redacted_types": redacted_types,
            "message": "The preview redacted some patterns that looked like sensitive credentials or identifiers. Review your original text before saving; this scrubber is a safety net, not a guarantee.",
        }
    return result


@app.get("/api/cases")
def list_cases():
    with get_db() as con:
        user_id = CURRENT_USER_ID.get()
        if user_id:
            rows = con.execute(
                "SELECT case_id, created_at, updated_at, issue_type, merchant, amount, payment_date, language_code, status, case_stage, resolution_json FROM cases WHERE owner_id = ? ORDER BY created_at DESC LIMIT 500",
                (user_id,),
            ).fetchall()
        elif AUTH_REQUIRED:
            raise HTTPException(status_code=401, detail="Please sign in to access your private cases.")
        else:
            rows = con.execute(
                "SELECT case_id, created_at, updated_at, issue_type, merchant, amount, payment_date, language_code, status, case_stage, resolution_json FROM cases WHERE owner_id IS NULL ORDER BY created_at DESC LIMIT 500"
            ).fetchall()
        result = []
        for r in rows:
            item = dict(r)
            raw_resolution = item.pop("resolution_json", "") or "{}"
            try:
                resolution = json.loads(raw_resolution)
            except (TypeError, json.JSONDecodeError):
                resolution = {}
            adaptive = resolution.get("adaptive_workflow", {}) if isinstance(resolution, dict) else {}
            current_step = adaptive.get("current_step") if isinstance(adaptive, dict) else None
            if not isinstance(current_step, dict):
                steps = resolution.get("recommended_steps", []) if isinstance(resolution, dict) else []
                current_step = steps[0] if isinstance(steps, list) and steps and isinstance(steps[0], dict) else {}
            item["next_action"] = str((current_step or {}).get("title") or (current_step or {}).get("action") or "Review case details")[:180]
            followup = con.execute("SELECT due_date, completed FROM case_followups WHERE case_id=?", (item["case_id"],)).fetchone()
            item["follow_up_due"] = str(followup["due_date"] or "") if followup and not bool(followup["completed"]) else ""
            item["evidence_count"] = con.execute("SELECT COUNT(*) FROM evidence WHERE case_id = ?", (item["case_id"],)).fetchone()[0]
            result.append(item)
        return result


@app.post("/api/cases", status_code=201)
def create_case(request: CaseCreate):
    validate_payment_date(request.payment_date)
    if request.language_code not in LANGUAGES:
        raise HTTPException(status_code=400, detail="Choose a supported language code.")
    case_id = safe_case_id()
    created = now_iso()
    with get_db() as con:
        safe_description = scrub_sensitive_text(request.description.strip())
        safe_merchant = scrub_sensitive_text(request.merchant.strip())
        safe_issue_type = scrub_sensitive_text(request.issue_type.strip())
        redaction_types = sorted(set(safe_description.redacted_types + safe_merchant.redacted_types + safe_issue_type.redacted_types))
        resolution = build_resolution(
            issue_type=safe_issue_type.text, description=safe_description.text,
            merchant=safe_merchant.text, amount=request.amount, payment_date=request.payment_date.strip(),
            payment_status=request.payment_status.strip(), contacted_support=request.contacted_support,
        )
        resolution = add_support_context(resolution, safe_merchant.text, safe_description.text, request.amount)
        classification = resolution.get("classification", {})
        saved_issue_type = classification.get("issue_type") if classification.get("confidence") in {"high", "medium"} else safe_issue_type.text
        if redaction_types:
            resolution["privacy_notice"] = {
                "redacted_types": redaction_types,
                "message": "Sensitive-looking values were redacted before this case was stored. Please review the saved description for accuracy.",
            }
        con.execute(
            "INSERT INTO cases (case_id, owner_id, created_at, updated_at, issue_type, merchant, amount, payment_date, language_code, description, status, case_stage, payment_status, contacted_support, resolution_json, redaction_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                case_id, CURRENT_USER_ID.get(), created, created, saved_issue_type, safe_merchant.text,
                request.amount, request.payment_date.strip(), request.language_code, safe_description.text,
                "Received", "Needs next step", request.payment_status.strip(),
                None if request.contacted_support is None else int(request.contacted_support),
                json.dumps(resolution, ensure_ascii=False), json.dumps(redaction_types),
            ),
        )
        con.execute(
            "INSERT INTO timeline (event_id, case_id, event_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, case_id, "created", "Case created from details supplied by the user. No payment source has been checked.", created),
        )
        con.execute(
            "INSERT INTO timeline (event_id, case_id, event_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, case_id, "notice", "A first-pass resolution plan was generated from official-source playbooks. Please review the suggested steps and linked sources; no transaction was verified.", created),
        )
        record_product_quality_event(con, "case_created", case_id=case_id, issue_family=str(classification.get("issue_family") or ""), channel="web")
        record_case_fact_snapshot(con, case_id, {
            "merchant": safe_merchant.text, "amount": request.amount, "issue_type": saved_issue_type,
            "payment_status": request.payment_status, "payment_date": request.payment_date.strip(),
        }, source_type="case_form", source_excerpt=safe_description.text, confidence="user_entered")
        if redaction_types:
            con.execute(
                "INSERT INTO timeline (event_id, case_id, event_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
                (uuid.uuid4().hex, case_id, "privacy", "Sensitive-looking text was redacted before storage: " + ", ".join(redaction_types) + ". This automated scrubber is a safety net, not a guarantee.", created),
            )
        return case_bundle(con, case_id)


@app.put("/api/cases/{case_id}")
def update_case_details(case_id: str, request: CaseDetailsUpdate):
    """Save corrected user facts and recalculate resolution guidance from the edited story."""
    normalized_id = case_id.upper()
    validate_payment_date(request.payment_date)
    if request.language_code not in LANGUAGES:
        raise HTTPException(status_code=400, detail="Choose a supported language code.")
    with get_db() as con:
        existing = require_case_access(con, normalized_id)
        clean_description = scrub_sensitive_text(request.description.strip())
        clean_merchant = scrub_sensitive_text(request.merchant.strip())
        clean_issue = scrub_sensitive_text(request.issue_type.strip())
        redaction_types = sorted(set(clean_description.redacted_types + clean_merchant.redacted_types + clean_issue.redacted_types))
        resolution = build_resolution(
            issue_type=clean_issue.text, description=clean_description.text,
            merchant=clean_merchant.text, amount=request.amount, payment_date=request.payment_date.strip(),
            payment_status=request.payment_status, contacted_support=request.contacted_support,
        )
        resolution = add_support_context(resolution, clean_merchant.text, clean_description.text, request.amount)
        classification = resolution.get("classification", {})
        saved_issue_type = classification.get("issue_type") if classification.get("confidence") in {"high", "medium"} else clean_issue.text
        created = now_iso()
        con.execute(
            "UPDATE cases SET updated_at=?, issue_type=?, merchant=?, amount=?, payment_date=?, language_code=?, description=?, payment_status=?, contacted_support=?, resolution_json=?, redaction_json=? WHERE case_id=?",
            (created, saved_issue_type, clean_merchant.text, request.amount, request.payment_date.strip(), request.language_code,
             clean_description.text, request.payment_status,
             None if request.contacted_support is None else int(request.contacted_support),
             json.dumps(resolution, ensure_ascii=False), json.dumps(redaction_types), normalized_id),
        )
        con.execute(
            "INSERT INTO timeline (event_id, case_id, event_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, normalized_id, "details_updated", "Case details were updated by the user; guided steps were recalculated from those user-reported details.", created),
        )
        return case_bundle(con, normalized_id)


@app.post("/api/cases/{case_id}/refresh-guidance")
def refresh_case_guidance(case_id: str):
    """Reclassify an existing case with the current rules and refresh its source-backed plan."""
    normalized_id = case_id.upper()
    with get_db() as con:
        row = require_case_access(con, normalized_id)
        resolution = build_resolution(
            issue_type=row["issue_type"], description=row["description"], merchant=row["merchant"],
            amount=row["amount"], payment_date=row["payment_date"], payment_status=row["payment_status"],
            contacted_support=None if row["contacted_support"] is None else bool(row["contacted_support"]),
        )
        resolution = add_support_context(resolution, str(row["merchant"] or ""), str(row["description"] or ""), row["amount"])
        classification = resolution.get("classification", {})
        issue_type = classification.get("issue_type") if classification.get("confidence") in {"high", "medium"} else row["issue_type"]
        created = now_iso()
        con.execute(
            "UPDATE cases SET updated_at=?, issue_type=?, resolution_json=? WHERE case_id=?",
            (created, issue_type, json.dumps(resolution, ensure_ascii=False), normalized_id),
        )
        con.execute(
            "INSERT INTO timeline (event_id, case_id, event_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, normalized_id, "guidance_refreshed", "Guidance was refreshed using the details currently saved in this case. No bank, payment network or merchant records were checked.", created),
        )
        return case_bundle(con, normalized_id)


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: str):
    """Delete one case and its evidence; private in production mode through owner checks."""
    normalized_id = case_id.upper()
    with get_db() as con:
        require_case_access(con, normalized_id)
        stored_files = [row["stored_name"] for row in con.execute(
            "SELECT stored_name FROM evidence WHERE case_id = ?", (normalized_id,)
        ).fetchall()]
        con.execute("DELETE FROM cases WHERE case_id = ?", (normalized_id,))
    # Delete files only after the database transaction commits. Names are generated by
    # the server; basename enforcement provides defence in depth against path traversal.
    for name in stored_files:
        safe_name = Path(name).name
        if safe_name == name and safe_name not in {"", ".", ".."}:
            try:
                (UPLOAD_DIR / safe_name).unlink(missing_ok=True)
            except OSError:
                # Orphan cleanup can be handled by a scheduled maintenance task; never
                # make the already-committed case deletion appear to have failed.
                pass
    return {"ok": True, "case_id": normalized_id, "deleted": True}


@app.post("/api/cases/{case_id}/commitments/preview")
def preview_case_commitment(case_id: str, request: CommitmentPreviewRequest):
    """Preview a possible conditional commitment without persisting transcript or audio."""
    normalized_id = case_id.upper()
    with get_db() as con:
        require_case_access(con, normalized_id)
    preview = extract_commitment_candidate(request.text, request.source_type)
    return preview


@app.post("/api/cases/{case_id}/commitments/confirm", status_code=201)
def confirm_case_commitment(case_id: str, request: CommitmentConfirmRequest):
    """Persist only a candidate the user explicitly reviewed and confirmed."""
    if not request.confirmed:
        raise HTTPException(status_code=400, detail="Review the fields and confirm them before saving this commitment.")
    normalized_id = case_id.upper()
    if request.statement_date:
        validate_payment_date(request.statement_date)
    if request.duration_value is not None and request.duration_max_value is not None and request.duration_max_value < request.duration_value:
        raise HTTPException(status_code=422, detail="The maximum duration cannot be shorter than the minimum duration.")
    if request.trigger_type == "condition_met" and not request.condition_text.strip():
        raise HTTPException(status_code=422, detail="Add the condition that must happen before this clock starts, or choose a different start rule.")
    if request.condition_text.strip() and request.trigger_type == "statement_date":
        raise HTTPException(status_code=422, detail="This statement includes a prerequisite, so it cannot be timed from the statement date unless you remove that condition after reviewing the original wording.")
    if request.trigger_type == "statement_date" and not request.statement_date:
        raise HTTPException(status_code=422, detail="Add the statement date before using it as the clock start.")
    safe_excerpt_result = scrub_sensitive_text(request.source_excerpt.strip())
    safe_excerpt = safe_excerpt_result.text[:1200]
    if len(safe_excerpt) < 8:
        raise HTTPException(status_code=422, detail="The source statement is too short after sensitive-looking values were redacted. Review it and try again.")
    if request.source_evidence_id:
        with get_db() as con:
            evidence = con.execute(
                "SELECT evidence_id FROM evidence WHERE evidence_id=? AND case_id=?",
                (request.source_evidence_id, normalized_id),
            ).fetchone()
            if not evidence:
                raise HTTPException(status_code=404, detail="The selected evidence file was not found in this case.")
    created = now_iso()
    commitment_id = "CM-" + uuid.uuid4().hex[:12].upper()
    source_label = request.source_label.strip() or {
        "support_call_transcript": "User-reviewed support-call transcript",
        "support_email": "User-reviewed support email excerpt",
        "chat_message": "User-reviewed chat message excerpt",
        "user_note": "User-entered statement note",
        "case_evidence": "User-reviewed statement linked to case evidence",
    }[request.source_type]
    with get_db() as con:
        require_case_access(con, normalized_id)
        con.execute(
            "INSERT INTO case_commitments (commitment_id, case_id, source_type, source_label, source_excerpt_redacted, source_hash, source_evidence_id, source_authenticity_verified, speech_act, action_code, action_text, amount_minor_units, currency, condition_text, trigger_type, duration_value, duration_max_value, duration_unit, day_type, qualifier, statement_date, review_state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'user_confirmed', ?, ?)",
            (commitment_id, normalized_id, request.source_type, source_label, safe_excerpt,
             commitment_source_hash(safe_excerpt), request.source_evidence_id or None, request.speech_act,
             request.action_code, scrub_sensitive_text(request.action_text.strip()).text[:200],
             request.amount_minor_units, request.currency, scrub_sensitive_text(request.condition_text.strip()).text[:300],
             request.trigger_type, request.duration_value, request.duration_max_value, request.duration_unit,
             request.day_type, request.qualifier.strip()[:50], request.statement_date, created, created),
        )
        first_event_id = uuid.uuid4().hex
        con.execute(
            "INSERT INTO commitment_events (event_id, commitment_id, case_id, event_type, source_type, evidence_id, source_excerpt_redacted, relation, evidence_status, event_date_claimed, event_date_confirmed, details_json, created_at, reviewed_by_user_at) VALUES (?, ?, ?, 'commitment_confirmed', ?, ?, '', 'supports', 'user_confirmed', ?, '', ?, ?, ?)",
            (first_event_id, commitment_id, normalized_id, request.source_type, request.source_evidence_id or None,
             request.statement_date, json.dumps({"initial_confirmation": True, "source_authenticity_verified": False}, ensure_ascii=False), created, created),
        )
        con.execute("UPDATE cases SET updated_at=? WHERE case_id=?", (created, normalized_id))
        record_case_event(con, normalized_id, "commitment_recorded", "A statement was reviewed and added to the commitment record. Its source has not been independently verified.", created, actor="user", metadata={"commitment_id": commitment_id, "source_type": request.source_type})
        case = case_bundle(con, normalized_id)
        return next(item for item in case["commitments"] if item["commitment_id"] == commitment_id)


@app.post("/api/cases/{case_id}/commitments/{commitment_id}/reconcile", status_code=201)
def reconcile_case_commitment(case_id: str, commitment_id: str, request: CommitmentReconcileRequest):
    """Append a user-reviewed update and recalculate the commitment state without overwriting history."""
    normalized_id = case_id.upper()
    if request.event_date_claimed:
        validate_payment_date(request.event_date_claimed)
    if request.event_date_confirmed:
        validate_payment_date(request.event_date_confirmed)
        if request.relation == "triggers":
            confirmed_day = date.fromisoformat(request.event_date_confirmed)
            today_local = datetime.now(ZoneInfo("Asia/Kolkata")).date()
            if confirmed_day > today_local:
                raise HTTPException(status_code=422, detail="A condition occurrence date cannot be in the future. Add an expected date as a note instead.")
    safe_text = scrub_sensitive_text(request.event_text.strip()).text[:900]
    if len(safe_text) < 3:
        raise HTTPException(status_code=422, detail="The update is too short after sensitive-looking values were redacted.")
    created = now_iso()
    event_id = uuid.uuid4().hex
    with get_db() as con:
        require_case_access(con, normalized_id)
        commitment = con.execute(
            "SELECT commitment_id FROM case_commitments WHERE commitment_id=? AND case_id=?",
            (commitment_id, normalized_id),
        ).fetchone()
        if not commitment:
            raise HTTPException(status_code=404, detail="Commitment not found in this case.")
        evidence_id = request.evidence_id.strip()
        if evidence_id:
            evidence = con.execute("SELECT evidence_id FROM evidence WHERE evidence_id=? AND case_id=?", (evidence_id, normalized_id)).fetchone()
            if not evidence:
                raise HTTPException(status_code=404, detail="The selected evidence file was not found in this case.")
        evidence_status = "document_reviewed_by_user" if evidence_id else request.evidence_status
        if request.relation == "triggers" and not request.event_date_confirmed:
            # Keep the event, but do not start a date-based clock until the user can
            # identify the occurrence date. The evaluator will continue to show unknown.
            details = {"trigger_date_missing": True, "note": "Condition reported as met, but no confirmed trigger date was supplied."}
        else:
            details = {}
        details.update({"source_authenticity_verified": False, "external_status_checked": False})
        con.execute(
            "INSERT INTO commitment_events (event_id, commitment_id, case_id, event_type, source_type, evidence_id, source_excerpt_redacted, relation, evidence_status, event_date_claimed, event_date_confirmed, details_json, created_at, reviewed_by_user_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, commitment_id, normalized_id, "commitment_update", "case_evidence" if evidence_id else "user_update", evidence_id or None,
             safe_text, request.relation, evidence_status, request.event_date_claimed, request.event_date_confirmed,
             json.dumps(details, ensure_ascii=False), created, created),
        )
        con.execute("UPDATE case_commitments SET updated_at=? WHERE commitment_id=? AND case_id=?", (created, commitment_id, normalized_id))
        con.execute("UPDATE cases SET updated_at=? WHERE case_id=?", (created, normalized_id))
        record_case_event(con, normalized_id, "commitment_update_recorded", f"A user-reviewed update was linked to a commitment ({request.relation}). The source and claims are not independently verified.", created, actor="user", metadata={"commitment_id": commitment_id, "event_id": event_id, "relation": request.relation})
        case = case_bundle(con, normalized_id)
        return next(item for item in case["commitments"] if item["commitment_id"] == commitment_id)


@app.delete("/api/cases/{case_id}/commitments/{commitment_id}")
def delete_case_commitment(case_id: str, commitment_id: str):
    """Remove a commitment and its attached event history from the active case record."""
    normalized_id = case_id.upper()
    with get_db() as con:
        require_case_access(con, normalized_id)
        cursor = con.execute("DELETE FROM case_commitments WHERE commitment_id=? AND case_id=?", (commitment_id, normalized_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Commitment not found in this case.")
        con.execute("UPDATE cases SET updated_at=? WHERE case_id=?", (now_iso(), normalized_id))
    return {"ok": True, "commitment_id": commitment_id, "deleted": True}


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    with get_db() as con:
        return case_bundle(con, case_id.upper())


@app.get("/api/cases/{case_id}/action-pack")
def get_case_action_pack(case_id: str):
    with get_db() as con:
        case = case_bundle(con, case_id.upper())
        return case["action_pack"]


@app.get("/api/cases/{case_id}/passport.json")
def download_resolution_passport_json(case_id: str):
    """Download a portable structured copy of the current user-controlled case record."""
    normalized_id = case_id.upper()
    with get_db() as con:
        case = case_bundle(con, normalized_id)
        payload = build_passport_export(case)
    safe_id = re.sub(r"[^A-Z0-9_-]", "", normalized_id)[:40] or "CASE"
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f"attachment; filename=\"BolKeResolve-{safe_id}-passport.json\""},
    )


@app.get("/api/cases/{case_id}/passport/print", response_class=HTMLResponse)
def print_resolution_passport(case_id: str):
    """Open a self-contained print view that users can print or save as PDF."""
    with get_db() as con:
        case = case_bundle(con, case_id.upper())
        markup = render_printable_passport(case)
    return HTMLResponse(markup, headers={"Cache-Control": "no-store, max-age=0"})


@app.put("/api/cases/{case_id}/outcome")
def update_case_outcome(case_id: str, request: CaseOutcomeUpdate):
    """Record the latest user-reported outcome; never implies outside verification."""
    normalized_id = case_id.upper()
    details_clean = scrub_sensitive_text(request.details.strip())
    reference_clean = scrub_sensitive_text(request.reference.strip())
    details = details_clean.text[:1000]
    reference = reference_clean.text[:120]
    stamp = now_iso()
    labels = {
        "still_pending": "Still pending",
        "no_response": "No response",
        "partially_resolved": "Partially resolved",
        "resolved": "Resolved (user-reported)",
        "stopped": "Stopped pursuing for now",
    }
    with get_db() as con:
        require_case_access(con, normalized_id)
        previous = con.execute("SELECT created_at FROM case_outcomes WHERE case_id = ?", (normalized_id,)).fetchone()
        created = previous["created_at"] if previous else stamp
        con.execute(
            "INSERT INTO case_outcomes (case_id, outcome_code, details, reference, provenance, created_at, updated_at) VALUES (?, ?, ?, ?, 'user_reported', ?, ?) "
            "ON CONFLICT(case_id) DO UPDATE SET outcome_code=excluded.outcome_code, details=excluded.details, reference=excluded.reference, provenance='user_reported', updated_at=excluded.updated_at",
            (normalized_id, request.outcome_code, details, reference, created, stamp),
        )
        # Progress is separate from the reported outcome, but a resolution report should
        # be reflected in the journey rail. Other outcomes move the case to the next
        # useful stage without ever implying an external status check.
        stage_by_outcome = {
            "still_pending": "Awaiting response",
            "no_response": "Follow-up needed",
            "partially_resolved": "Follow-up needed",
            "resolved": "Resolved (user-reported)",
        }
        new_stage = stage_by_outcome.get(request.outcome_code)
        if new_stage:
            con.execute("UPDATE cases SET case_stage = ?, updated_at = ? WHERE case_id = ?", (new_stage, stamp, normalized_id))
        else:
            con.execute("UPDATE cases SET updated_at = ? WHERE case_id = ?", (stamp, normalized_id))
        message = f"The user recorded the outcome as: {labels[request.outcome_code]}. This is user-reported and has not been independently verified."
        if details:
            message += " Details: " + details
        metadata = {"user_reported": True, "outcome_code": request.outcome_code}
        if reference:
            metadata["reference_provided"] = reference
        redacted = sorted(set(details_clean.redacted_types + reference_clean.redacted_types))
        if redacted:
            metadata["redacted_categories"] = redacted
        record_case_event(con, normalized_id, "outcome_updated", message, stamp, actor="user", channel="web", source="user_action", metadata=metadata)
        record_product_quality_event(con, "outcome_reported", case_id=normalized_id, channel="web")
        return case_bundle(con, normalized_id)


@app.patch("/api/cases/{case_id}/checklist/{task_key}")
def update_checklist_item(case_id: str, task_key: str, request: ChecklistItemUpdate):
    normalized_id = case_id.upper()
    if task_key not in ALL_CHECKLIST_KEYS:
        raise HTTPException(status_code=404, detail="Checklist item not found.")
    updated = now_iso()
    with get_db() as con:
        require_case_access(con, normalized_id)
        con.execute(
            "INSERT INTO case_checklist_state (case_id, task_key, checked, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(case_id, task_key) DO UPDATE SET checked=excluded.checked, updated_at=excluded.updated_at",
            (normalized_id, task_key, int(request.checked), updated),
        )
        con.execute("UPDATE cases SET updated_at = ? WHERE case_id = ?", (updated, normalized_id))
        return {"action_pack": case_bundle(con, normalized_id)["action_pack"]}


@app.post("/api/cases/{case_id}/reply-review/preview")
def preview_support_reply(case_id: str, request: ReplyReviewRequest):
    """Interpret pasted support text without writing the text or preview to the case database."""
    normalized_id = case_id.upper()
    with get_db() as con:
        require_case_access(con, normalized_id)
    safe_reply = scrub_sensitive_text(request.reply_text.strip())
    result = review_support_reply(safe_reply.text)
    result["privacy"] = {
        "raw_reply_saved": False,
        "redacted_categories": sorted(set(safe_reply.redacted_types)),
        "message": "This preview does not save the pasted reply. Only save a short interpretation to your timeline after reviewing it.",
    }
    return result


@app.post("/api/cases/{case_id}/reply-review/confirm", status_code=201)
def confirm_support_reply_review(case_id: str, request: ReplyReviewConfirmRequest):
    """Store a user-confirmed interpretation, never the raw reply text."""
    if not request.confirmed:
        raise HTTPException(status_code=400, detail="Confirm that you reviewed the original reply before saving its summary.")
    normalized_id = case_id.upper()
    safe_reply = scrub_sensitive_text(request.reply_text.strip())
    result = review_support_reply(safe_reply.text)
    safe_reference = scrub_sensitive_text(request.reference.strip()) if request.reference.strip() else None
    stamp = now_iso()
    message = (
        f"The user reviewed a support reply. First-pass category: {result['label']}. "
        f"Suggested next action: {result['next_step']} "
        "This interpretation was explicitly confirmed by the user; the original reply text was not saved by this review action and the organisation's status was not independently verified."
    )
    metadata = {
        "user_reported": True,
        "reply_review_category": result["category"],
        "reply_review_label": result["label"],
        "reply_review_engine": result["engine"],
        "reply_interpretation_confirmed": True,
        "raw_reply_retained": False,
    }
    if safe_reply.redacted_types:
        metadata["redacted_categories"] = sorted(set(safe_reply.redacted_types))
    if safe_reference and safe_reference.text:
        metadata["reference_provided"] = safe_reference.text[:120]
        if safe_reference.redacted_types:
            metadata["reference_redacted_categories"] = sorted(set(safe_reference.redacted_types))
        message += " A user-supplied reference was recorded privately."
    with get_db() as con:
        require_case_access(con, normalized_id)
        reply_stage = stage_for_reply_category(result["category"])
        con.execute("UPDATE cases SET case_stage = ?, updated_at = ? WHERE case_id = ?", (reply_stage, stamp, normalized_id))
        record_case_event(con, normalized_id, "response_received", message, stamp, actor="user", channel="web", source="user_confirmed_reply_review", metadata=metadata)
        return {"review": result, "case": case_bundle(con, normalized_id), "raw_reply_saved": False}


@app.post("/api/cases/{case_id}/events", status_code=201)
def add_case_event(case_id: str, request: CaseEventCreate):
    """Record a user-reported real-world action without claiming external verification."""
    normalized_id = case_id.upper()
    safe_details = scrub_sensitive_text(request.details.strip()) if request.details.strip() else None
    safe_reference = scrub_sensitive_text(request.reference.strip()) if request.reference.strip() else None
    stage_by_event = {
        "contacted_support": "Contacted support",
        "still_waiting": "Awaiting response",
        "submission_reported": "Awaiting response",
        "response_received": "Follow-up needed",
        "resolved": "Resolved (user-reported)",
        "not_resolved": "Follow-up needed",
        "official_channel_opened": "Needs next step",
    }
    messages = {
        "contacted_support": "You reported that you contacted the organisation's support team.",
        "still_waiting": "You reported that you are still waiting for a response.",
        "submission_reported": "You reported that you submitted a complaint through an external channel. BolKeResolve did not submit or verify it.",
        "response_received": "You reported receiving a response from the organisation.",
        "resolved": "You marked the issue resolved. This status is user-reported and has not been independently verified.",
        "not_resolved": "You reported that the issue is not resolved yet.",
        "official_channel_opened": "You reported opening an official support or grievance channel.",
    }
    event_message = messages[request.event_type]
    metadata = {"user_reported": True}
    if safe_details and safe_details.text:
        event_message += " Details: " + safe_details.text
        if safe_details.redacted_types:
            metadata["redacted_categories"] = safe_details.redacted_types
    if safe_reference and safe_reference.text:
        metadata["reference_provided"] = safe_reference.text[:120]
        event_message += " Reference recorded privately in the case timeline."
        if safe_reference.redacted_types:
            metadata["reference_redacted_categories"] = safe_reference.redacted_types
    stamp = now_iso()
    with get_db() as con:
        require_case_access(con, normalized_id)
        stage = stage_by_event[request.event_type]
        con.execute("UPDATE cases SET case_stage = ?, updated_at = ? WHERE case_id = ?", (stage, stamp, normalized_id))
        record_case_event(con, normalized_id, request.event_type, event_message, stamp, actor="user", channel="web", source="user_action", metadata=metadata)
        return case_bundle(con, normalized_id)


@app.post("/api/cases/{case_id}/whatsapp-link")
def create_whatsapp_link_token(case_id: str) -> dict:
    """Create a short-lived single-use pairing code for Meta or the Twilio sandbox."""
    normalized_id = case_id.upper()
    provider = messaging_service.selected_provider()
    common_config = whatsapp_service.config_status()
    if provider == "twilio":
        provider_config = twilio_service.config_status()
        if not provider_config["ready_for_sandbox_testing"] or not common_config["persistent_identity_ready"] or not common_config["privacy_policy_configured"] or not common_config["support_escalation_configured"]:
            raise HTTPException(status_code=503, detail="Twilio Sandbox linking needs its credentials, public HTTPS webhook, encrypted phone storage, privacy notice and support contact.")
        raw_sender = os.getenv("TWILIO_WHATSAPP_FROM", "").strip()
        number = whatsapp_service.normalise_phone(raw_sender[len("whatsapp:+"):] if raw_sender.startswith("whatsapp:+") else "")
        if not number:
            raise HTTPException(status_code=503, detail="The configured Twilio WhatsApp sender is invalid.")
        setup_hint = "Twilio Sandbox test link only; this is not a production number. Your phone must already have joined this exact Sandbox in the Twilio Console. If it has not, join first, then create a fresh case-link code because this code expires in 10 minutes."
    else:
        if not common_config["cloud_api_ready"]:
            raise HTTPException(status_code=503, detail="WhatsApp updates are not connected in this installation yet.")
        number = common_config["business_number"]
        setup_hint = "Send this one-time code only to the official BolKeResolve WhatsApp number. If asked to opt in first, send START, then resend the LINK code before it expires."
    with get_db() as con:
        row = require_case_access(con, normalized_id)
        owner_id = CURRENT_USER_ID.get() or row["owner_id"]
        # Invalidate unused codes for this case to avoid multiple active credentials.
        con.execute("UPDATE whatsapp_link_tokens SET consumed_at = ? WHERE case_id = ? AND consumed_at = ''", (now_iso(), normalized_id))
        token = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(8))
        stamp = int(time.time())
        con.execute(
            "INSERT INTO whatsapp_link_tokens (token_hash, case_id, owner_id, expires_at, created_at, consumed_at) VALUES (?, ?, ?, ?, ?, '')",
            (hashlib.sha256(token.encode("ascii")).hexdigest(), normalized_id, owner_id, stamp + 600, now_iso()),
        )
    whatsapp_url = f"https://wa.me/{number}?text={quote('LINK ' + token)}"
    return {"case_id": normalized_id, "code": token, "expires_in_seconds": 600, "whatsapp_url": whatsapp_url, "business_number": number, "provider": provider, "sandbox_join_required": provider == "twilio", "setup_hint": setup_hint}


@app.put("/api/cases/{case_id}/follow-up")
def update_case_followup(case_id: str, request: FollowupUpdate):
    normalized_id = case_id.upper()
    if request.due_date:
        validate_payment_date(request.due_date)
    safe_note = scrub_sensitive_text(request.note.strip())
    updated = now_iso()
    with get_db() as con:
        require_case_access(con, normalized_id)
        previous = con.execute("SELECT due_date, note, completed FROM case_followups WHERE case_id = ?", (normalized_id,)).fetchone()
        if not request.due_date and not safe_note.text and not request.completed:
            con.execute("DELETE FROM case_followups WHERE case_id = ?", (normalized_id,))
            event_text = "The follow-up date and note were cleared by the user."
            event_meta = {"cleared": True}
        else:
            existing = con.execute("SELECT created_at FROM case_followups WHERE case_id = ?", (normalized_id,)).fetchone()
            created = existing["created_at"] if existing else updated
            con.execute(
                "INSERT INTO case_followups (case_id, due_date, note, completed, created_at, updated_at, reminder_sent_for) VALUES (?, ?, ?, ?, ?, ?, '') "
                "ON CONFLICT(case_id) DO UPDATE SET due_date=excluded.due_date, note=excluded.note, completed=excluded.completed, updated_at=excluded.updated_at, reminder_sent_for=''",
                (normalized_id, request.due_date, safe_note.text, int(request.completed), created, updated),
            )
            if request.completed:
                event_text = "The user marked the follow-up complete."
            elif request.due_date:
                event_text = f"The user set a follow-up date for {request.due_date}."
            else:
                event_text = "The user updated the follow-up note."
            event_meta = {"due_date": request.due_date, "completed": request.completed}
            if safe_note.text:
                event_meta["note"] = safe_note.text
            if safe_note.redacted_types:
                event_meta["redacted_categories"] = safe_note.redacted_types
        con.execute("UPDATE cases SET updated_at = ? WHERE case_id = ?", (updated, normalized_id))
        record_case_event(con, normalized_id, "followup_updated", event_text, updated, actor="user", channel="web", source="user_action", metadata=event_meta)
        if request.due_date and not request.completed:
            record_product_quality_event(con, "followup_set", case_id=normalized_id, channel="web")
        return case_bundle(con, normalized_id)


def _live_room_ai_consent(con: sqlite3.Connection, case_id: str) -> bool:
    row = con.execute(
        "SELECT metadata_json FROM timeline WHERE case_id=? AND event_type='live_room_ai_consent' ORDER BY created_at DESC, rowid DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    if not row:
        return False
    try:
        metadata = json.loads(row["metadata_json"] or "{}")
    except (TypeError, json.JSONDecodeError):
        return False
    return bool(metadata.get("allowed"))


def _live_room_case_interpretation_consent(con: sqlite3.Connection, case_id: str) -> bool:
    row = con.execute(
        "SELECT metadata_json FROM timeline WHERE case_id=? AND event_type='live_room_case_ai_consent' ORDER BY created_at DESC, rowid DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    if not row:
        return False
    try:
        metadata = json.loads(row["metadata_json"] or "{}")
    except (TypeError, json.JSONDecodeError):
        return False
    return bool(metadata.get("allowed"))


def _confirmed_live_evidence_context(con: sqlite3.Connection, case_id: str) -> str:
    """Only user-confirmed visual observations may influence resolution routing."""
    rows = con.execute(
        "SELECT message, metadata_json FROM timeline WHERE case_id=? AND event_type='live_room_evidence_analysis_confirmed' ORDER BY created_at DESC, rowid DESC LIMIT 8",
        (case_id,),
    ).fetchall()
    parts: list[str] = []
    for row in reversed(rows):
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            metadata = {}
        fields = metadata.get("confirmed_fields", {}) if isinstance(metadata.get("confirmed_fields"), dict) else {}
        safe_fields = [f"{key}: {str(value)[:120]}" for key, value in fields.items() if value not in (None, "")]
        if safe_fields:
            parts.append("User-confirmed visual evidence candidates (not independently authenticated): " + "; ".join(safe_fields))
        # Model-generated summaries/observations are not routing facts. Only the
        # individual fields the user selected and confirmed below may influence a route.
    fact_rows = con.execute(
        "SELECT field_key, field_value_json FROM case_fact_sources WHERE case_id=? ORDER BY confirmed_at DESC LIMIT 24",
        (case_id,),
    ).fetchall()
    confirmed_fields: list[str] = []
    seen_fields: set[str] = set()
    for fact_row in fact_rows:
        field = str(fact_row["field_key"] or "")
        if not field or field in seen_fields:
            continue
        seen_fields.add(field)
        try:
            value = json.loads(fact_row["field_value_json"] or "null")
        except json.JSONDecodeError:
            continue
        if value not in (None, ""):
            confirmed_fields.append(f"{field}: {str(value)[:100]}")
    if confirmed_fields:
        parts.append("User-reviewed evidence facts (candidate, not independently authenticated): " + "; ".join(confirmed_fields))
    return "\n".join(parts)[-4000:]


def extract_live_room_reported_facts(text: str) -> dict:
    """Extract high-confidence facts explicitly stated in a live-room conversation.

    These values remain user-reported (not verified). We only promote exact merchant
    matches, currency-marked amounts, and unambiguous support-contact statements.
    """
    story = str(text or "")[:7000]
    lowered = story.casefold()
    facts: dict = {}

    # Merchant recognition is restricted to our curated support-directory aliases.
    destinations = find_support_destinations("", story, "")
    for destination in destinations:
        if destination.get("id") not in {
            "national_consumer_helpline", "npci_upi", "cybercrime_india", "rbi_ombudsman"
        }:
            facts["merchant"] = destination.get("name", "")
            facts["merchant_source"] = "matched in the user's own words to a curated organisation alias"
            break

    amount_match = re.search(r"(?:₹\s*|\bINR\s*|\bRs\.?\s*)([0-9][0-9,]*(?:\.\d{1,2})?)", story, re.I)
    if amount_match:
        try:
            amount = float(amount_match.group(1).replace(",", ""))
            if 0 <= amount <= 100_000_000:
                facts["amount"] = amount
                facts["amount_source"] = "currency-marked amount in the user's own words; review before sharing"
        except ValueError:
            pass

    explicit_not_contacted = re.search(
        r"\b(?:not yet contacted|haven't contacted|have not contacted|didn't contact|did not contact|not contacted)\b",
        lowered,
    )
    explicit_contacted = re.search(
        r"\b(?:already contacted|contacted (?:the )?(?:support|customer care|merchant|bank)|raised (?:a )?(?:ticket|complaint)|sent (?:a )?complaint|spoke (?:to|with) (?:support|customer care)|no response|no reply|haven't heard back|have not heard back)\b",
        lowered,
    )
    if explicit_not_contacted:
        facts["contacted_support"] = False
        facts["contacted_support_source"] = "explicitly reported not having contacted support"
    elif explicit_contacted:
        facts["contacted_support"] = True
        facts["contacted_support_source"] = "explicitly reported prior support contact or no response"

    elapsed = re.search(
        r"\b(?:about |around |approximately |nearly )?(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(days?|weeks?|months?)\s+ago\b",
        lowered,
    )
    if elapsed:
        facts["elapsed_time_reported"] = elapsed.group(0).strip()
    elif re.search(r"\bthree weeks\b", lowered):
        facts["elapsed_time_reported"] = "three weeks"
    if re.search(r"\bno response\b|\bno reply\b|\bhaven't heard back\b|\bhave not heard back\b", lowered):
        facts["support_response_reported"] = "No response reported by the user"
    return facts


@app.post("/api/live-room/cases", status_code=201)
def create_live_room_draft_case(request: LiveRoomDraftRequest):
    """Create a persistent draft before asking for camera/microphone permissions.

    Evidence can therefore be uploaded immediately, even before the first transcript.
    """
    speech_language_mode = "auto" if request.language_code == "indic-auto" else "pinned"
    if request.language_code not in {*LANGUAGES.keys(), "indic-auto"}:
        raise HTTPException(status_code=400, detail="Choose automatic detection or a supported language.")
    language_code = request.language_code if request.language_code in LANGUAGES else "en-IN"
    session_id = re.sub(r"[^A-Za-z0-9_-]", "", request.session_id)[:80]
    if len(session_id) < 8:
        raise HTTPException(status_code=400, detail="A valid live session identifier is required.")
    case_id = safe_case_id()
    created = now_iso()
    description = "Live resolution started. The user's issue description is being collected."
    issue_type = "Other payment issue"
    resolution = build_resolution(issue_type=issue_type, description=description, merchant="", amount=None, payment_date="", payment_status="unknown", contacted_support=None)
    resolution = add_support_context(resolution, "", description, None)
    resolution["adaptive_workflow"] = build_adaptive_workflow(description, intake_complete=False)
    with get_db() as con:
        con.execute(
            "INSERT INTO cases (case_id, owner_id, created_at, updated_at, issue_type, merchant, amount, payment_date, language_code, description, status, case_stage, payment_status, contacted_support, resolution_json, redaction_json) VALUES (?, ?, ?, ?, ?, '', NULL, '', ?, ?, 'Draft', 'Draft — collecting details', 'unknown', NULL, ?, '[]')",
            (case_id, CURRENT_USER_ID.get(), created, created, issue_type, language_code, description, json.dumps(resolution, ensure_ascii=False)),
        )
        record_case_event(
            con, case_id, "live_room_draft_created", "A draft case was created when the user started Live Resolution. Details are still being collected.", created,
            actor="user", channel="live_room", source="live_resolution_room", metadata={"session_id": session_id, "speech_language_mode": speech_language_mode, "provenance": "draft case created before media permissions; no issue details inferred"},
        )
        record_case_event(
            con, case_id, "live_room_session_started", "Live resolution session started.", created,
            actor="user", channel="live_room", source="live_resolution_room", metadata={"session_id": session_id, "started_at_client": request.started_at[:40], "provenance": "application session event; not an external payment event"},
        )
        record_case_event(
            con, case_id, "live_room_ai_consent",
            "The user allowed selected case text to be translated by the configured AI provider." if request.allow_ai_assistance else "The user did not enable optional external AI translation for this session.",
            created, actor="user", channel="live_room", source="privacy_consent",
            metadata={"session_id": session_id, "allowed": bool(request.allow_ai_assistance), "scope": "translation of generated guidance only; evidence images require a separate per-image consent"},
        )
        record_case_event(
            con, case_id, "live_room_case_ai_consent",
            "The user allowed the configured AI provider to interpret saved case text and personalize the next response." if request.allow_ai_case_interpretation else "The user did not enable external AI case interpretation for this session.",
            created, actor="user", channel="live_room", source="privacy_consent",
            metadata={"session_id": session_id, "allowed": bool(request.allow_ai_case_interpretation), "scope": "saved, redacted typed/transcribed case text and minimal case facts for semantic interpretation and response drafting; raw audio and images are not included; images require separate consent"},
        )
        result = case_bundle(con, case_id)
    result["live_session_id"] = session_id
    result["speech_language_mode"] = speech_language_mode
    return result


@app.post("/api/cases/{case_id}/live-room/case-ai-consent")
def update_live_room_case_ai_consent(case_id: str, request: LiveRoomCaseInterpretationConsentRequest):
    normalized_id = case_id.upper()
    stamp = now_iso()
    session_id = re.sub(r"[^A-Za-z0-9_-]", "", request.session_id)[:80]
    with get_db() as con:
        require_case_access(con, normalized_id)
        record_case_event(
            con, normalized_id, "live_room_case_ai_consent",
            "The user allowed the configured AI provider to interpret saved case text and personalize the next response." if request.allowed else "The user disabled external AI case interpretation for this case.",
            stamp, actor="user", channel="live_room", source="privacy_consent",
            metadata={"session_id": session_id, "allowed": bool(request.allowed), "scope": "saved, redacted typed/transcribed case text and minimal case facts for semantic interpretation and response drafting; raw audio and images are not included; images require separate consent"},
        )
        return {"case_id": normalized_id, "allowed": bool(request.allowed), "available": agent_assist.configured()}


def build_live_room_guidance(resolution: dict) -> str:
    """Return a short, action-led response grounded in the saved case and reviewed routes."""
    resolution = resolution if isinstance(resolution, dict) else {}
    steps = resolution.get("recommended_steps", [])
    steps = steps if isinstance(steps, list) else []
    first = steps[0] if steps and isinstance(steps[0], dict) else {}
    routes = resolution.get("support_destinations", [])
    routes = routes if isinstance(routes, list) else []
    route = routes[0] if routes and isinstance(routes[0], dict) else {}
    facts = resolution.get("reported_conversation_facts", {})
    facts = facts if isinstance(facts, dict) else {}
    classification = resolution.get("classification", {})
    classification = classification if isinstance(classification, dict) else {}
    issue = str(classification.get("issue_type") or "Your issue")
    merchant = str(facts.get("merchant") or route.get("name") or "")
    amount = facts.get("amount")
    amount_label = f"₹{amount:,.2f}".rstrip("0").rstrip(".") if isinstance(amount, (int, float)) else ""
    title = str(first.get("title") or "Review the information you have")
    detail = str(first.get("detail") or "Add the most relevant order, payment or support record.")
    reason = str(first.get("why") or "This is the next step in the reviewed case workflow.")
    parts: list[str] = []
    case_bits = [value for value in (merchant, issue, amount_label) if value]
    if case_bits:
        parts.append("YOUR CASE · " + " | ".join(case_bits))

    reported: list[str] = []
    if facts.get("elapsed_time_reported"):
        reported.append("Pending for " + str(facts["elapsed_time_reported"]) + " (as you reported).")
    if facts.get("contacted_support") is True:
        reported.append("You already contacted support; no response has been reported.")
    elif facts.get("contacted_support") is False:
        reported.append("You have not contacted support yet.")
    if reported:
        parts.append("WHAT YOU TOLD US\n" + "\n".join("• " + item for item in reported))

    parts.append("Your next move: " + title)
    # The first deterministic playbook action is retained, but long rationale text
    # is trimmed from the conversation bubble. The right panel keeps full detail.
    parts.append(detail)
    if route:
        parts.append("OFFICIAL SUPPORT · " + str(route.get("name") or "Organisation support"))
        parts.append(str(route.get("action") or "Open the organisation's official support channel and select the order or transaction."))
        if route.get("url"):
            parts.append("Open: " + str(route["url"]))

    draft = resolution.get("suggested_support_draft", {})
    if classification.get("issue_type") == "Refund not received" and facts.get("contacted_support") is True:
        parts.append("ADD ONE PROOF\nUpload either (1) the order cancellation/refund confirmation, or (2) a screenshot of the earlier support ticket/chat. Start with one relevant item; hide unrelated personal details, OTPs, PINs and passwords.")
    elif isinstance(draft, dict) and draft.get("message"):
        parts.append("SUPPORT MESSAGE\nA ready-to-edit follow-up message is available in the case panel. Review it and send it yourself through the official channel.")

    missing = resolution.get("missing_information", [])
    missing = missing if isinstance(missing, list) else []
    if missing:
        # Ask for only the first useful missing fact, not every possible field.
        parts.append("ONE DETAIL THAT WILL HELP\n" + str(missing[0]))
    parts.append("WHEN YOU GET A REPLY\nAdd the support response here. This same case will update with the next action; nothing is sent automatically.")
    parts.append("Based on your report and the official source shown. BolKeResolve has not accessed Flipkart, bank or payment records.")
    return "\n".join(part.strip() for part in parts if part and part.strip())[:2200]


@app.post("/api/cases/{case_id}/live-room/turn")
def save_live_room_turn(case_id: str, request: LiveRoomTurnRequest):
    """Persist a user turn without prematurely generating recommendations.

    The first story remains in collection mode until the user explicitly finishes
    explaining. After intake is complete, each answer advances one adaptive stage.
    """
    normalized_id = case_id.upper()
    if request.language_code not in LANGUAGES and request.language_code != "hi-en":
        raise HTTPException(status_code=400, detail="Choose a supported language.")
    safe_text = scrub_sensitive_text(request.text.strip())
    if len(safe_text.text) < 2:
        raise HTTPException(status_code=422, detail="There is not enough safe text to save.")
    stamp = now_iso()
    with get_db() as con:
        row = require_case_access(con, normalized_id)
        prior_text = current_conversation_turn_texts(con, normalized_id)
        draft_description = str(row["description"] or "")
        is_unstarted_draft = draft_description.startswith("Live resolution started. The user's issue description is being collected.")
        first_story = safe_text.text if is_unstarted_draft else draft_description
        combined = "\n".join(part for part in [*prior_text, safe_text.text] if part)[-8000:]
        resolution = json.loads(row["resolution_json"] or "{}")
        if not isinstance(resolution, dict): resolution = {}
        workflow_previous = resolution.get("adaptive_workflow", {}) if isinstance(resolution.get("adaptive_workflow"), dict) else {}
        previous_question = workflow_previous.get("next_question", {}) if isinstance(workflow_previous.get("next_question"), dict) else {}
        facts = extract_workflow_facts(combined, workflow_previous.get("facts", {}), str(previous_question.get("field", "")))
        # Re-read the newest turn against the accumulated fact snapshot so explicit
        # corrections and newly supplied values override older facts. Historical
        # context remains available for merchant/status recognition and audit.
        latest_fact_snapshot = extract_workflow_facts(
            safe_text.text, facts, str(previous_question.get("field", ""))
        )
        facts.update({key: value for key, value in latest_fact_snapshot.items() if value not in (None, "", [], {})})
        # Update only clearly user-reported facts. Do not run the generic recommendation
        # engine here: the user may still be narrating their first story.
        saved_merchant = facts.get("merchant") or str(row["merchant"] or "")
        saved_amount = facts.get("amount") if facts.get("amount") is not None else row["amount"]
        issue_type = facts.get("issue_type") or str(row["issue_type"] or "Other payment issue")
        contacted = facts.get("support_contacted")
        if contacted is None: contacted = row["contacted_support"]
        intake_complete = bool(workflow_previous.get("intake_complete"))
        # Carry the just-extracted facts into the workflow builder. This makes
        # the current expected question authoritative for short spoken answers.
        workflow_previous = {**workflow_previous, "facts": facts}
        workflow = build_adaptive_workflow(
            combined or first_story, previous=workflow_previous, intake_complete=intake_complete,
            evidence_count=con.execute("SELECT COUNT(*) FROM evidence WHERE case_id=?", (normalized_id,)).fetchone()[0],
        )
        resolution["adaptive_workflow"] = workflow
        # Keep legacy case renderers in sync with the adaptive state. In
        # particular, clear stale questions during collection/action stages.
        resolution["fastest_path"] = {"title": workflow.get("title", "Tell us what happened"), "reason": workflow.get("reason", "")}
        resolution["recommended_steps"] = [workflow["current_step"]] if workflow.get("current_step") else []
        resolution["next_question"] = workflow.get("next_question")
        resolution["clarifying_question"] = (workflow.get("next_question") or {}).get("prompt", "")
        resolution["support_destinations"] = workflow.get("support_destinations", [])
        resolution["suggested_support_draft"] = workflow.get("support_draft") or {}
        con.execute(
            "UPDATE cases SET description=?, issue_type=?, merchant=?, amount=?, contacted_support=?, language_code=?, resolution_json=?, updated_at=?, status='Information received', case_stage=? WHERE case_id=?",
            (first_story[:5000], issue_type, saved_merchant, saved_amount,
             None if contacted is None else int(bool(contacted)), request.language_code,
             json.dumps(resolution, ensure_ascii=False), stamp,
             "Collecting the user's story" if not intake_complete else "Updating resolution details", normalized_id),
        )
        source_labels = {
            "typed": "user-entered text",
            "live_speech": "final transcript returned by Gnani live speech recognition",
            "imported_call_recording": "user-confirmed transcript preview from an uploaded recording",
            "user_note": "user-entered case note",
        }
        metadata = {
            "speaker": "user", "language_code": request.language_code,
            "session_id": re.sub(r"[^A-Za-z0-9_-]", "", request.session_id)[:80],
            "input_source": request.input_source,
            "redacted_categories": safe_text.redacted_types,
            "provenance": source_labels[request.input_source] + "; user-provided and not independently verified",
        }
        turn_id = uuid.uuid4().hex
        source_evidence_id = None
        if request.input_source == "imported_call_recording" and metadata["session_id"]:
            linked = con.execute(
                "SELECT evidence_id FROM evidence WHERE case_id=? AND session_id=? AND mime_type LIKE 'audio/%' ORDER BY created_at DESC LIMIT 1",
                (normalized_id, metadata["session_id"]),
            ).fetchone()
            source_evidence_id = linked["evidence_id"] if linked else None
        record_case_event(con, normalized_id, "live_room_user_turn", "User said: " + safe_text.text,
                          stamp, actor="user", channel="live_room", source="live_resolution_room", metadata={**metadata, "turn_id": turn_id, "source_evidence_id": source_evidence_id})
        con.execute(
            "INSERT INTO conversation_turns (turn_id, case_id, speaker, text, language_code, input_source, source_evidence_id, session_id, user_confirmed, created_at) VALUES (?, ?, 'user', ?, ?, ?, ?, ?, 1, ?)",
            (turn_id, normalized_id, safe_text.text, request.language_code, request.input_source, source_evidence_id, metadata["session_id"], stamp),
        )
        record_case_fact_snapshot(con, normalized_id, facts, source_type=request.input_source, source_excerpt=safe_text.text, confidence="user_reported")
        record_product_quality_event(con, "user_turn_saved", case_id=normalized_id, issue_family=str(facts.get("issue_family") or ""), workflow_stage=str(workflow.get("stage") or ""), channel="live_room")
        bundle = case_bundle(con, normalized_id)
        bundle["redacted_categories"] = safe_text.redacted_types
        return bundle


@app.patch("/api/cases/{case_id}/conversation-turns/{turn_id}", status_code=201)
def correct_conversation_turn(case_id: str, turn_id: str, request: ConversationTurnCorrectionRequest):
    """Append a corrected transcript version while retaining the original turn."""
    normalized_id = case_id.upper()
    clean = scrub_sensitive_text(request.text.strip())
    if len(clean.text) < 2:
        raise HTTPException(status_code=422, detail="Add a little more detail to the corrected transcript.")
    stamp = now_iso()
    with get_db() as con:
        require_case_access(con, normalized_id)
        original = con.execute(
            "SELECT * FROM conversation_turns WHERE turn_id=? AND case_id=? AND speaker='user' ORDER BY created_at DESC LIMIT 1",
            (turn_id, normalized_id),
        ).fetchone()
        if not original:
            raise HTTPException(status_code=404, detail="Conversation turn not found.")
        new_id = uuid.uuid4().hex
        con.execute(
            "INSERT INTO conversation_turns (turn_id, case_id, speaker, text, language_code, input_source, transcript_confidence, source_evidence_id, session_id, user_confirmed, supersedes_turn_id, created_at) VALUES (?, ?, 'user', ?, ?, 'user_correction', ?, ?, ?, 1, ?, ?)",
            (new_id, normalized_id, clean.text, original["language_code"], original["transcript_confidence"], original["source_evidence_id"], original["session_id"], turn_id, stamp),
        )
        record_case_event(
            con, normalized_id, "conversation_turn_corrected",
            "The user corrected a saved conversation transcript. The previous wording remains in the case history.",
            stamp, actor="user", channel="live_room", source="transcript_correction",
            metadata={"turn_id": new_id, "supersedes_turn_id": turn_id, "source_evidence_id": original["source_evidence_id"], "redacted_categories": clean.redacted_types},
        )
        con.execute("UPDATE cases SET updated_at=? WHERE case_id=?", (stamp, normalized_id))
        return {"ok": True, "turn_id": new_id, "supersedes_turn_id": turn_id, "case": case_bundle(con, normalized_id)}


@app.post("/api/cases/{case_id}/live-room/guidance")
async def save_live_room_guidance(case_id: str, request: LiveRoomGuidanceRequest):
    """Advance the case from the complete history, with optional consented semantic interpretation."""
    normalized_id = case_id.upper()
    if request.language_code not in LANGUAGES and request.language_code != "hi-en":
        raise HTTPException(status_code=400, detail="Choose a supported language.")
    stamp = now_iso()

    # Read a compact, redacted case context and release SQLite before network calls.
    with get_db() as con:
        case_row = require_case_access(con, normalized_id)
        evidence_context = _confirmed_live_evidence_context(con, normalized_id)
        conversation_turns = current_conversation_turn_texts(con, normalized_id)
        conversation_text = "\n".join(conversation_turns or [str(case_row["description"] or "")])[-9000:]
        latest_turn = conversation_turns[-1] if conversation_turns else str(case_row["description"] or "")
        workflow_input = "\n".join(part for part in (conversation_text, evidence_context) if part)[-11000:]
        resolution = json.loads(case_row["resolution_json"] or "{}")
        if not isinstance(resolution, dict):
            resolution = {}
        previous = resolution.get("adaptive_workflow", {}) if isinstance(resolution.get("adaptive_workflow"), dict) else {}
        if request.finish_intake:
            previous = {**previous, "collecting_update": False}
        intake_complete = bool(request.finish_intake or previous.get("intake_complete"))
        evidence_count = con.execute("SELECT COUNT(*) FROM evidence WHERE case_id=?", (normalized_id,)).fetchone()[0]
        interpretation_allowed = _live_room_case_interpretation_consent(con, normalized_id)
        translation_allowed = _live_room_ai_consent(con, normalized_id)
        previous_facts = previous.get("facts", {}) if isinstance(previous.get("facts"), dict) else {}
        current_question = previous.get("next_question") if isinstance(previous.get("next_question"), dict) else None
        compact_case = {
            "case_id": normalized_id,
            "issue_type": case_row["issue_type"],
            "merchant": case_row["merchant"],
            "amount": case_row["amount"],
            "payment_status": case_row["payment_status"],
            "facts": previous_facts,
        }

    analysis: dict[str, Any] = {}
    semantic_facts: dict[str, Any] = {}
    applied_fact_updates: list[dict[str, Any]] = []
    case_ai_available = agent_assist.configured()
    if intake_complete and interpretation_allowed and case_ai_available and latest_turn.strip():
        try:
            analysis = await agent_assist.interpret_case_conversation(
                conversation=conversation_text,
                latest_turn=latest_turn,
                current_facts=previous_facts,
                current_question=current_question,
                workflow_context={"case": compact_case, "stage": previous.get("stage", ""), "status": previous.get("status", "")},
                language_code=request.language_code,
            )
            semantic_facts, applied_fact_updates = agent_assist.apply_quoted_case_fact_updates(
                previous_facts, analysis, conversation_text,
            )
            # If the model identifies a genuinely different issue, do not carry the
            # previous complaint's amount/status/order facts into the new route. Keep
            # only new-turn facts that passed exact-quote validation, and preserve the
            # full prior conversation in the timeline for auditability.
            latest_normalized = re.sub(r"\s+", " ", latest_turn).strip().casefold()
            accepted_family = any(
                item.get("field") == "issue_family" and
                re.sub(r"\s+", " ", str(item.get("evidence_quote") or "")).strip().casefold() in latest_normalized
                for item in applied_fact_updates
            )
            if analysis.get("intent") == "new_issue" and analysis.get("different_issue") and accepted_family:
                keep_fields = {item.get("field") for item in applied_fact_updates}
                reset_values = {
                    "merchant": "", "payment_app": "", "amount": None, "issue_type": "", "unauthorized": False,
                    "order_outcome": "", "refund_scope": "", "refund_status": "",
                    "refund_reason": "", "item_count": None, "promised_timeline": "",
                    "elapsed": "", "support_contacted": None, "support_reference": "",
                    "payment_method": "", "transaction_status": "", "transaction_date": "",
                }
                for field, value in reset_values.items():
                    if field not in keep_fields:
                        semantic_facts[field] = value
            else:
                # A new issue must be grounded in both the model's intent and a quoted
                # issue-family update, not just an ungrounded boolean flag.
                analysis["different_issue"] = False
            analysis["applied_fact_updates"] = applied_fact_updates
        except Exception as exc:
            logger.warning("Live case semantic interpretation failed (%s)", type(exc).__name__)
            analysis = {"enabled": True, "failed": True, "intent": "unclear", "summary": ""}

    # Build the next step from deterministic, source-reviewed workflows. Model output
    # may add only quote-validated facts; it cannot add support URLs or choose legal routes.
    workflow = build_adaptive_workflow(
        workflow_input,
        previous=previous,
        intake_complete=intake_complete,
        evidence_count=evidence_count,
        semantic_facts=semantic_facts,
        semantic_analysis=analysis,
    )
    if analysis and analysis.get("summary"):
        workflow["user_understanding_summary"] = str(analysis["summary"])[:500]
    if analysis and not analysis.get("failed") and case_ai_available and interpretation_allowed and intake_complete:
        try:
            personalized = await agent_assist.compose_case_guidance(
                latest_turn=latest_turn,
                case_summary=str(analysis.get("summary") or ""),
                facts=workflow.get("facts", {}),
                next_question=workflow.get("next_question"),
                current_step=workflow.get("current_step"),
                evidence_request=workflow.get("evidence_request"),
                official_routes=workflow.get("support_destinations", []),
                language_code=request.language_code,
            )
            if personalized:
                workflow["message"] = personalized
                workflow["response_mode"] = "consented_semantic_case_guidance"
        except Exception as exc:
            logger.warning("Live case response composition failed (%s)", type(exc).__name__)

    guidance_english = str(workflow.get("message") or "Your case is saved. Continue sharing details when you are ready.")
    guidance_text = guidance_english
    guidance_language = "en-IN"
    if workflow.get("response_mode") == "consented_semantic_case_guidance":
        guidance_language = request.language_code
        translation_status = "ai_personalized"
    elif request.language_code == "en-IN":
        translation_status = "native_language"
    elif not translation_allowed:
        translation_status = "consent_required"
    elif not case_ai_available:
        translation_status = "provider_not_configured"
    else:
        try:
            guidance_text = await agent_assist.localize_guidance(guidance_english, request.language_code)
            guidance_language = request.language_code
            translation_status = "translated"
        except Exception as exc:
            logger.warning("Live guidance localization failed (%s)", type(exc).__name__)
            translation_status = "translation_unavailable"

    facts = workflow.get("facts", {})
    resolution["adaptive_workflow"] = workflow
    resolution["fastest_path"] = {"title": workflow.get("title", "Tell us what happened"), "reason": workflow.get("reason", "")}
    resolution["recommended_steps"] = [workflow["current_step"]] if workflow.get("current_step") else []
    resolution["next_question"] = workflow.get("next_question")
    resolution["support_destinations"] = workflow.get("support_destinations", [])
    resolution["suggested_support_draft"] = workflow.get("support_draft") or {}
    resolution["clarifying_question"] = (workflow.get("next_question") or {}).get("prompt", "")
    case_stage = {
        "collecting_story": "Collecting the user's story", "collecting_update": "Collecting case update",
        "question": "Needs one detail", "action": "Action ready", "complete": "Resolution outcome recorded",
    }.get(workflow.get("status"), "Needs next step")
    issue_type = facts.get("issue_type") or str(compact_case.get("issue_type") or "Other payment issue")
    merchant = facts.get("merchant") or str(compact_case.get("merchant") or "")
    amount = facts.get("amount") if facts.get("amount") is not None else compact_case.get("amount")
    contacted = facts.get("support_contacted")
    if contacted is None:
        contacted = compact_case.get("contacted_support")
    with get_db() as con:
        require_case_access(con, normalized_id)
        con.execute(
            "UPDATE cases SET issue_type=?, merchant=?, amount=?, contacted_support=?, resolution_json=?, case_stage=?, updated_at=? WHERE case_id=?",
            (issue_type, merchant, amount, None if contacted is None else int(bool(contacted)),
             json.dumps(resolution, ensure_ascii=False), case_stage, stamp, normalized_id),
        )
        if intake_complete:
            metadata = {
                "speaker": "assistant", "language_code": guidance_language,
                "requested_language_code": request.language_code,
                "translation_status": translation_status,
                "confirmed_evidence_context_used": bool(evidence_context),
                "session_id": re.sub(r"[^A-Za-z0-9_-]", "", request.session_id)[:80],
                "workflow_stage": workflow.get("stage", ""),
                "workflow_engine": workflow.get("engine_version", ""),
                "case_interpretation_enabled": bool(interpretation_allowed and case_ai_available),
                "case_interpretation_intent": str(analysis.get("intent") or "")[:40],
                "case_interpretation_fact_updates": len(applied_fact_updates),
                "provenance": "rule-selected action from user-reported facts and reviewed routes; optional AI wording used only after consent and quote-validated fact extraction; not an external organisation response",
            }
            record_case_event(con, normalized_id, "live_room_agent_guidance", "BolKeResolve guidance: " + str(workflow.get("message") or "Your case was updated."),
                              stamp, actor="assistant", channel="live_room", source="adaptive_resolution_workflow", metadata=metadata)
        record_case_fact_snapshot(con, normalized_id, workflow.get("facts", {}), source_type="live_room_workflow", source_excerpt=latest_turn, confidence="user_reported_or_user_confirmed")
        family = str((workflow.get("facts") or {}).get("issue_family") or "")
        record_product_quality_event(con, "workflow_guidance_generated", case_id=normalized_id, issue_family=family, workflow_stage=str(workflow.get("stage") or ""), channel="live_room")
        if workflow.get("status") == "question" and isinstance(workflow.get("next_question"), dict):
            record_product_quality_event(con, "workflow_question_shown", case_id=normalized_id, issue_family=family, workflow_stage=str(workflow.get("stage") or ""), channel="live_room")
            prior_field = str((previous.get("next_question") or {}).get("field") or "") if isinstance(previous, dict) else ""
            next_field = str(workflow["next_question"].get("field") or "")
            if prior_field and next_field and prior_field == next_field:
                record_product_quality_event(con, "workflow_question_repeated", case_id=normalized_id, issue_family=family, workflow_stage=str(workflow.get("stage") or ""), channel="live_room")
        if workflow.get("status") == "action":
            record_product_quality_event(con, "workflow_action_ready", case_id=normalized_id, issue_family=family, workflow_stage=str(workflow.get("stage") or ""), channel="live_room")
        if analysis.get("failed"):
            record_product_quality_event(con, "semantic_interpretation_failed", case_id=normalized_id, issue_family=family, workflow_stage=str(workflow.get("stage") or ""), channel="live_room")
        result_case = case_bundle(con, normalized_id)

    return {
        "case": result_case, "guidance_text": guidance_text, "guidance_english": guidance_english,
        "workflow": workflow, "language_code": guidance_language,
        "requested_language_code": request.language_code, "translation_status": translation_status,
        "external_ai_consent": translation_allowed,
        "case_interpretation_consent": interpretation_allowed,
        "case_interpretation_available": case_ai_available,
        "case_interpretation_used": bool(workflow.get("response_mode") == "consented_semantic_case_guidance"),
        "visual_evidence_ai_available": case_ai_available,
    }


@app.post("/api/cases/{case_id}/live-room/evidence/{evidence_id}/analyze")
async def analyze_live_room_evidence(case_id: str, evidence_id: str, request: LiveRoomEvidenceAnalysisRequest, http_request: Request):
    """Analyse one saved image only after a separate, explicit per-image AI-processing consent."""
    normalized_id = case_id.upper()
    if not request.consent_to_external_processing:
        raise HTTPException(status_code=400, detail="Check the consent box before sending this image to the configured AI provider.")
    if not agent_assist.configured():
        raise HTTPException(status_code=503, detail="Visual AI is not configured. Add OPENAI_API_KEY on the server; local OCR review remains available.")
    enforce_voice_rate_limit(http_request, "live-vision", int(os.getenv("BOLKE_LIVE_VISION_LIMIT_PER_MINUTE", "8")))
    with get_db() as con:
        require_case_access(con, normalized_id)
        row = con.execute("SELECT evidence_id, original_name, stored_name, mime_type, size_bytes FROM evidence WHERE case_id=? AND evidence_id=?", (normalized_id, evidence_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Evidence file not found.")
        if row["mime_type"] not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=415, detail="Visual AI currently analyses JPG, PNG and WEBP images. PDFs remain available through local OCR review.")
        case_row = con.execute("SELECT description, merchant, amount, payment_date, payment_status, language_code FROM cases WHERE case_id=?", (normalized_id,)).fetchone()
        user_turns = con.execute("SELECT message FROM timeline WHERE case_id=? AND event_type='live_room_user_turn' ORDER BY created_at DESC, rowid DESC LIMIT 4", (normalized_id,)).fetchall()
        stored_name = Path(row["stored_name"]).name
        if stored_name != row["stored_name"] or stored_name in {"", ".", ".."}:
            raise HTTPException(status_code=400, detail="The evidence file reference is invalid.")
        evidence_path = UPLOAD_DIR / stored_name
        case_language = case_row["language_code"]
        context_parts = [str(case_row["description"] or "")]
        if case_row["merchant"]:
            context_parts.append("Merchant candidate: " + str(case_row["merchant"]))
        if case_row["amount"] is not None:
            context_parts.append("Amount candidate: " + str(case_row["amount"]))
        if case_row["payment_date"]:
            context_parts.append("Payment date candidate: " + str(case_row["payment_date"]))
        if case_row["payment_status"] and case_row["payment_status"] != "unknown":
            context_parts.append("Payment status candidate: " + str(case_row["payment_status"]))
        context_parts.extend(str(turn["message"] or "")[:600] for turn in reversed(user_turns))
        case_context = "\n".join(part for part in context_parts if part)[-3000:]
    if not evidence_path.exists():
        raise HTTPException(status_code=404, detail="The original evidence file is missing from storage.")
    if evidence_path.stat().st_size > MAX_EVIDENCE_BYTES:
        raise HTTPException(status_code=413, detail="This image is too large for visual analysis. Upload an image under 8 MB.")
    try:
        with Image.open(evidence_path) as source_image:
            image = ImageOps.exif_transpose(source_image).convert("RGB")
            image.thumbnail((1800, 1800))
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=88, optimize=True)
            image_bytes = buffer.getvalue()
    except Exception as exc:
        raise HTTPException(status_code=415, detail="This file is not a readable image. Use the original document or a fresh screenshot.") from exc
    image_data_url = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("ascii")
    try:
        result = await agent_assist.analyze_image(
            image_data_url=image_data_url,
            language_code=case_language,
            question=request.question,
            case_context=case_context,
        )
    except Exception as exc:
        logger.warning("Live evidence AI analysis failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Visual analysis is temporarily unavailable. Your original evidence remains safely attached; use local OCR review or try again.") from exc
    analysis_id = uuid.uuid4().hex
    stamp = now_iso()
    with get_db() as con:
        require_case_access(con, normalized_id)
        con.execute(
            "INSERT INTO live_room_evidence_analyses (analysis_id, case_id, evidence_id, model_name, result_json, status, created_at) VALUES (?, ?, ?, ?, ?, 'previewed', ?)",
            (analysis_id, normalized_id, evidence_id, str(result.get("model", ""))[:80], json.dumps(result, ensure_ascii=False), stamp),
        )
        record_case_event(
            con, normalized_id, "live_room_evidence_analysis_previewed",
            f"AI visual review prepared for {Path(row['original_name']).name}. Findings are unconfirmed and have not changed case facts.",
            stamp, actor="assistant", channel="live_room", source="user_consented_visual_ai",
            metadata={"analysis_id": analysis_id, "evidence_id": evidence_id, "model": result.get("model", ""), "external_processing_consented": True, "case_context_included": bool(case_context), "provider_api_store_disabled": True, "provider_side_retention_governed_by_provider_terms": True, "provenance": "AI-generated visual candidate analysis using selected image and minimum relevant user-reported case context; not document authentication"},
        )
        con.execute("UPDATE cases SET updated_at=? WHERE case_id=?", (stamp, normalized_id))
    return {"analysis_id": analysis_id, "evidence_id": evidence_id, "evidence_name": row["original_name"], "analysis": result, "status": "previewed", "notice": "The selected image and minimum relevant case details were sent to the configured AI provider after your consent. API response storage is disabled; provider-side data handling is still governed by its terms. These observations are not proof of authenticity or bank status. Confirm each fact against the original before adding it to your case."}


@app.post("/api/cases/{case_id}/live-room/evidence-analysis/confirm", status_code=201)
def confirm_live_room_evidence_analysis(case_id: str, request: LiveRoomEvidenceAnalysisConfirmRequest):
    if not request.confirmed:
        raise HTTPException(status_code=400, detail="Confirm that you reviewed the AI observations against the original image.")
    normalized_id = case_id.upper()
    accepted = list(dict.fromkeys(request.accepted_fields))
    apply_fields = list(dict.fromkeys(request.apply_fields))
    allowed = {"merchant", "amount", "payment_date", "payment_status", "reference_suffix"}
    if set(accepted) - allowed or set(apply_fields) - {"merchant", "amount", "payment_date", "payment_status"} or set(apply_fields) - set(accepted):
        raise HTTPException(status_code=422, detail="Choose only supported fields, and apply only facts you have accepted.")
    stamp = now_iso()
    with get_db() as con:
        case_row = require_case_access(con, normalized_id)
        analysis_row = con.execute("SELECT * FROM live_room_evidence_analyses WHERE analysis_id=? AND case_id=? AND status='previewed'", (request.analysis_id, normalized_id)).fetchone()
        if not analysis_row:
            raise HTTPException(status_code=404, detail="This visual review is no longer available. Analyse the saved image again.")
        if not con.execute("SELECT 1 FROM evidence WHERE evidence_id=? AND case_id=?", (analysis_row["evidence_id"], normalized_id)).fetchone():
            raise HTTPException(status_code=404, detail="The source evidence no longer belongs to this case.")
        try:
            result = json.loads(analysis_row["result_json"] or "{}")
        except json.JSONDecodeError:
            raise HTTPException(status_code=409, detail="The visual review could not be loaded. Run it again.")
        facts = result.get("facts", {}) if isinstance(result.get("facts"), dict) else {}
        selected = {field: facts[field] for field in accepted if field in facts and facts[field] not in (None, "")}
        if not selected:
            raise HTTPException(status_code=422, detail="Select at least one candidate fact to add to the case.")
        review_id = uuid.uuid4().hex
        candidates = {field: {"value": value, "confidence": result.get("fact_confidence", {}).get(field, "low"), "needs_confirmation": True} for field, value in selected.items()}
        con.execute(
            "INSERT INTO evidence_fact_reviews (review_id, case_id, evidence_id, candidates_json, conflicts_json, extraction_method, status, created_at, confirmed_at) VALUES (?, ?, ?, ?, '[]', 'vision_ai', 'confirmed', ?, ?)",
            (review_id, normalized_id, analysis_row["evidence_id"], json.dumps(candidates, ensure_ascii=False), stamp, stamp),
        )
        for field, value in selected.items():
            con.execute(
                "INSERT INTO case_fact_sources (fact_source_id, case_id, evidence_id, review_id, field_key, field_value_json, source_label, applied_to_case, confirmed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (uuid.uuid4().hex, normalized_id, analysis_row["evidence_id"], review_id, field, json.dumps(value, ensure_ascii=False), "AI visual candidate from user-selected image; checked and confirmed by user; authenticity not independently verified", int(field in apply_fields), stamp),
            )
        updates: dict[str, Any] = {}
        if "merchant" in apply_fields:
            updates["merchant"] = str(selected["merchant"])[:120]
        if "amount" in apply_fields:
            try:
                amount = float(selected["amount"])
            except (ValueError, TypeError) as exc:
                raise HTTPException(status_code=422, detail="The selected amount is not a valid number.") from exc
            if amount < 0 or amount > 100_000_000:
                raise HTTPException(status_code=422, detail="The selected amount is outside the supported range.")
            updates["amount"] = amount
        if "payment_date" in apply_fields:
            payment_date = str(selected["payment_date"])
            validate_payment_date(payment_date)
            updates["payment_date"] = payment_date
        if "payment_status" in apply_fields:
            status_text = str(selected["payment_status"]).lower()
            status = "pending" if "pending" in status_text else "failed" if any(word in status_text for word in ("fail", "declin")) else "success" if any(word in status_text for word in ("success", "complete", "credited")) else "unknown"
            updates["payment_status"] = status
        set_clause = ", ".join(f"{key}=?" for key in updates)
        if set_clause:
            con.execute(f"UPDATE cases SET {set_clause}, updated_at=? WHERE case_id=?", (*updates.values(), stamp, normalized_id))
        summary = str(result.get("summary") or "")[:700]
        observations = result.get("observations", []) if isinstance(result.get("observations"), list) else []
        metadata = {
            "analysis_id": request.analysis_id,
            "evidence_id": analysis_row["evidence_id"],
            "model": analysis_row["model_name"],
            "confirmed_fields": selected,
            "applied_fields": apply_fields,
            "confirmed_summary": summary,
            "observations": [str(item)[:180] for item in observations[:6]],
            "security_warning": bool(result.get("security_warning")),
            "provenance": "User reviewed and confirmed AI-derived candidates against the original image; underlying transaction not independently verified",
        }
        record_case_event(con, normalized_id, "live_room_evidence_analysis_confirmed", "The user reviewed AI visual observations and selected which facts to record. The original image remains the source exhibit.", stamp, actor="user", channel="live_room", source="user_confirmed_visual_review", metadata=metadata)
        con.execute("UPDATE live_room_evidence_analyses SET status='confirmed', confirmed_at=? WHERE analysis_id=? AND case_id=?", (stamp, request.analysis_id, normalized_id))
        derivative_payload = {
            "accepted_fields": selected, "applied_fields": apply_fields, "summary": summary,
            "observations": [str(item)[:180] for item in observations[:6]],
            "processor": analysis_row["model_name"],
            "notice": "AI-generated observations reviewed by the user against the original image. These observations do not authenticate the file or transaction.",
        }
        derivative_json = json.dumps(derivative_payload, ensure_ascii=False)
        con.execute(
            "INSERT INTO evidence_derivatives (derivative_id, case_id, evidence_id, derivative_type, mime_type, content_json, content_sha256, processor, review_status, created_at, confirmed_at) VALUES (?, ?, ?, 'visual_ai_review', 'application/json', ?, ?, ?, 'user_confirmed', ?, ?)",
            (uuid.uuid4().hex, normalized_id, analysis_row["evidence_id"], derivative_json, hashlib.sha256(derivative_json.encode('utf-8')).hexdigest(), str(analysis_row["model_name"] or "vision_ai")[:80], stamp, stamp),
        )
        # Recompute only from user-confirmed details; unreviewed model observations never route the case.
        current = con.execute("SELECT * FROM cases WHERE case_id=?", (normalized_id,)).fetchone()
        evidence_context = _confirmed_live_evidence_context(con, normalized_id)
        resolution_input = "\n".join(part for part in (str(current["description"] or ""), evidence_context) if part)[-7000:]
        existing_resolution = json.loads(current["resolution_json"] or "{}")
        adaptive_workflow = existing_resolution.get("adaptive_workflow") if isinstance(existing_resolution, dict) else None
        resolution = build_resolution(
            issue_type=str(current["issue_type"] or "Other payment issue"), description=resolution_input,
            merchant=str(current["merchant"] or ""), amount=current["amount"], payment_date=str(current["payment_date"] or ""),
            payment_status=str(current["payment_status"] or "unknown"),
            contacted_support=None if current["contacted_support"] is None else bool(current["contacted_support"]),
        )
        if isinstance(adaptive_workflow, dict):
            resolution["adaptive_workflow"] = adaptive_workflow
        resolution = add_support_context(resolution, str(current["merchant"] or ""), resolution_input, current["amount"])
        con.execute("UPDATE cases SET resolution_json=?, updated_at=? WHERE case_id=?", (json.dumps(resolution, ensure_ascii=False), stamp, normalized_id))
        return {"ok": True, "case": case_bundle(con, normalized_id), "accepted_fields": selected, "applied_fields": apply_fields, "guidance_ready": True}


@app.post("/api/cases/{case_id}/live-room/session-event")
def record_live_room_session_event(case_id: str, request: LiveRoomSessionEventRequest):
    """Append the lifecycle of a live session to the existing case timeline."""
    normalized_id = case_id.upper()
    stamp = now_iso()
    event_type = "live_room_session_started" if request.event == "started" else "live_room_session_ended"
    message = "Live resolution session started." if request.event == "started" else "Live resolution session ended by the user or page navigation."
    metadata = {
        "session_id": re.sub(r"[^A-Za-z0-9_-]", "", request.session_id)[:80],
        "started_at_client": request.started_at[:40] if request.event == "started" else "",
        "provenance": "application session event; records interface lifecycle, not a payment or support-provider event",
    }
    with get_db() as con:
        case_row = require_case_access(con, normalized_id)
        if request.event == "started":
            resolution = json.loads(case_row["resolution_json"] or "{}")
            if not isinstance(resolution, dict): resolution = {}
            workflow = resolution.get("adaptive_workflow")
            if isinstance(workflow, dict) and workflow.get("intake_complete"):
                workflow["collecting_update"] = True
                resolution["adaptive_workflow"] = workflow
                con.execute("UPDATE cases SET resolution_json=? WHERE case_id=?", (json.dumps(resolution, ensure_ascii=False), normalized_id))
        record_case_event(con, normalized_id, event_type, message, stamp, actor="user", channel="live_room", source="live_resolution_room", metadata=metadata)
        con.execute("UPDATE cases SET updated_at=? WHERE case_id=?", (stamp, normalized_id))
        return case_bundle(con, normalized_id)


@app.websocket("/api/live-room/voice")
async def live_room_voice_proxy(websocket: WebSocket):
    """Same-origin WebSocket proxy for Gnani Prisma; keeps the provider key server-side."""
    origin = websocket.headers.get("origin", "").strip()
    host = websocket.headers.get("host", "").lower()
    valid_origin = is_allowed_browser_origin(origin, host)
    if not valid_origin:
        await websocket.close(code=4403, reason="Origin not allowed")
        return
    if AUTH_REQUIRED:
        token = websocket.cookies.get(SESSION_COOKIE_NAME, "")
        user_id = lookup_session_user(token)
        public_enabled = os.getenv("BOLKE_PUBLIC_VOICE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
        if not user_id and not public_enabled:
            await websocket.close(code=4401, reason="Sign in to use live voice")
            return
    key = os.getenv("GNANI_API_KEY", "").strip()
    if not key:
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Live voice is not configured on this server yet. You can still type and upload evidence."})
        await websocket.close(code=4403)
        return
    address = websocket.client.host if websocket.client else "unknown"
    rate_key = f"live-stt:{address}"
    now = time.monotonic()
    attempts = [item for item in _VOICE_ATTEMPTS.get(rate_key, []) if now - item < 60]
    if len(attempts) >= int(os.getenv("BOLKE_LIVE_STT_LIMIT_PER_MINUTE", "5")):
        await websocket.close(code=4429, reason="Voice session limit reached. Please wait and retry.")
        return
    attempts.append(now)
    _VOICE_ATTEMPTS[rate_key] = attempts
    language = websocket.query_params.get("language_code", "indic-auto")
    if language not in {*LANGUAGES.keys(), "indic-auto"}:
        language = "indic-auto"
    # Stream at the AudioContext's actual rate. Prisma accepts native browser
    # rates and resamples server-side; do not label 48 kHz samples as 16 kHz.
    try:
        sample_rate = int(websocket.query_params.get("sample_rate", "48000"))
    except (TypeError, ValueError):
        sample_rate = 48000
    if sample_rate not in {8000, 16000, 44100, 48000}:
        sample_rate = 48000
    configured_model = os.getenv("GNANI_STT_MODEL", "prisma-v3.0").strip()
    # Auto language identification is a Prisma v3.0 feature. Do not silently send
    # indic-auto to v2.5: that creates the misleading state where the socket opens
    # but the user only gets a transcript after manually pinning a language.
    model = "prisma-v3.0" if language == "indic-auto" else configured_model
    # Gnani's current realtime guide recommends 0.60–0.70 for laptop/open-room
    # microphones, while quiet close-talk microphones need a lower threshold.
    # Keep the simple default suitable for a normal laptop and expose two
    # explicit alternatives in the Live Room settings.
    voice_profile = websocket.query_params.get("voice_profile", "laptop")
    profiles = {
        "laptop": {"x-vad-threshold": "0.62", "x-min-speech-ms": "100", "x-min-segment-ms": "100", "x-min-silence-ms": "600"},
        "quiet": {"x-vad-threshold": "0.50", "x-min-speech-ms": "70", "x-min-segment-ms": "100", "x-min-silence-ms": "550"},
        "noisy": {"x-vad-threshold": "0.70", "x-min-speech-ms": "200", "x-min-segment-ms": "220", "x-min-silence-ms": "750"},
    }
    if voice_profile not in profiles:
        voice_profile = "laptop"
    provider_headers = {
        "X-API-Key-ID": key,
        "language_code": language,
        "model": model,
        "format": "transcribe",
        "x-sample-rate": str(sample_rate),
        "x-idle-timeout-sec": "300",
        "x-max-speech-s": "30",
        **profiles[voice_profile],
    }
    await websocket.accept()
    upstream = None
    try:
        upstream = await websockets.connect(
            "wss://api.vachana.ai/stt/v3/stream",
            additional_headers=provider_headers,
            open_timeout=12, close_timeout=3, max_size=2 * 1024 * 1024,
        )
        try:
            first = await asyncio.wait_for(upstream.recv(), timeout=10)
            await websocket.send_text(first if isinstance(first, str) else first.decode("utf-8", "replace"))
        except asyncio.TimeoutError:
            pass

        async def browser_to_gnani():
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    return
                payload = message.get("bytes")
                if payload is not None:
                    # The browser worklet sends fixed-size mono PCM16 frames.
                    # Prisma expects 512 samples × 2 bytes for every frame.
                    if len(payload) != 1024:
                        await websocket.send_json({"type": "error", "message": "The microphone sent an invalid audio frame. Restart voice or continue by typing."})
                        continue
                    await upstream.send(payload)
                    continue
                text = message.get("text") or ""
                try:
                    command = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if command.get("type") == "commit":
                    # Provider uses VAD; a commit is only a user-initiated end-of-utterance hint.
                    await upstream.send(json.dumps({"type": "commit"}))

        async def gnani_to_browser():
            async for message in upstream:
                text = message if isinstance(message, str) else message.decode("utf-8", "replace")
                await websocket.send_text(text)
                try:
                    provider_event = json.loads(text)
                except (TypeError, json.JSONDecodeError):
                    provider_event = {}
                if isinstance(provider_event, dict) and provider_event.get("type") == "error":
                    logger.warning("Gnani live STT returned a provider error (%s)", str(provider_event.get("code") or "unspecified")[:80])
                    return

        tasks = [asyncio.create_task(browser_to_gnani()), asyncio.create_task(gnani_to_browser())]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            if task.exception():
                raise task.exception()
    except WebSocketDisconnect:
        pass
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as exc:
        logger.warning("Live STT proxy failed (%s)", type(exc).__name__)
        try:
            await websocket.send_json({"type": "error", "message": "The live speech connection failed. Check the Gnani API key, model access and microphone connection, then restart voice. You can keep typing; your case is saved."})
        except Exception:
            pass
    finally:
        if upstream is not None:
            try:
                await upstream.close()
            except Exception:
                pass
        try:
            await websocket.close()
        except Exception:
            pass


@app.post("/api/cases/{case_id}/evidence", status_code=201)
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    capture_source: str = Form(default="user_upload"),
    session_id: str = Form(default=""),
    captured_at: str = Form(default=""),
):
    case_id = case_id.upper()
    allowed_capture_sources = {"user_upload", "camera_photo", "screen_capture", "camera_video", "screen_video", "audio_recording", "imported_call_recording"}
    capture_source = capture_source if capture_source in allowed_capture_sources else "user_upload"
    session_id = re.sub(r"[^A-Za-z0-9_-]", "", session_id)[:80]
    client_captured_at = captured_at[:40] if captured_at else ""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EVIDENCE:
        raise HTTPException(status_code=415, detail="Allowed evidence formats: PNG, JPG, WEBP, PDF, WEBM, MP4, WAV, MP3, M4A, OGG, FLAC and AAC.")
    max_file_bytes = 20 * 1024 * 1024 if ext in {".webm", ".mp4"} else (MAX_AUDIO_BYTES if ext in {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac"} else MAX_EVIDENCE_BYTES)
    content = await file.read(max_file_bytes + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The evidence file is empty.")
    if len(content) > max_file_bytes:
        raise HTTPException(status_code=413, detail="Images and PDFs are limited to 8 MB, audio to 12 MB, and short video evidence to 20 MB.")
    # MediaRecorder commonly produces audio-only WebM. Preserve its audio MIME so
    # reopened cases render an audio player rather than a blank video element.
    declared_mime = (file.content_type or "").lower().split(";", 1)[0].strip()
    mime = "audio/webm" if ext == ".webm" and declared_mime.startswith("audio/") else ALLOWED_EVIDENCE[ext]
    # Basic signature checks reduce accidental upload mismatches. This is not malware scanning.
    if ext == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The file does not look like a PDF.")
    if ext in {".jpg", ".jpeg"} and not content.startswith(b"\xff\xd8\xff"):
        raise HTTPException(status_code=400, detail="The file does not look like a JPEG image.")
    if ext == ".png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=400, detail="The file does not look like a PNG image.")
    if ext == ".webp" and not (content.startswith(b"RIFF") and content[8:12] == b"WEBP"):
        raise HTTPException(status_code=400, detail="The file does not look like a WEBP image.")
    if ext == ".webm" and not content.startswith(b"\x1aE\xdf\xa3"):
        raise HTTPException(status_code=400, detail="The file does not look like a WEBM recording.")
    if ext == ".mp4" and (len(content) < 12 or content[4:8] != b"ftyp"):
        raise HTTPException(status_code=400, detail="The file does not look like an MP4 recording.")
    if ext == ".wav" and not (content.startswith(b"RIFF") and content[8:12] == b"WAVE"):
        raise HTTPException(status_code=400, detail="The file does not look like a WAV recording.")
    if ext == ".mp3" and not (content.startswith(b"ID3") or (len(content) > 1 and content[0] == 0xFF and content[1] & 0xE0 == 0xE0)):
        raise HTTPException(status_code=400, detail="The file does not look like an MP3 recording.")
    if ext == ".m4a" and (len(content) < 12 or content[4:8] != b"ftyp"):
        raise HTTPException(status_code=400, detail="The file does not look like an M4A recording.")
    if ext == ".ogg" and not content.startswith(b"OggS"):
        raise HTTPException(status_code=400, detail="The file does not look like an OGG recording.")
    if ext == ".flac" and not content.startswith(b"fLaC"):
        raise HTTPException(status_code=400, detail="The file does not look like a FLAC recording.")
    if ext == ".aac" and not (len(content) > 1 and content[0] == 0xFF and content[1] & 0xF6 == 0xF0):
        raise HTTPException(status_code=400, detail="The file does not look like an AAC recording.")
    if ext == ".csv":
        try:
            csv_text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="Please export this report as UTF-8 CSV.") from exc
        if "\x00" in csv_text[:4096] or len(csv_text.splitlines()) < 2:
            raise HTTPException(status_code=400, detail="The CSV needs a header and at least one data row.")
    with get_db() as con:
        require_case_access(con, case_id)
        usage = con.execute(
            "SELECT COUNT(*) AS file_count, COALESCE(SUM(size_bytes), 0) AS bytes_used FROM evidence WHERE case_id = ?",
            (case_id,),
        ).fetchone()
        if usage["file_count"] >= 10:
            raise HTTPException(status_code=413, detail="A case can contain at most 10 evidence files in this prototype.")
        if usage["bytes_used"] + len(content) > 40 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Evidence storage for a case is limited to 40 MB in this prototype.")
        evidence_id = uuid.uuid4().hex
        stored_name = evidence_id + ext
        (UPLOAD_DIR / stored_name).write_bytes(content)
        created = now_iso()
        submitted_name = (file.filename or "evidence").replace("\\", "/").split("/")[-1]
        original_name = scrub_sensitive_text(submitted_name).text[:180]
        sha256 = hashlib.sha256(content).hexdigest()
        con.execute(
            "INSERT INTO evidence (evidence_id, case_id, original_name, stored_name, mime_type, size_bytes, created_at, capture_source, captured_at, session_id, sha256) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (evidence_id, case_id, original_name, stored_name, mime, len(content), created, capture_source, client_captured_at, session_id, sha256),
        )
        con.execute("UPDATE cases SET updated_at = ?, status = ? WHERE case_id = ?", (created, "Evidence added", case_id))
        record_case_event(
            con, case_id, "evidence", f"Evidence file uploaded by the user: {original_name}. Its authenticity has not been verified.", created,
            actor="user", channel="live_room" if session_id else "web", source="evidence_upload",
            metadata={"evidence_id": evidence_id, "capture_source": capture_source, "session_id": session_id, "captured_at_client": client_captured_at, "mime_type": mime, "size_bytes": len(content), "sha256": sha256, "authenticity_verified": False, "malware_scan_status": "not_scanned"},
        )
        record_product_quality_event(con, "evidence_added", case_id=case_id, channel="live_room" if session_id else "web")
        bundle = case_bundle(con, case_id)
        bundle["uploaded_evidence_id"] = evidence_id
        return bundle


@app.post("/api/cases/{case_id}/reconciliation/preview", status_code=201)
async def preview_reconciliation_csv(case_id: str, file: UploadFile = File(...)):
    """Save the original CSV and return a minimised, review-first settlement preview."""
    normalized_id = case_id.upper()
    filename = Path(file.filename or "settlement-report.csv").name
    if Path(filename).suffix.casefold() != ".csv":
        raise HTTPException(status_code=415, detail="Choose a CSV settlement or transaction report.")
    raw = await file.read(MAX_CSV_BYTES + 1)
    try:
        preview = parse_reconciliation_csv(raw, provider_hint="Razorpay" if "razor" in filename.casefold() else "")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await file.seek(0)
    bundle = await upload_evidence(normalized_id, file, capture_source="user_upload", session_id="", captured_at="")
    evidence_id = bundle.get("uploaded_evidence_id")
    if not evidence_id:
        raise HTTPException(status_code=500, detail="The original report could not be saved to this case.")
    import_id = uuid.uuid4().hex
    created = now_iso()
    preview_to_save = {k: v for k, v in preview.items() if k != "notice"}
    with get_db() as con:
        require_case_access(con, normalized_id)
        con.execute(
            "INSERT INTO reconciliation_imports (import_id, case_id, evidence_id, provider, status, preview_json, created_at) VALUES (?, ?, ?, ?, 'previewed', ?, ?)",
            (import_id, normalized_id, evidence_id, str(preview.get("provider") or "Unspecified provider")[:60], json.dumps(preview_to_save, ensure_ascii=False), created),
        )
        record_case_event(con, normalized_id, "reconciliation_previewed", f"A {preview.get('provider', 'payment provider')} CSV report was saved as original evidence and parsed for user review. {preview['row_count']} usable rows were found; no values were applied to case facts.", created, actor="user", channel="web", source="reconciliation_import", metadata={"import_id": import_id, "evidence_id": evidence_id, "row_count": preview["row_count"], "status": "preview_requires_user_review"})
        record_product_quality_event(con, "reconciliation_previewed", case_id=normalized_id, channel="web")
        case = case_bundle(con, normalized_id)
    return {"import_id": import_id, "evidence_id": evidence_id, "preview": preview, "case": case}


@app.post("/api/cases/{case_id}/reconciliation/{import_id}/confirm", status_code=201)
def confirm_reconciliation_import(case_id: str, import_id: str, request: ReconciliationConfirmRequest):
    normalized_id = case_id.upper()
    if not request.confirmed:
        raise HTTPException(status_code=400, detail="Explicitly confirm the selected report rows before adding them to the case record.")
    with get_db() as con:
        require_case_access(con, normalized_id)
        row = con.execute("SELECT * FROM reconciliation_imports WHERE import_id=? AND case_id=?", (import_id, normalized_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Reconciliation import not found.")
        try:
            preview = json.loads(row["preview_json"] or "{}")
        except json.JSONDecodeError:
            preview = {}
        rows = preview.get("rows", []) if isinstance(preview, dict) else []
        selected = sorted(set(int(index) for index in request.selected_rows if 0 <= int(index) < len(rows)))
        if not selected:
            raise HTTPException(status_code=422, detail="Select at least one report row to confirm.")
        selected_rows = [rows[index] for index in selected]
        confirmed_at = now_iso()
        preview["confirmed_rows"] = selected_rows
        preview["confirmed_row_indices"] = selected
        preview["status"] = "user_confirmed_rows"
        con.execute("UPDATE reconciliation_imports SET status='confirmed', preview_json=?, confirmed_at=? WHERE import_id=?", (json.dumps(preview, ensure_ascii=False), confirmed_at, import_id))
        record_case_event(con, normalized_id, "reconciliation_confirmed", f"The user reviewed and confirmed {len(selected_rows)} row(s) from the {row['provider']} report. This is user-confirmed report content, not an independent provider or bank verification.", confirmed_at, actor="user", channel="web", source="reconciliation_import", metadata={"import_id": import_id, "evidence_id": row["evidence_id"], "confirmed_rows": len(selected_rows), "verification": "user_confirmed_report_not_provider_verified"})
        record_product_quality_event(con, "reconciliation_confirmed", case_id=normalized_id, channel="web")
        return {"ok": True, "import_id": import_id, "confirmed_rows": len(selected_rows), "case": case_bundle(con, normalized_id)}


@app.post("/api/cases/{case_id}/evidence/{evidence_id}/claims", status_code=201)
def link_evidence_to_claim(case_id: str, evidence_id: str, request: EvidenceClaimLinkRequest):
    normalized_id = case_id.upper()
    safe_label = scrub_sensitive_text(request.claim_label.strip()).text[:120]
    safe_note = scrub_sensitive_text(request.note.strip()).text[:300]
    if not safe_label:
        raise HTTPException(status_code=422, detail="Add a short label for the claim this file relates to.")
    with get_db() as con:
        require_case_access(con, normalized_id)
        evidence = con.execute("SELECT evidence_id FROM evidence WHERE evidence_id=? AND case_id=?", (evidence_id, normalized_id)).fetchone()
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence file not found in this case.")
        link_id = uuid.uuid4().hex
        created = now_iso()
        con.execute(
            "INSERT INTO evidence_claim_links (link_id, case_id, evidence_id, claim_key, claim_label, relation, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(evidence_id, claim_key, relation) DO UPDATE SET claim_label=excluded.claim_label, note=excluded.note, created_at=excluded.created_at",
            (link_id, normalized_id, evidence_id, request.claim_key, safe_label, request.relation, safe_note, created),
        )
        record_case_event(con, normalized_id, "evidence_claim_linked", f"The user linked an evidence file to the case claim: {safe_label} ({request.relation}). The link does not independently verify the claim.", created, actor="user", channel="web", source="evidence_claim_link", metadata={"evidence_id": evidence_id, "claim_key": request.claim_key, "relation": request.relation})
        record_product_quality_event(con, "evidence_claim_linked", case_id=normalized_id, channel="web")
        return {"ok": True, "case": case_bundle(con, normalized_id)}


@app.delete("/api/cases/{case_id}/evidence-claim-links/{link_id}")
def delete_evidence_claim_link(case_id: str, link_id: str):
    normalized_id = case_id.upper()
    with get_db() as con:
        require_case_access(con, normalized_id)
        deleted = con.execute("DELETE FROM evidence_claim_links WHERE link_id=? AND case_id=?", (link_id, normalized_id)).rowcount
        if not deleted:
            raise HTTPException(status_code=404, detail="Evidence-to-claim link not found.")
        record_case_event(con, normalized_id, "evidence_claim_unlinked", "The user removed an evidence-to-claim link.", actor="user", channel="web", source="evidence_claim_link")
        return {"ok": True, "case": case_bundle(con, normalized_id)}


@app.get("/api/internal/quality/summary")
def internal_product_quality_summary(x_bolke_metrics_token: str = Header(default="")):
    """Operator-only aggregate metrics. No message bodies, filenames or evidence are returned."""
    expected = os.getenv("BOLKE_QUALITY_METRICS_TOKEN", "").strip()
    if len(expected) < 24:
        raise HTTPException(status_code=404, detail="Not found")
    if not hmac.compare_digest(x_bolke_metrics_token, expected):
        raise HTTPException(status_code=401, detail="Invalid metrics token.")
    from datetime import timedelta
    since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    with get_db() as con:
        event_rows = con.execute(
            "SELECT event_name, COUNT(*) AS count FROM product_quality_events WHERE created_at>=? GROUP BY event_name ORDER BY event_name",
            (since,),
        ).fetchall()
        family_rows = con.execute(
            "SELECT issue_family, COUNT(DISTINCT case_id) AS cases FROM product_quality_events WHERE created_at>=? AND issue_family<>'' GROUP BY issue_family ORDER BY cases DESC LIMIT 20",
            (since,),
        ).fetchall()
        totals = {row["event_name"]: int(row["count"]) for row in event_rows}
        questions = totals.get("workflow_question_shown", 0)
        repeats = totals.get("workflow_question_repeated", 0)
        return {
            "window_days": 30,
            "generated_at": now_iso(),
            "privacy": "Aggregated product events only. User message text, filenames, payment references and evidence contents are never included.",
            "events": totals,
            "cases_by_issue_family": [dict(row) for row in family_rows],
            "metrics": {
                "cases_created": totals.get("case_created", 0),
                "evidence_added": totals.get("evidence_added", 0),
                "followups_set": totals.get("followup_set", 0),
                "user_reported_outcomes": totals.get("outcome_reported", 0),
                "question_repeat_rate": round(repeats / questions, 4) if questions else 0.0,
            },
        }


EVIDENCE_REVIEWABLE_FIELDS = {"merchant", "amount", "payment_date", "payment_status"}
EVIDENCE_APPLICABLE_FIELDS = {"merchant", "amount", "payment_date", "payment_status"}


def _candidate_value_is_present(value: object) -> bool:
    return value not in (None, "", "unknown")


def _compare_document_candidates(case_row: sqlite3.Row, candidates: dict[str, dict]) -> dict[str, dict]:
    comparisons: dict[str, dict] = {}
    for field in EVIDENCE_REVIEWABLE_FIELDS:
        item = candidates.get(field)
        if not isinstance(item, dict) or not _candidate_value_is_present(item.get("value")):
            continue
        candidate = item.get("value")
        current = case_row[field] if field in case_row.keys() else None
        current_present = current not in (None, "", "unknown")
        mismatch = False
        if current_present:
            if field == "amount":
                try:
                    mismatch = abs(float(current) - float(candidate)) >= 0.01
                except (TypeError, ValueError):
                    mismatch = str(current) != str(candidate)
            elif field in {"merchant", "payment_status"}:
                mismatch = str(current).strip().casefold() != str(candidate).strip().casefold()
            elif field == "payment_date":
                mismatch = str(current).strip() != str(candidate).strip()
        comparisons[field] = {
            "label": {"merchant": "Merchant / app", "amount": "Amount", "payment_date": "Date found", "payment_status": "Status wording"}[field],
            "value": candidate,
            "confidence": item.get("confidence", "low"),
            "source_excerpt": str(item.get("evidence", ""))[:160],
            "needs_confirmation": bool(item.get("needs_confirmation", True)),
            "current_value": current if current_present else None,
            "mismatch": bool(current_present and mismatch),
            "comparison": "possible_mismatch" if current_present and mismatch else "matches_current" if current_present else "no_saved_value",
            "comparison_notice": (
                "This value differs from the current case. Check the document and choose whether to update the case."
                if current_present and mismatch else
                "This value appears consistent with the current case; it is still only a document-derived candidate."
                if current_present else
                "No value is currently saved for this field. Confirm whether the document value belongs in this case."
            ),
        }
    return comparisons


@app.post("/api/cases/{case_id}/evidence/{evidence_id}/review")
def review_uploaded_evidence(case_id: str, evidence_id: str):
    """Extract candidate facts from one upload locally; raw OCR/text is never persisted."""
    normalized_id = case_id.upper()
    with get_db() as con:
        case_row = require_case_access(con, normalized_id)
        evidence = con.execute(
            "SELECT evidence_id, original_name, stored_name, mime_type FROM evidence WHERE case_id=? AND evidence_id=?",
            (normalized_id, evidence_id),
        ).fetchone()
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence file not found.")
        stored_name = Path(evidence["stored_name"]).name
        if stored_name != evidence["stored_name"] or stored_name in {"", ".", ".."}:
            raise HTTPException(status_code=400, detail="The evidence file reference is invalid.")
        stored_path = UPLOAD_DIR / stored_name
    try:
        extracted = extract_evidence_text(stored_path, str(evidence["mime_type"]))
    except EvidenceExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # keep parser failures private and non-fatal
        logger.warning("Evidence extraction failed for evidence %s (%s)", evidence_id[:8], type(exc).__name__)
        raise HTTPException(status_code=422, detail="This file could not be read reliably. You can review it manually.") from exc

    scrubbed = scrub_sensitive_text(str(extracted.get("text", "")))
    extraction = extract_case_facts(scrubbed.text)
    raw_fields = extraction.get("fields", {}) if isinstance(extraction, dict) else {}
    candidates: dict[str, dict] = {}
    for key in EVIDENCE_REVIEWABLE_FIELDS:
        item = raw_fields.get(key, {})
        value = item.get("value") if isinstance(item, dict) else None
        if not _candidate_value_is_present(value) or str(item.get("confidence", "low")) == "low":
            continue
        excerpt = scrub_sensitive_text(str(item.get("evidence", ""))).text[:160]
        candidates[key] = {
            "value": value,
            "confidence": str(item.get("confidence", "low")),
            "evidence": excerpt,
            "needs_confirmation": bool(item.get("needs_confirmation", True)),
        }
    if not candidates:
        raise HTTPException(status_code=422, detail="No reliable amount, merchant, date or status wording was detected. You can still use this file and check it manually.")

    # No source text is stored. Only bounded, redacted candidate fields and a source method remain.
    conflicts = extraction.get("conflicts", []) if isinstance(extraction, dict) else []
    safe_conflicts = [{
        "field": str(item.get("field", "unknown"))[:40],
        "values": item.get("values", [])[:8] if isinstance(item.get("values", []), list) else [],
        "message": scrub_sensitive_text(str(item.get("message", "Several possible values were found."))).text[:240],
    } for item in conflicts[:10] if isinstance(item, dict)]
    review_id = uuid.uuid4().hex
    stamp = now_iso()
    comparisons = _compare_document_candidates(case_row, candidates)
    stored_candidates = {
        key: {name: value for name, value in item.items() if name != "evidence"}
        for key, item in candidates.items()
    }
    with get_db() as con:
        require_case_access(con, normalized_id)
        # Confirm that the evidence row is still attached to this case before storing a preview.
        exists = con.execute("SELECT 1 FROM evidence WHERE case_id=? AND evidence_id=?", (normalized_id, evidence_id)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Evidence file not found.")
        con.execute(
            "INSERT INTO evidence_fact_reviews (review_id, case_id, evidence_id, candidates_json, conflicts_json, extraction_method, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'previewed', ?)",
            (review_id, normalized_id, evidence_id, json.dumps(stored_candidates, ensure_ascii=False), json.dumps(safe_conflicts, ensure_ascii=False), str(extracted.get("method", "local_extraction"))[:40], stamp),
        )
    return {
        "review_id": review_id,
        "evidence_id": evidence_id,
        "evidence_name": evidence["original_name"],
        "method": extracted.get("method", "local_extraction"),
        "fields": comparisons,
        "extraction_conflicts": safe_conflicts,
        "raw_document_text_saved": False,
        "notice": "Text was processed on this server and the extracted text itself was not retained. These are unverified candidates from your uploaded file. Confirm the wording before recording any fact; nothing in the case is changed unless you explicitly select an update.",
    }


@app.post("/api/cases/{case_id}/evidence-review/confirm", status_code=201)
def confirm_uploaded_evidence_review(case_id: str, request: EvidenceReviewConfirmRequest):
    if not request.confirmed:
        raise HTTPException(status_code=400, detail="Confirm that you reviewed the extracted details against the original file.")
    normalized_id = case_id.upper()
    accepted = list(dict.fromkeys(request.accepted_fields))
    apply = list(dict.fromkeys(request.apply_fields))
    if set(accepted) - EVIDENCE_REVIEWABLE_FIELDS or set(apply) - EVIDENCE_APPLICABLE_FIELDS:
        raise HTTPException(status_code=422, detail="One or more selected fields are not supported.")
    if set(apply) - set(accepted):
        raise HTTPException(status_code=422, detail="A field must be accepted as a document fact before it can update the case.")
    stamp = now_iso()
    with get_db() as con:
        case_row = require_case_access(con, normalized_id)
        review = con.execute(
            "SELECT * FROM evidence_fact_reviews WHERE review_id=? AND case_id=? AND status='previewed'",
            (request.review_id, normalized_id),
        ).fetchone()
        if not review:
            raise HTTPException(status_code=404, detail="This evidence review is no longer available. Run the review again.")
        exists = con.execute("SELECT 1 FROM evidence WHERE case_id=? AND evidence_id=?", (normalized_id, review["evidence_id"])).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Evidence file not found.")
        try:
            candidates = json.loads(review["candidates_json"] or "{}")
        except json.JSONDecodeError:
            candidates = {}
        missing = [field for field in accepted if field not in candidates]
        if missing:
            raise HTTPException(status_code=422, detail="A selected field is not part of this evidence review.")
        if not accepted:
            raise HTTPException(status_code=422, detail="Select at least one document detail to record.")
        changed: dict[str, object] = {}
        for field in accepted:
            item = candidates[field]
            value = item.get("value")
            source_label = f"Extracted from {review['extraction_method']} in user-uploaded file; reviewed by user; authenticity not independently verified"
            con.execute(
                "INSERT INTO case_fact_sources (fact_source_id, case_id, evidence_id, review_id, field_key, field_value_json, source_label, applied_to_case, confirmed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(review_id, field_key) DO UPDATE SET field_value_json=excluded.field_value_json, source_label=excluded.source_label, applied_to_case=excluded.applied_to_case, confirmed_at=excluded.confirmed_at",
                (uuid.uuid4().hex, normalized_id, review["evidence_id"], request.review_id, field, json.dumps(value, ensure_ascii=False), source_label, int(field in apply), stamp),
            )
            if field in apply:
                if field == "amount":
                    try:
                        value = float(value)
                    except (ValueError, TypeError) as exc:
                        raise HTTPException(status_code=422, detail="The extracted amount could not be applied safely.") from exc
                    if value < 0 or value > 100_000_000:
                        raise HTTPException(status_code=422, detail="The extracted amount is outside the supported range.")
                elif field == "payment_date":
                    value = str(value or "")
                    validate_payment_date(value)
                elif field == "merchant":
                    value = scrub_sensitive_text(str(value or "")).text[:100]
                elif field == "payment_status" and value not in {"unknown", "failed", "pending", "successful", "refund_pending", "unauthorized"}:
                    raise HTTPException(status_code=422, detail="The extracted payment status is not supported.")
                changed[field] = value
        if changed:
            merged = {key: case_row[key] for key in case_row.keys()}
            merged.update(changed)
            resolution = build_resolution(
                issue_type=merged.get("issue_type", "Other payment issue"), description=merged.get("description", ""),
                merchant=merged.get("merchant", ""), amount=merged.get("amount"), payment_date=merged.get("payment_date", ""),
                payment_status=merged.get("payment_status", "unknown"), contacted_support=None if merged.get("contacted_support") is None else bool(merged.get("contacted_support")),
            )
            resolution = add_support_context(resolution, str(merged.get("merchant") or ""), str(merged.get("description") or ""), merged.get("amount"))
            con.execute(
                "UPDATE cases SET merchant=?, amount=?, payment_date=?, payment_status=?, resolution_json=?, updated_at=?, status=? WHERE case_id=?",
                (merged.get("merchant", ""), merged.get("amount"), merged.get("payment_date", ""), merged.get("payment_status", "unknown"), json.dumps(resolution, ensure_ascii=False), stamp, "Evidence details reviewed", normalized_id),
            )
        con.execute("UPDATE evidence_fact_reviews SET status='confirmed', confirmed_at=? WHERE review_id=?", (stamp, request.review_id))
        derivative_payload = {
            "accepted_fields": {field: candidates[field].get("value") for field in accepted if field in candidates},
            "applied_fields": list(changed), "extraction_method": review["extraction_method"],
            "notice": "User-reviewed candidate facts derived from the original file. Raw OCR text was not retained; file authenticity was not independently verified.",
        }
        derivative_json = json.dumps(derivative_payload, ensure_ascii=False)
        con.execute(
            "INSERT INTO evidence_derivatives (derivative_id, case_id, evidence_id, derivative_type, mime_type, content_json, content_sha256, processor, review_status, created_at, confirmed_at) VALUES (?, ?, ?, 'document_fact_review', 'application/json', ?, ?, ?, 'user_confirmed', ?, ?)",
            (uuid.uuid4().hex, normalized_id, review["evidence_id"], derivative_json, hashlib.sha256(derivative_json.encode('utf-8')).hexdigest(), str(review["extraction_method"] or "local_extraction")[:80], stamp, stamp),
        )
        label_map = {"merchant": "merchant / app", "amount": "amount", "payment_date": "date", "payment_status": "payment-status wording"}
        recorded = ", ".join(label_map[field] for field in accepted)
        applied = ", ".join(label_map[field] for field in changed) or "none"
        event_message = f"The user reviewed candidate details extracted from an uploaded evidence file. Recorded document facts: {recorded}. Applied to case details: {applied}. The file authenticity and underlying payment were not independently verified; raw extracted document text was not retained."
        record_case_event(con, normalized_id, "evidence_facts_reviewed", event_message, stamp, actor="user", channel="web", source="user_confirmed_evidence_review", metadata={"evidence_id": review["evidence_id"], "review_id": request.review_id, "confirmed_fields": accepted, "applied_fields": list(changed), "raw_document_text_retained": False})
        return {"ok": True, "accepted_fields": accepted, "applied_fields": list(changed), "case": case_bundle(con, normalized_id), "raw_document_text_saved": False}


@app.delete("/api/cases/{case_id}/evidence-review/{review_id}")
def discard_evidence_review(case_id: str, review_id: str):
    normalized_id = case_id.upper()
    with get_db() as con:
        require_case_access(con, normalized_id)
        review = con.execute("SELECT review_id FROM evidence_fact_reviews WHERE review_id=? AND case_id=? AND status='previewed'", (review_id, normalized_id)).fetchone()
        if not review:
            raise HTTPException(status_code=404, detail="Evidence review not found.")
        con.execute("UPDATE evidence_fact_reviews SET status='discarded', candidates_json='{}', conflicts_json='[]', confirmed_at=? WHERE review_id=?", (now_iso(), review_id))
        return {"ok": True, "discarded": True}


def _draft_amount(value: object) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric < 0:
        return None
    return f"₹{numeric:,.0f}" if numeric.is_integer() else f"₹{numeric:,.2f}"


def _draft_payment_date(value: object, language: str = "en") -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = date.fromisoformat(raw[:10])
        if language == "hi":
            hindi_months = ("जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर")
            return f"{parsed.day} {hindi_months[parsed.month - 1]} {parsed.year}"
        return parsed.strftime("%d %b %Y")
    except (TypeError, ValueError):
        return None


def make_support_draft(case: dict, language: str) -> str:
    """Create an issue-specific message using only facts actually saved in the case.

    This is user-facing copy for a merchant/payment provider. Product disclaimers stay
    in the surrounding interface; they are not pasted into the user's complaint.
    Unknown data is omitted rather than filled with plausible-sounding placeholders.
    """
    language = language if language in {"en", "hi", "hinglish"} else "en"
    issue = str(case.get("issue_type") or "Other payment issue")
    merchant = re.sub(r"\s+", " ", str(case.get("merchant") or "").strip())
    description = str(case.get("description") or "").strip()
    amount = _draft_amount(case.get("amount"))
    payment_date = _draft_payment_date(case.get("payment_date"), language)
    payment_status = str(case.get("payment_status") or "unknown")
    contacted_support = case.get("contacted_support")

    summaries = {
        "en": {
            "Refund not received": "a refund that has not arrived",
            "Merchant settlement not credited": "merchant funds collected through the payment gateway that have not reached my business bank account",
            "Failed UPI payment": "a UPI payment that appears to have failed",
            "UPI payment pending / recipient not credited": "a UPI transfer where the recipient has not been credited",
            "Duplicate charge": "a possible duplicate charge",
            "Incorrect amount": "an amount discrepancy",
            "Order paid but not received": "an order I paid for but have not received",
            "Suspected fraud or unauthorised transaction": "a payment I do not recognise or believe may be unauthorised",
            "Other payment issue": "a payment-related issue",
        },
        "hi": {
            "Refund not received": "रिफंड न मिलने",
            "Merchant settlement not credited": "पेमेंट गेटवे से मेरे व्यवसाय के बैंक खाते में सेटलमेंट राशि न पहुँचने",
            "Failed UPI payment": "असफल UPI भुगतान",
            "UPI payment pending / recipient not credited": "लंबित UPI ट्रांसफर या प्राप्तकर्ता को राशि न मिलने",
            "Duplicate charge": "संभावित दोहरे शुल्क",
            "Incorrect amount": "राशि में अंतर",
            "Order paid but not received": "भुगतान किए गए ऑर्डर के न मिलने",
            "Suspected fraud or unauthorised transaction": "संभावित अनधिकृत भुगतान",
            "Other payment issue": "भुगतान से जुड़ी समस्या",
        },
        "hinglish": {
            "Refund not received": "refund jo abhi tak nahi aaya hai",
            "Merchant settlement not credited": "payment gateway se business bank account mein settlement amount nahi aane",
            "Failed UPI payment": "UPI payment jo failed dikh raha tha",
            "UPI payment pending / recipient not credited": "UPI transfer jisme recipient ko amount nahi mila hai",
            "Duplicate charge": "ek hi cheez ke liye possible double charge",
            "Incorrect amount": "amount mein difference",
            "Order paid but not received": "aisa order jiske liye payment ki, par order mila nahi",
            "Suspected fraud or unauthorised transaction": "aisa payment jise main pehchaan nahi raha/rahi ya unauthorised maanta/maanti hoon",
            "Other payment issue": "payment se judi problem",
        },
    }
    actions = {
        "en": {
            "Merchant settlement not credited": [
                "Please confirm the settlement status for the affected customer collections and whether the payments were captured.",
                "Share the settlement ID, scheduled settlement date and UTR if the settlement is marked processed.",
                "If the settlement failed or is on hold, explain the precise reason and any action or document required through the signed-in Dashboard.",
                "Please link this request to my existing support ticket, if one exists, and give the next expected update.",
            ],
            "Refund not received": [
                "Confirm whether the refund has been initiated.",
                "If it has been initiated, share the refund reference and expected credit date; if not, explain what is pending.",
                "Tell me the next step if the expected refund timeline has passed.",
            ],
            "Failed UPI payment": [
                "Confirm the transaction outcome against your records.",
                "If money was debited, share the reversal status, any reference available, and the expected timeline.",
            ],
            "UPI payment pending / recipient not credited": [
                "Confirm whether the recipient was credited.",
                "If the transfer did not complete, explain the reversal process, reference and expected timeline.",
            ],
            "Duplicate charge": [
                "Review the charges and confirm whether a duplicate payment occurred.",
                "If a duplicate is confirmed, explain the correction or reversal process and expected timeline.",
            ],
            "Incorrect amount": [
                "Review the amount shown in your records and explain the difference.",
                "Please advise how the incorrect amount can be corrected or formally disputed.",
            ],
            "Order paid but not received": [
                "Confirm the order's latest fulfilment or cancellation status.",
                "Explain the available delivery or refund option and its expected timeline.",
            ],
            "Suspected fraud or unauthorised transaction": [
                "Please review this urgently and explain how I should report and secure the affected payment method or account.",
                "Tell me which official reporting channel and reference I should use. I will not share an OTP, PIN or password.",
            ],
            "Other payment issue": [
                "Review the relevant order and payment records and explain what may have happened.",
                "Please give me the next action and the expected timeline.",
            ],
        },
        "hi": {
            "Merchant settlement not credited": [
                "कृपया संबंधित ग्राहक भुगतानों की सेटलमेंट स्थिति और यह पुष्टि करें कि भुगतान Captured हुए थे या नहीं।",
                "सेटलमेंट ID, निर्धारित सेटलमेंट तारीख और Processed होने पर UTR साझा करें।",
                "यदि सेटलमेंट Failed या On hold है, तो Dashboard में दिखाया गया सटीक कारण और आवश्यक कार्रवाई/दस्तावेज़ बताएं।",
                "यदि पहले से कोई सहायता टिकट है, तो इसी अनुरोध को उससे जोड़कर अगला अपडेट कब मिलेगा यह बताएं।",
            ],
            "Refund not received": [
                "कृपया पुष्टि करें कि रिफंड शुरू किया गया है या नहीं।",
                "यदि रिफंड शुरू हुआ है, तो उसका संदर्भ नंबर और खाते में आने की अनुमानित तारीख बताएं; यदि नहीं, तो बताएं कि क्या लंबित है।",
                "रिफंड की बताई गई समय-सीमा बीत गई है, तो अगला कदम बताएं।",
            ],
            "Failed UPI payment": [
                "कृपया अपने रिकॉर्ड में लेन-देन का परिणाम जाँचकर बताएं।",
                "यदि खाते से पैसे कटे हैं, तो रिवर्सल की स्थिति, उपलब्ध संदर्भ नंबर और अनुमानित समय-सीमा बताएं।",
            ],
            "UPI payment pending / recipient not credited": [
                "कृपया पुष्टि करें कि प्राप्तकर्ता को पैसे मिले हैं या नहीं।",
                "यदि ट्रांसफर पूरा नहीं हुआ, तो रिवर्सल की प्रक्रिया, संदर्भ नंबर और अनुमानित समय-सीमा बताएं।",
            ],
            "Duplicate charge": [
                "कृपया दोनों शुल्कों की जाँच कर पुष्टि करें कि दोहरा भुगतान हुआ है या नहीं।",
                "यदि दोहरा शुल्क हुआ है, तो सुधार या रिवर्सल की प्रक्रिया और समय-सीमा बताएं।",
            ],
            "Incorrect amount": [
                "कृपया अपने रिकॉर्ड में दिखाई गई राशि जाँचकर अंतर का कारण बताएं।",
                "गलत राशि को ठीक करने या औपचारिक रूप से चुनौती देने का तरीका बताएं।",
            ],
            "Order paid but not received": [
                "कृपया ऑर्डर की मौजूदा डिलीवरी या कैंसलेशन स्थिति बताएं।",
                "उपलब्ध डिलीवरी या रिफंड विकल्प और उसकी अनुमानित समय-सीमा बताएं।",
            ],
            "Suspected fraud or unauthorised transaction": [
                "कृपया इस मामले की तुरंत जाँच कर प्रभावित भुगतान माध्यम या खाते को सुरक्षित करने और रिपोर्ट करने का तरीका बताएं।",
                "कृपया आधिकारिक रिपोर्टिंग चैनल और संदर्भ नंबर बताएं। मैं OTP, PIN या पासवर्ड साझा नहीं करूँगा/करूँगी।",
            ],
            "Other payment issue": [
                "कृपया ऑर्डर और भुगतान से जुड़े रिकॉर्ड जाँचकर बताएं कि क्या हुआ हो सकता है।",
                "अगला कदम और अनुमानित समय-सीमा बताएं।",
            ],
        },
        "hinglish": {
            "Merchant settlement not credited": [
                "Please affected customer payments ka settlement status aur Captured status confirm karein.",
                "Settlement ID, scheduled settlement date aur Processed hone par UTR share karein.",
                "Agar settlement Failed ya On hold hai, Dashboard mein dikh raha exact reason aur required action/document batayein.",
                "Agar pehle se support ticket hai, isi request ko usse link karke next update ka time batayein.",
            ],
            "Refund not received": [
                "Please confirm karein ki refund initiate hua hai ya nahi.",
                "Agar initiate hua hai, refund reference aur expected credit date batayein; agar nahi, to batayein kya pending hai.",
                "Agar promised refund time nikal gaya hai, to next step guide karein.",
            ],
            "Failed UPI payment": [
                "Apne records check karke transaction ka final outcome confirm karein.",
                "Agar paise debit hue the, reversal status, available reference aur expected timeline batayein.",
            ],
            "UPI payment pending / recipient not credited": [
                "Confirm karein ki recipient ko amount mila hai ya nahi.",
                "Agar transfer complete nahi hua, reversal process, reference aur expected timeline batayein.",
            ],
            "Duplicate charge": [
                "Charges check karke confirm karein ki duplicate payment hua hai ya nahi.",
                "Agar duplicate confirm hota hai, correction/reversal process aur timeline batayein.",
            ],
            "Incorrect amount": [
                "Apne records mein amount check karke difference explain karein.",
                "Wrong amount correct ya formally dispute karne ka process batayein.",
            ],
            "Order paid but not received": [
                "Order ka latest delivery ya cancellation status confirm karein.",
                "Available delivery/refund option aur expected timeline batayein.",
            ],
            "Suspected fraud or unauthorised transaction": [
                "Please isko urgently review karein aur affected payment method/account ko secure aur report karne ka tareeka batayein.",
                "Official reporting channel aur reference share karein. Main OTP, PIN ya password share nahi karunga/karungi.",
            ],
            "Other payment issue": [
                "Relevant order aur payment records check karke batayein ki kya hua ho sakta hai.",
                "Next action aur expected timeline share karein.",
            ],
        },
    }
    status_labels = {
        "en": {"failed": "Failed", "pending": "Pending", "successful": "Successful", "refund_pending": "Refund pending", "unauthorized": "Not recognised by me"},
        "hi": {"failed": "असफल", "pending": "लंबित", "successful": "सफल", "refund_pending": "रिफंड लंबित", "unauthorized": "मेरी पहचान में नहीं है"},
        "hinglish": {"failed": "Failed", "pending": "Pending", "successful": "Successful", "refund_pending": "Refund pending", "unauthorized": "Mujhe ye payment pehchaan mein nahi aata"},
    }
    langs = {
        "en": {
            "subject_label": "Subject",
            "subject": f"Request to review {summaries['en'].get(issue, summaries['en']['Other payment issue'])}",
            "greeting": f"Hello {merchant} Support Team," if merchant else "Hello Support Team,",
            "opening": f"I’m requesting help with {summaries['en'].get(issue, summaries['en']['Other payment issue'])}.",
            "details": "Details I can provide:", "amount": "Amount at issue", "date": "Payment date", "status": "Status shown in the app", "contacted_yes": "I have contacted support already", "contacted_no": "I have not contacted support yet", "description": "My original description (unchanged)", "request": "Could you please:", "reference": "Please share a support/reference number for this request.", "closing": "Thank you.", "amount_unknown": None,
        },
        "hi": {
            "subject_label": "विषय",
            "subject": f"{summaries['hi'].get(issue, summaries['hi']['Other payment issue'])} की जाँच का अनुरोध",
            "greeting": f"नमस्ते {merchant} सहायता टीम," if merchant else "नमस्ते सहायता टीम,",
            "opening": f"मुझे {summaries['hi'].get(issue, summaries['hi']['Other payment issue'])} के बारे में सहायता चाहिए।",
            "details": "मेरे पास उपलब्ध जानकारी:", "amount": "राशि", "date": "भुगतान की तारीख", "status": "ऐप में दिखाई गई स्थिति", "contacted_yes": "मैंने पहले सहायता से संपर्क किया है", "contacted_no": "मैंने अभी तक सहायता से संपर्क नहीं किया है", "description": "मेरा मूल विवरण (बिना बदले)", "request": "मेरा अनुरोध है:", "reference": "इस अनुरोध का सहायता/शिकायत संदर्भ नंबर दें।", "closing": "धन्यवाद।", "amount_unknown": None,
        },
        "hinglish": {
            "subject_label": "Subject",
            "subject": f"{summaries['hinglish'].get(issue, summaries['hinglish']['Other payment issue'])} ko review karne ki request",
            "greeting": f"Namaste {merchant} Support Team," if merchant else "Namaste Support Team,",
            "opening": f"Mujhe {summaries['hinglish'].get(issue, summaries['hinglish']['Other payment issue'])} mein help chahiye.",
            "details": "Mere paas available details:", "amount": "Amount", "date": "Payment date", "status": "App mein dikh raha status", "contacted_yes": "Maine pehle support se contact kiya hai", "contacted_no": "Maine abhi tak support se contact nahi kiya hai", "description": "Mera original description (unchanged)", "request": "Meri request hai:", "reference": "Is request ka support/reference number share karein.", "closing": "Dhanyavaad.", "amount_unknown": None,
        },
    }
    t = langs[language]
    actual_actions = actions[language].get(issue, actions[language]["Other payment issue"])
    subject = f"{t['subject']} — {merchant}" if merchant else t["subject"]
    lines = [f"{t['subject_label']}: {subject}", "", t["greeting"], "", t["opening"]]
    known_facts: list[str] = []
    if amount:
        known_facts.append(f"{t['amount']}: {amount}")
    if payment_date:
        known_facts.append(f"{t['date']}: {payment_date}")
    if payment_status in status_labels[language]:
        known_facts.append(f"{t['status']}: {status_labels[language][payment_status]}")
    if contacted_support is True:
        known_facts.append(t["contacted_yes"])
    elif contacted_support is False:
        known_facts.append(t["contacted_no"])
    if known_facts:
        lines.extend(["", t["details"], *[f"• {item}" for item in known_facts]])
    if description:
        lines.extend(["", f"{t['description']}:", f"“{description}”"])
    lines.extend(["", t["request"], *[f"• {action}" for action in actual_actions], f"• {t['reference']}", "", t["closing"]])
    return "\n".join(lines)


@app.post("/api/cases/{case_id}/draft")
def create_support_draft(case_id: str, request: DraftRequest):
    case_id = case_id.upper()
    with get_db() as con:
        case = case_bundle(con, case_id)
        draft = make_support_draft(case, request.language)
        created = now_iso()
        con.execute("UPDATE cases SET support_draft = ?, updated_at = ?, status = ? WHERE case_id = ?", (draft, created, "Support draft ready", case_id))
        con.execute(
            "INSERT INTO timeline (event_id, case_id, event_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, case_id, "draft", "A support message draft was prepared for user review. It has not been sent.", created),
        )
        return case_bundle(con, case_id)


@app.put("/api/cases/{case_id}/draft")
def update_support_draft(case_id: str, request: DraftEditRequest):
    normalized_id = case_id.upper()
    clean = scrub_sensitive_text(request.text.strip())
    if len(clean.text) < 1:
        raise HTTPException(status_code=422, detail="Add a message before saving the draft.")
    created = now_iso()
    with get_db() as con:
        require_case_access(con, normalized_id)
        con.execute(
            "UPDATE cases SET support_draft = ?, updated_at = ?, status = ? WHERE case_id = ?",
            (clean.text, created, "Support draft edited", normalized_id),
        )
        message = "The user edited and saved the support message draft. It has not been sent."
        if clean.redacted_types:
            message += " Sensitive-looking values were redacted: " + ", ".join(clean.redacted_types) + "."
        con.execute(
            "INSERT INTO timeline (event_id, case_id, event_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, normalized_id, "draft_edited", message, created),
        )
        return case_bundle(con, normalized_id)


@app.post("/api/cases/{case_id}/timeline", status_code=201)
def add_timeline_note(case_id: str, request: TimelineCreate):
    case_id = case_id.upper()
    created = now_iso()
    safe_note = scrub_sensitive_text(request.message.strip())
    note_message = "User note: " + safe_note.text
    if safe_note.redacted_types:
        note_message += " [Sensitive-looking values redacted: " + ", ".join(safe_note.redacted_types) + ".]"
    with get_db() as con:
        require_case_access(con, case_id)
        con.execute(
            "INSERT INTO timeline (event_id, case_id, event_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, case_id, "user_note", note_message, created),
        )
        con.execute("UPDATE cases SET updated_at = ? WHERE case_id = ?", (created, case_id))
        return case_bundle(con, case_id)


@app.patch("/api/cases/{case_id}/progress")
def update_case_progress(case_id: str, request: CaseProgressUpdate):
    case_id = case_id.upper()
    created = now_iso()
    raw_note = request.note.strip()
    safe_note = scrub_sensitive_text(raw_note)
    note = safe_note.text
    if len(note) > 500:
        raise HTTPException(status_code=400, detail="Status note must be 500 characters or fewer.")
    if request.case_stage == "Resolved (user-reported)":
        message = "User marked this case resolved. This status is self-reported and has not been independently verified."
    else:
        message = f"User updated case progress to: {request.case_stage}. This is self-reported."
    if note:
        message += f" Note: {note}"
    if safe_note.redacted_types:
        message += " Sensitive-looking values redacted: " + ", ".join(safe_note.redacted_types) + "."
    with get_db() as con:
        require_case_access(con, case_id)
        con.execute("UPDATE cases SET case_stage = ?, updated_at = ? WHERE case_id = ?", (request.case_stage, created, case_id))
        con.execute(
            "INSERT INTO timeline (event_id, case_id, event_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, case_id, "progress", message, created),
        )
        return case_bundle(con, case_id)


@app.get("/api/cases/{case_id}/evidence-bundle.zip")
def download_case_evidence_bundle(
    case_id: str,
    mode: Literal["complete", "share"] = "complete",
    include_evidence: str = "",
    redact_text: bool = False,
):
    """Build a structured case dossier plus original evidence and integrity metadata.

    `complete` includes every available original. `share` includes only explicitly
    selected evidence IDs and may redact obvious sensitive patterns from text files.
    Original files are never modified or redacted by this export endpoint.
    """
    normalized_id = case_id.upper()
    buffer = io.BytesIO()
    with get_db() as con:
        require_case_access(con, normalized_id)
        case = case_bundle(con, normalized_id)
        rows = con.execute(
            "SELECT evidence_id, original_name, stored_name, mime_type, size_bytes, created_at, capture_source, captured_at, session_id, sha256, scan_status FROM evidence WHERE case_id=? ORDER BY created_at, rowid",
            (normalized_id,),
        ).fetchall()
        all_ids = {str(row["evidence_id"]) for row in rows}
        requested_ids = {item.strip() for item in include_evidence.split(",") if item.strip()}
        if mode == "share":
            unknown_ids = requested_ids - all_ids
            if unknown_ids:
                raise HTTPException(status_code=404, detail="One or more selected evidence files are not in this case.")
            selected_ids = requested_ids
        else:
            selected_ids = all_ids
        exported_at = now_iso()
        passport = build_passport_export(case)
        turns = list(case.get("conversation_turns") or [])
        case_timeline = case.get("timeline") or []
        if not turns:
            # Backward-compatible transcript recovery for cases created before the
            # structured conversation_turns table was introduced.
            for event in case_timeline:
                if event.get("event_type") == "live_room_user_turn":
                    turns.append({
                        "speaker": "user", "text": re.sub(r"^User said:\s*", "", str(event.get("message") or "")),
                        "language_code": event.get("metadata", {}).get("language_code", ""),
                        "input_source": event.get("metadata", {}).get("input_source", "legacy_timeline"),
                        "created_at": event.get("created_at", ""), "user_confirmed": True,
                    })
        # The structured table stores user speech and corrections. Assistant guidance
        # and reviewed organisation replies live in the case timeline, so merge those
        # events into the transcript rather than exporting only one side of the chat.
        for event in case_timeline:
            event_type = str(event.get("event_type") or "")
            if event_type == "live_room_agent_guidance":
                message = str(event.get("message") or "")
                message = re.sub(r"^BolKeResolve guidance:\s*", "", message)
                turns.append({
                    "speaker": "assistant", "text": message, "input_source": "case_guidance",
                    "created_at": event.get("created_at", ""), "user_confirmed": False,
                })
            elif event_type == "response_received":
                turns.append({
                    "speaker": "organisation_reply_user_reported", "text": str(event.get("message") or ""),
                    "input_source": "user_confirmed_support_reply",
                    "created_at": event.get("created_at", ""), "user_confirmed": True,
                })
        turns = sorted(turns, key=lambda item: str(item.get("created_at") or ""))
        timeline = sorted(case_timeline, key=lambda item: str(item.get("created_at") or ""))
        evidence_items = [item for item in case.get("evidence", []) if item.get("evidence_id") in selected_ids]

        def export_text(value: object) -> str:
            text_value = str(value or "")
            if mode == "share" and redact_text:
                text_value = scrub_sensitive_text(text_value).text
                # Additional share-export-only patterns: email addresses and standalone
                # Indian mobile numbers. This is best-effort text redaction, not DLP.
                text_value = re.sub(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[REDACTED EMAIL]", text_value)
                text_value = re.sub(r"(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)", "[REDACTED PHONE]", text_value)
            return text_value

        def export_data(value):
            if isinstance(value, str):
                return export_text(value)
            if isinstance(value, list):
                return [export_data(item) for item in value]
            if isinstance(value, dict):
                return {key: export_data(item) for key, item in value.items()}
            return value

        def csv_bytes(headers: list[str], records: list[list[object]]) -> bytes:
            output = io.StringIO(newline="")
            writer = csv.writer(output, lineterminator="\n")
            writer.writerow(headers)
            for record in records:
                safe_row = []
                for cell in record:
                    value = export_text(cell)
                    # Prevent spreadsheet formula execution if a recipient opens a CSV.
                    if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
                        value = "'" + value
                    safe_row.append(value)
                writer.writerow(safe_row)
            return output.getvalue().encode("utf-8-sig")

        def pdf_bytes(title: str, sections: list[tuple[str, list[str]]]) -> bytes:
            """Create simple, portable PDFs; UTF-8 text remains alongside PDFs in ZIP."""
            try:
                from reportlab.lib import colors
                from reportlab.lib.enums import TA_LEFT
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import mm
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
                from xml.sax.saxutils import escape
            except ImportError as exc:
                raise HTTPException(status_code=503, detail="PDF export needs the ReportLab dependency. Install requirements.txt and try again.") from exc

            font_name = "Helvetica"
            font_bold = "Helvetica-Bold"
            font_paths = [
                ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
                ("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
            ]
            for regular_path, bold_path in font_paths:
                if Path(regular_path).is_file() and Path(bold_path).is_file():
                    try:
                        if "BolkeUnicode" not in pdfmetrics.getRegisteredFontNames():
                            pdfmetrics.registerFont(TTFont("BolkeUnicode", regular_path))
                            pdfmetrics.registerFont(TTFont("BolkeUnicode-Bold", bold_path))
                        font_name, font_bold = "BolkeUnicode", "BolkeUnicode-Bold"
                        break
                    except Exception:
                        pass
            style = getSampleStyleSheet()
            style.add(ParagraphStyle(name="BolkeTitle", parent=style["Title"], fontName=font_bold, fontSize=20, leading=25, textColor=colors.HexColor("#174f43"), alignment=TA_LEFT, spaceAfter=8))
            style.add(ParagraphStyle(name="BolkeHeading", parent=style["Heading2"], fontName=font_bold, fontSize=12, leading=16, textColor=colors.HexColor("#174f43"), spaceBefore=12, spaceAfter=5))
            style.add(ParagraphStyle(name="BolkeBody", parent=style["BodyText"], fontName=font_name, fontSize=8.5, leading=12, textColor=colors.HexColor("#263b34"), spaceAfter=4, wordWrap="CJK"))
            style.add(ParagraphStyle(name="BolkeSmall", parent=style["BodyText"], fontName=font_name, fontSize=7, leading=10, textColor=colors.HexColor("#61746b"), spaceAfter=3))
            doc_buffer = io.BytesIO()
            doc = SimpleDocTemplate(doc_buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=17*mm, bottomMargin=17*mm, title=title, author="BolKeResolve")
            story = [Paragraph(escape(title), style["BolkeTitle"]), Paragraph(f"Case {escape(normalized_id)} · Generated {escape(exported_at)} · {escape(mode.title())} export", style["BolkeSmall"]), Spacer(1, 4)]
            for heading, lines in sections:
                story.append(Paragraph(escape(heading), style["BolkeHeading"]))
                for line in lines:
                    value = export_text(line)
                    if not value.strip():
                        continue
                    story.append(Paragraph(escape(value).replace("\n", "<br/>"), style["BolkeBody"]))
            story.append(Spacer(1, 8))
            story.append(Paragraph("This is a user-assembled case record. User statements, AI-generated observations and uploaded records are labelled by source. BolKeResolve does not certify legal admissibility or independently verify the underlying transaction.", style["BolkeSmall"]))
            def footer(canvas, _doc):
                canvas.saveState(); canvas.setFont(font_name, 7); canvas.setFillColor(colors.HexColor("#718078"))
                canvas.drawString(18*mm, 10*mm, "BolKeResolve · Private case export")
                canvas.drawRightString(A4[0]-18*mm, 10*mm, f"Page {_doc.page}")
                canvas.restoreState()
            doc.build(story, onFirstPage=footer, onLaterPages=footer)
            return doc_buffer.getvalue()

        amount_label = f"INR {float(case['amount']):,.2f}" if case.get("amount") is not None else "Not provided"
        summary_sections = [
            ("Case overview", [
                f"Issue: {case.get('issue_type') or 'Not provided'}",
                f"Organisation: {case.get('merchant') or 'Not provided'}",
                f"Amount: {amount_label}",
                f"Progress: {case.get('case_stage') or 'Needs next step'}",
                f"Created: {case.get('created_at') or ''} · Updated: {case.get('updated_at') or ''}",
                f"Problem story (user-reported): {case.get('description') or 'Not provided'}",
            ]),
            ("Current next action", [str((case.get("action_pack") or {}).get("first_action") or "Review the current case plan.")]),
            ("Evidence included", [f"{item.get('original_name')} · {item.get('mime_type')} · {item.get('verification_status', 'Not independently verified')}" for item in evidence_items] or ["No original evidence files were selected for this export."]),
        ]
        timeline_sections = [(str(event.get("created_at") or "Event"), [
            f"{str(event.get('event_type') or 'Update').replace('_',' ').title()} · {event.get('actor') or 'system'} · {event.get('channel') or 'web'}",
            export_text(event.get("message") or ""),
        ]) for event in timeline]
        transcript_sections = [(f"{turn.get('created_at') or 'Time not recorded'} · {str(turn.get('speaker') or 'user').title()} · {turn.get('input_source') or 'recorded'}", [str(turn.get("text") or "")]) for turn in turns]
        summary_pdf = pdf_bytes("BolKeResolve Case Summary", summary_sections)
        timeline_pdf = pdf_bytes("BolKeResolve Case Timeline", timeline_sections or [("Timeline", ["No timeline events were recorded."])])
        transcript_pdf = pdf_bytes("BolKeResolve Conversation Transcript", transcript_sections or [("Conversation", ["No structured conversation turns were recorded."])])

        evidence_index_rows = []
        manifest_items = []
        archive_entries: dict[str, bytes] = {}
        for index, row in enumerate(rows, start=1):
            if str(row["evidence_id"]) not in selected_ids:
                continue
            stored_path = UPLOAD_DIR / Path(row["stored_name"]).name
            safe_name = _safe_evidence_export_name(export_text(row["original_name"]))
            kind = "Photos" if str(row["mime_type"]).startswith("image/") else "Audio" if str(row["mime_type"]).startswith("audio/") else "Video" if str(row["mime_type"]).startswith("video/") else "Documents"
            archive_path = f"03-Original-Evidence/{kind}/E-{index:03d}-{safe_name}"
            if not stored_path.is_file():
                manifest_items.append({"exhibit_id": f"E-{index:03d}", "evidence_id": row["evidence_id"], "filename": row["original_name"], "missing_file": True, "included": False})
                evidence_index_rows.append([f"E-{index:03d}", row["evidence_id"], row["original_name"], row["mime_type"], row["size_bytes"], row["created_at"], row["capture_source"], row["scan_status"], "Missing from storage"])
                continue
            file_bytes = stored_path.read_bytes()
            actual_hash = hashlib.sha256(file_bytes).hexdigest()
            manifest_item = {
                "exhibit_id": f"E-{index:03d}", "evidence_id": row["evidence_id"], "archive_path": archive_path,
                "filename": export_text(row["original_name"]), "mime_type": row["mime_type"], "size_bytes": row["size_bytes"],
                "uploaded_at": row["created_at"], "capture_source": row["capture_source"], "captured_at_client": row["captured_at"],
                "session_id": row["session_id"], "sha256": actual_hash, "scan_status": row["scan_status"],
                "authenticity_verified": False, "original_included": True,
            }
            manifest_items.append(manifest_item)
            archive_entries[archive_path] = file_bytes
            evidence_index_rows.append([f"E-{index:03d}", row["evidence_id"], row["original_name"], row["mime_type"], row["size_bytes"], row["created_at"], row["capture_source"], row["scan_status"], "Original included"])

        # Text exports preserve the complete Unicode transcript. PDFs are a readable
        # companion; transcript.txt remains the lossless text representation.
        transcript_lines: list[str] = []
        for turn in turns:
            transcript_lines.extend([
                f"{turn.get('created_at') or 'Time not recorded'} | {str(turn.get('speaker') or 'user').upper()} | {turn.get('input_source') or 'recorded'}",
                export_text(turn.get("text") or ""),
                f"User-confirmed: {'yes' if turn.get('user_confirmed') else 'no'}",
                f"Supersedes turn: {turn.get('supersedes_turn_id') or 'none'}",
                "",
            ])
        transcript_text = "\n".join(transcript_lines).strip() + ("\n" if transcript_lines else "")
        event_rows = [[e.get("created_at", ""), e.get("event_type", ""), e.get("actor", "system"), e.get("channel", "web"), e.get("source", "bolkeresolve"), e.get("message", "")] for e in timeline]
        confirmed_facts = [item for item in (case.get("evidence_fact_sources") or [])]
        confirmed_fact_rows = [[item.get("field_key", ""), json.dumps(item.get("value"), ensure_ascii=False), item.get("original_name", ""), item.get("source_label", ""), item.get("applied_to_case", False), item.get("confirmed_at", "")] for item in confirmed_facts]
        disputed_rows = [[item.get("fact_key", ""), json.dumps(item.get("value"), ensure_ascii=False), item.get("source_type", ""), item.get("confidence", ""), item.get("is_current", False), item.get("created_at", ""), item.get("source_excerpt_redacted", "")] for item in (case.get("fact_ledger") or []) if not item.get("is_current") or str(item.get("confidence", "")).lower() in {"low", "disputed"}]
        passport_json = json.dumps(export_data(passport), ensure_ascii=False, indent=2).encode("utf-8")
        case_facts_json = json.dumps(export_data({
            "case_id": normalized_id, "fact_provenance": case.get("fact_provenance", []),
            "fact_history": case.get("fact_ledger", []), "document_fact_sources": confirmed_facts,
            "notice": "Current and historical facts retain provenance. AI suggestions are not independent verification.",
        }), ensure_ascii=False, indent=2).encode("utf-8")
        timeline_csv = csv_bytes(["created_at", "event_type", "actor", "channel", "source", "message"], event_rows)
        evidence_csv = csv_bytes(["exhibit_id", "evidence_id", "original_filename", "mime_type", "size_bytes", "uploaded_at", "capture_source", "scan_status", "export_status"], evidence_index_rows)
        confirmed_csv = csv_bytes(["field", "value_json", "source_file", "source_label", "applied_to_case", "confirmed_at"], confirmed_fact_rows)
        disputed_csv = csv_bytes(["fact_key", "value_json", "source_type", "confidence", "is_current", "created_at", "source_excerpt_redacted"], disputed_rows)
        transcript_bytes = export_text(transcript_text).encode("utf-8")
        support_draft = str(case.get("support_draft") or "")
        if support_draft:
            archive_entries["01-Case-History/Support-Message-DRAFT-ONLY.txt"] = ("DRAFT ONLY — this message is not evidence that a message was sent.\n\n" + export_text(support_draft)).encode("utf-8")

        for item in evidence_items:
            derivatives = item.get("derivatives") or []
            if derivatives:
                derivative_name = _safe_evidence_export_name(export_text(item.get("original_name") or item.get("evidence_id")))
                archive_entries[f"04-Derivatives/{item.get('evidence_id')}-{derivative_name}.json"] = json.dumps(export_data(derivatives), ensure_ascii=False, indent=2).encode("utf-8")

        export_manifest = {
            "format": "bolkeresolve-case-export", "version": "2.0", "case_id": normalized_id,
            "mode": mode, "generated_at": exported_at, "text_redaction_requested": bool(mode == "share" and redact_text),
            "original_evidence_redacted": False,
            "notice": "This is a user-assembled case record, not a certified legal record. SHA-256 hashes identify exported bytes and do not establish origin, capture time, authorship or truth. Original evidence is never modified by report redaction.",
            "conversation_turns": len(turns), "timeline_events": len(timeline), "included_evidence": manifest_items,
            "support_message_status": "draft_not_sent" if support_draft else "none_recorded",
        }
        # Keep the legacy paths for existing integrations and older users.
        archive_entries["case/Resolution-Passport.json"] = passport_json
        archive_entries["00-Readme/Case-Summary.pdf"] = summary_pdf
        archive_entries["00-Readme/Export-Manifest.json"] = json.dumps(export_manifest, ensure_ascii=False, indent=2).encode("utf-8")
        archive_entries["00-Readme/Evidence-Index.csv"] = evidence_csv
        archive_entries["00-Readme/Case-Facts.json"] = case_facts_json
        archive_entries["01-Case-History/Timeline.pdf"] = timeline_pdf
        archive_entries["01-Case-History/Case-Events.csv"] = timeline_csv
        archive_entries["01-Case-History/Confirmed-Facts.csv"] = confirmed_csv
        archive_entries["01-Case-History/Superseded-or-Disputed-Facts.csv"] = disputed_csv
        archive_entries["02-Conversation/Conversation-Transcript.pdf"] = transcript_pdf
        archive_entries["02-Conversation/Conversation-Transcript.txt"] = transcript_bytes
        archive_entries["evidence/manifest.json"] = json.dumps({"case_id": normalized_id, "generated_at": exported_at, "notice": export_manifest["notice"], "exhibits": manifest_items}, ensure_ascii=False, indent=2).encode("utf-8")
        # Hash every payload placed in the archive (except the hash list itself and
        # manifest, which necessarily describe the rest of the package).
        hash_lines = [f"{hashlib.sha256(payload).hexdigest()}  {name}" for name, payload in sorted(archive_entries.items()) if name not in {"00-Readme/File-Hashes-SHA256.txt", "00-Readme/Export-Manifest.json", "evidence/manifest.json"}]
        archive_entries["00-Readme/File-Hashes-SHA256.txt"] = ("SHA-256 hashes identify bytes in this export; they do not prove authenticity.\n" + "\n".join(hash_lines) + "\n").encode("utf-8")
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for archive_path, payload in archive_entries.items():
                archive.writestr(archive_path, payload)
        filename = f"BolKeResolve-{normalized_id}-{'share' if mode == 'share' else 'complete'}-case.zip"
        package_hash = hashlib.sha256(buffer.getvalue()).hexdigest()
        manifest_hash = hashlib.sha256(archive_entries["00-Readme/Export-Manifest.json"]).hexdigest()
        export_id = uuid.uuid4().hex
        included_evidence_ids = sorted(selected_ids)
        con.execute(
            "INSERT INTO case_exports (export_id, case_id, user_id, export_mode, included_evidence_json, redaction_requested, manifest_sha256, package_sha256, package_filename, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (export_id, normalized_id, CURRENT_USER_ID.get(), mode, json.dumps(included_evidence_ids), int(bool(mode == "share" and redact_text)), manifest_hash, package_hash, filename, exported_at),
        )
        record_case_event(
            con, normalized_id, "case_export_created",
            f"A {mode} case export was generated with {len(included_evidence_ids)} original evidence file(s).",
            exported_at, actor="user", channel="web", source="case_export",
            metadata={"export_id": export_id, "mode": mode, "included_evidence_ids": included_evidence_ids, "text_redaction_requested": bool(mode == "share" and redact_text), "package_sha256": package_hash},
        )
        record_audit_event(con, "case_export_created", case_id=normalized_id, target_type="case_export", target_id=export_id, metadata={"mode": mode, "evidence_count": len(included_evidence_ids), "redaction_requested": bool(mode == "share" and redact_text), "package_sha256": package_hash})
    filename = f"BolKeResolve-{normalized_id}-{'share' if mode == 'share' else 'complete'}-case.zip"
    return Response(content=buffer.getvalue(), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"})

def _safe_evidence_export_name(value: str) -> str:
    name = Path(str(value or "evidence")).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")[:100]
    return name or "evidence"


@app.get("/api/cases/{case_id}/evidence/{evidence_id}")
def fetch_evidence(case_id: str, evidence_id: str, inline: bool = False):
    with get_db() as con:
        require_case_access(con, case_id.upper())
        row = con.execute(
            "SELECT stored_name, original_name, mime_type FROM evidence WHERE case_id = ? AND evidence_id = ?",
            (case_id.upper(), evidence_id),
        ).fetchone()
        if row:
            event_type = "evidence_previewed" if inline else "evidence_downloaded"
            record_case_event(
                con, case_id.upper(), event_type,
                "The user opened an evidence preview." if inline else "The user downloaded an original evidence file.",
                actor="user", channel="web", source="evidence_library", metadata={"evidence_id": evidence_id, "filename": row["original_name"], "original_unchanged": True},
            )
            record_audit_event(con, event_type, case_id=case_id.upper(), target_type="evidence", target_id=evidence_id, metadata={"inline": bool(inline), "mime_type": row["mime_type"]})
    if not row:
        raise HTTPException(status_code=404, detail="Evidence not found")
    path = UPLOAD_DIR / row["stored_name"]
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Evidence file is missing")
    return FileResponse(
        path,
        media_type=row["mime_type"],
        filename=row["original_name"],
        content_disposition_type="inline" if inline else "attachment",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


# Static frontend is mounted last so /api routes remain available.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
