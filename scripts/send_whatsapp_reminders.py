"""Send due, opted-in WhatsApp follow-up reminders through approved templates.

Run this script daily from Windows Task Scheduler or a server cron. It does not
run a persistent background loop. Messages are sent only if the official Cloud
API is fully configured, a template name is configured, the contact opted in,
and Meta accepts the template message.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import main as app_service  # noqa: E402
from backend import whatsapp as whatsapp_service  # noqa: E402


def claim_reminder(case_id: str, followup_stamp: str) -> bool:
    """Atomically claim a reminder so overlapping scheduler runs don't send duplicates."""
    now_epoch = int(time.time())
    stamp = app_service.now_iso()
    with app_service.get_db() as con:
        con.execute("BEGIN IMMEDIATE")
        followup = con.execute(
            "SELECT updated_at, completed, reminder_sent_for FROM case_followups WHERE case_id=?",
            (case_id,),
        ).fetchone()
        if not followup or followup["updated_at"] != followup_stamp or followup["completed"] or followup["reminder_sent_for"] == followup_stamp:
            return False
        claim = con.execute(
            "SELECT status, lease_until, attempts FROM reminder_delivery_claims WHERE case_id=? AND followup_updated_at=?",
            (case_id, followup_stamp),
        ).fetchone()
        if claim and claim["status"] == "accepted":
            return False
        if claim and claim["status"] == "sending" and int(claim["lease_until"] or 0) > now_epoch:
            return False
        if claim:
            con.execute(
                "UPDATE reminder_delivery_claims SET status='sending', lease_until=?, attempts=attempts+1, updated_at=?, last_error_type='' WHERE case_id=? AND followup_updated_at=?",
                (now_epoch + 300, stamp, case_id, followup_stamp),
            )
        else:
            con.execute(
                "INSERT INTO reminder_delivery_claims (case_id, followup_updated_at, status, lease_until, attempts, updated_at, last_error_type) VALUES (?, ?, 'sending', ?, 1, ?, '')",
                (case_id, followup_stamp, now_epoch + 300, stamp),
            )
    return True


async def send_due_reminders() -> tuple[int, int]:
    # Phase 1 Twilio Sandbox is a text-only test channel; scheduled reminders
    # remain Meta-template-only until a compliant provider-template abstraction exists.
    if app_service.messaging_service.selected_provider() == "twilio":
        print("Skipped: BOLKE_WHATSAPP_PROVIDER=twilio; scheduled reminders are disabled for the Twilio Sandbox adapter.")
        return 0, 0
    template_name = os.getenv("WHATSAPP_REMINDER_TEMPLATE_NAME", "").strip()
    language = os.getenv("WHATSAPP_REMINDER_TEMPLATE_LANGUAGE", "en_US").strip() or "en_US"
    config = whatsapp_service.config_status()
    if not config["cloud_api_ready"] or not template_name:
        print("Skipped: live WhatsApp messaging and an approved reminder template are not both configured.")
        return 0, 0

    # Use an explicit business timezone; container/server local time is often UTC.
    timezone_name = os.getenv("BOLKE_TIMEZONE", "Asia/Kolkata").strip() or "Asia/Kolkata"
    try:
        business_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        print("Invalid BOLKE_TIMEZONE; falling back to Asia/Kolkata.")
        business_timezone = ZoneInfo("Asia/Kolkata")
    today = datetime.now(business_timezone).date().isoformat()

    # Snapshot identifiers and timestamps first. One follow-up row represents one due reminder.
    with app_service.get_db() as con:
        due_rows = con.execute(
            "SELECT f.case_id, f.due_date, f.note, f.updated_at AS followup_updated_at, "
            "c.issue_type, c.case_stage, l.phone_hash, p.phone_ciphertext "
            "FROM case_followups f JOIN cases c ON c.case_id = f.case_id "
            "JOIN whatsapp_case_links l ON l.case_id = c.case_id "
            "JOIN whatsapp_contacts p ON p.phone_hash = l.phone_hash "
            "WHERE f.due_date <> '' AND f.due_date <= ? "
            "AND f.completed = 0 AND f.reminder_sent_for <> f.updated_at "
            "AND p.enabled = 1 AND p.consent_at <> '' "
            "AND l.created_at = (SELECT MAX(l2.created_at) FROM whatsapp_case_links l2 WHERE l2.case_id = c.case_id) "
            "ORDER BY f.due_date ASC LIMIT 100",
            (today,),
        ).fetchall()

    sent = failed = 0
    for item in due_rows:
        case_id = item["case_id"]
        followup_stamp = item["followup_updated_at"]
        if not claim_reminder(case_id, followup_stamp):
            continue
        try:
            phone = whatsapp_service.decrypt_phone(item["phone_ciphertext"])
            response = await whatsapp_service.send_template_message(
                phone,
                template_name,
                language,
                [case_id, item["due_date"]],
            )
            accepted_at = app_service.now_iso()
            with app_service.get_db() as con:
                current = con.execute(
                    "SELECT updated_at, completed, reminder_sent_for FROM case_followups WHERE case_id = ?",
                    (case_id,),
                ).fetchone()
                # Do not mark a reminder sent if the user edited or completed it while the message was in flight.
                con.execute(
                    "UPDATE reminder_delivery_claims SET status='accepted', lease_until=0, updated_at=?, last_error_type='' WHERE case_id=? AND followup_updated_at=?",
                    (accepted_at, case_id, followup_stamp),
                )
                message_id = str(response.get("message_id", ""))[:180]
                if message_id:
                    con.execute(
                        "INSERT OR IGNORE INTO whatsapp_outbound_messages (message_id, case_id, purpose, status, created_at, updated_at, error_code) VALUES (?, ?, 'reminder', 'accepted', ?, ?, '')",
                        (message_id, case_id, accepted_at, accepted_at),
                    )
                if current and current["updated_at"] == followup_stamp and not current["completed"] and current["reminder_sent_for"] != followup_stamp:
                    con.execute(
                        "UPDATE case_followups SET reminder_sent_for = ? WHERE case_id = ? AND updated_at = ?",
                        (followup_stamp, case_id, followup_stamp),
                    )
                    app_service.record_case_event(
                        con,
                        case_id,
                        "reminder_sent",
                        "A WhatsApp follow-up reminder was accepted by the Cloud API. Delivery is not independently confirmed.",
                        accepted_at,
                        actor="system",
                        channel="whatsapp",
                        source="cloud_api_template",
                        metadata={"template": template_name, "message_id": message_id, "api_accepted": True},
                    )
            sent += 1
        except Exception as exc:  # avoid logging contact data or message payloads
            failed += 1
            with app_service.get_db() as con:
                con.execute(
                    "UPDATE reminder_delivery_claims SET status='failed', lease_until=0, updated_at=?, last_error_type=? WHERE case_id=? AND followup_updated_at=? AND status='sending'",
                    (app_service.now_iso(), type(exc).__name__[:80], case_id, followup_stamp),
                )
            print(f"Reminder for case {case_id} failed ({type(exc).__name__}).")
    print(f"Reminder run complete: {sent} accepted, {failed} failed.")
    return sent, failed


def main() -> int:
    accepted, failed = asyncio.run(send_due_reminders())
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
