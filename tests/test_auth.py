import os
import tempfile
import unittest
import uuid
from unittest.mock import patch

# Keep the auth/database tests entirely separate from any local runtime data.
_AUTH_TEST_DATA = tempfile.TemporaryDirectory(prefix="bolke-auth-test-")
os.environ["BOLKE_DATA_DIR"] = _AUTH_TEST_DATA.name

from fastapi.testclient import TestClient  # noqa: E402
from backend import main  # noqa: E402


CASE_PAYLOAD = {
    "issue_type": "Failed UPI payment",
    "merchant": "Synthetic Demo Merchant",
    "amount": 250,
    "payment_date": "2026-10-16",
    "language_code": "hi-IN",
    "payment_status": "failed",
    "contacted_support": False,
    "description": "Synthetic test: UPI payment failed and the demo amount was debited.",
}


class AuthenticationIsolationTests(unittest.TestCase):
    def setUp(self):
        self.auth_was_required = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = True
        with main.get_db() as con:
            con.execute("DELETE FROM auth_rate_limit_attempts")
        self.client = TestClient(main.app)

    def tearDown(self):
        self.client.close()
        main.AUTH_REQUIRED = self.auth_was_required

    def register(self, client, label):
        email = f"{label}-{uuid.uuid4().hex[:8]}@example.test"
        response = client.post("/api/auth/register", json={"email": email, "password": "Synthetic-demo-pass-2026"}, headers={"Origin": "http://testserver"})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertTrue(response.cookies.get(main.SESSION_COOKIE_NAME))
        return email


    def test_accounts_are_available_in_development_when_login_is_optional(self):
        """The header sign-in path works locally without making all guest previews private."""
        main.AUTH_REQUIRED = False
        first = TestClient(main.app)
        second = TestClient(main.app)
        guest = TestClient(main.app)
        try:
            first_email = self.register(first, "optional-first")
            second_email = self.register(second, "optional-second")
            first_me = first.get("/api/auth/me").json()
            self.assertFalse(first_me["auth_required"])
            self.assertTrue(first_me["accounts_enabled"])
            self.assertEqual(first_me["user"]["email"], first_email)
            self.assertNotEqual(first_email, second_email)

            first_case = first.post("/api/cases", json=CASE_PAYLOAD)
            second_case = second.post("/api/cases", json=CASE_PAYLOAD)
            guest_case = guest.post("/api/cases", json=CASE_PAYLOAD)
            self.assertEqual(first_case.status_code, 201, first_case.text)
            self.assertEqual(second_case.status_code, 201, second_case.text)
            self.assertEqual(guest_case.status_code, 201, guest_case.text)

            first_id = first_case.json()["case_id"]
            second_id = second_case.json()["case_id"]
            guest_id = guest_case.json()["case_id"]
            first_case_ids = {row["case_id"] for row in first.get("/api/cases").json()}
            second_case_ids = {row["case_id"] for row in second.get("/api/cases").json()}
            guest_case_ids = {row["case_id"] for row in guest.get("/api/cases").json()}
            self.assertIn(first_id, first_case_ids)
            self.assertNotIn(second_id, first_case_ids)
            self.assertNotIn(guest_id, first_case_ids)
            self.assertIn(second_id, second_case_ids)
            self.assertNotIn(first_id, second_case_ids)
            self.assertNotIn(guest_id, second_case_ids)
            self.assertIn(guest_id, guest_case_ids)
            self.assertNotIn(first_id, guest_case_ids)
            self.assertNotIn(second_id, guest_case_ids)
            self.assertEqual(first.get(f"/api/cases/{second_id}").status_code, 404)
            self.assertEqual(first.get(f"/api/cases/{guest_id}").status_code, 404)
            self.assertEqual(guest.get(f"/api/cases/{first_id}").status_code, 404)

            # Logging out returns to the guest workspace without retaining account access.
            first.post("/api/auth/logout")
            after_logout_ids = {row["case_id"] for row in first.get("/api/cases").json()}
            self.assertIn(guest_id, after_logout_ids)
            self.assertNotIn(first_id, after_logout_ids)
            self.assertNotIn(second_id, after_logout_ids)
        finally:
            first.close(); second.close(); guest.close()

    def test_private_api_requires_session(self):
        response = self.client.get("/api/cases")
        self.assertEqual(response.status_code, 401)
        email = self.register(self.client, "owner")
        me = self.client.get("/api/auth/me").json()
        self.assertEqual(me["user"]["email"], email)
        self.assertTrue(me["user"]["email_verified"])
        cookie = self.client.cookies.get(main.SESSION_COOKIE_NAME)
        self.assertTrue(cookie)

    def test_cases_are_isolated_between_accounts(self):
        owner_email = self.register(self.client, "first")
        created = self.client.post("/api/cases", json=CASE_PAYLOAD, headers={"Origin": "http://testserver"})
        self.assertEqual(created.status_code, 201, created.text)
        case_id = created.json()["case_id"]
        self.assertNotIn("owner_id", created.json(), "internal ownership metadata must not be exposed to the browser")

        other = TestClient(main.app)
        try:
            other_email = self.register(other, "second")
            self.assertNotEqual(owner_email, other_email)
            self.assertEqual(other.get("/api/cases").status_code, 200)
            self.assertEqual(other.get("/api/cases").json(), [])
            self.assertEqual(other.get(f"/api/cases/{case_id}").status_code, 404)
            self.assertEqual(other.post(f"/api/cases/{case_id}/timeline", json={"message": "attempt to access other user's case"}, headers={"Origin": "http://testserver"}).status_code, 404)
            self.assertEqual(other.delete(f"/api/cases/{case_id}", headers={"Origin": "http://testserver"}).status_code, 404)
            self.assertEqual(self.client.get(f"/api/cases/{case_id}").status_code, 200, "another account must not delete the owner's case")
        finally:
            other.close()

    def test_logout_revokes_session_and_login_restores_access(self):
        email = self.register(self.client, "login")
        create_response = self.client.post("/api/cases", json=CASE_PAYLOAD, headers={"Origin": "http://testserver"})
        self.assertEqual(create_response.status_code, 201, create_response.text)
        logout = self.client.post("/api/auth/logout", headers={"Origin": "http://testserver"})
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(self.client.get("/api/cases").status_code, 401)
        login = self.client.post("/api/auth/login", json={"email": email, "password": "Synthetic-demo-pass-2026"}, headers={"Origin": "http://testserver"})
        self.assertEqual(login.status_code, 200, login.text)
        self.assertEqual(len(self.client.get("/api/cases").json()), 1)

    def test_secure_cookie_flag_is_set_when_secure_cookies_are_enabled(self):
        previous = main.COOKIE_SECURE
        main.COOKIE_SECURE = True
        try:
            response = self.client.post("/api/auth/register", json={"email": f"secure-{uuid.uuid4().hex[:8]}@example.test", "password": "Synthetic-demo-pass-2026"}, headers={"Origin": "http://testserver"})
            self.assertEqual(response.status_code, 201, response.text)
            self.assertIn("Secure", response.headers.get("set-cookie", ""))
            self.assertIn("HttpOnly", response.headers.get("set-cookie", ""))
            self.assertIn("SameSite=lax", response.headers.get("set-cookie", ""))
        finally:
            main.COOKIE_SECURE = previous

    def test_exact_preview_origin_allowlist_does_not_open_wildcard_origins(self):
        with patch.dict(os.environ, {
            "BOLKE_PUBLIC_ORIGIN": "https://bolkeresolve.vercel.app",
            "BOLKE_ALLOWED_ORIGINS": "https://bolkeresolve-preview.vercel.app, https://staging.bolkeresolve.example",
        }):
            allowed = self.client.post(
                "/api/auth/register",
                json={"email": f"preview-{uuid.uuid4().hex[:8]}@example.test", "password": "Synthetic-demo-pass-2026"},
                headers={"Origin": "https://bolkeresolve-preview.vercel.app"},
            )
            self.assertEqual(allowed.status_code, 201, allowed.text)
            rejected = self.client.post(
                "/api/auth/register",
                json={"email": f"attacker-{uuid.uuid4().hex[:8]}@example.test", "password": "Synthetic-demo-pass-2026"},
                headers={"Origin": "https://random-preview.vercel.app"},
            )
            self.assertEqual(rejected.status_code, 403)

    def test_mutating_api_rejects_cross_origin_request(self):
        response = self.client.post(
            "/api/auth/register",
            json={"email": f"csrf-{uuid.uuid4().hex[:8]}@example.test", "password": "Synthetic-demo-pass-2026"},
            headers={"Origin": "https://attacker.example"},
        )
        self.assertEqual(response.status_code, 403)

    def test_unknown_auth_namespace_path_is_not_public(self):
        response = self.client.get("/api/auth/unimplemented-private-route")
        self.assertEqual(response.status_code, 401)

    def test_mutating_authenticated_request_requires_origin_header(self):
        response = self.client.post(
            "/api/auth/register",
            json={"email": f"missing-origin-{uuid.uuid4().hex[:8]}@example.test", "password": "Synthetic-demo-pass-2026"},
        )
        self.assertEqual(response.status_code, 403)

    def test_registration_rejects_short_password(self):
        response = self.client.post("/api/auth/register", json={"email": "shortpass@example.test", "password": "short"}, headers={"Origin": "http://testserver"})
        self.assertEqual(response.status_code, 422)

    def test_passport_exports_are_private_and_case_scoped(self):
        # Export routes must use the same authentication and per-owner access rules as the case API.
        for suffix in ("passport.json", "passport/print"):
            response = self.client.get(f"/api/cases/BR-NOTREAL/{suffix}")
            self.assertEqual(response.status_code, 401, suffix)

        owner_email = self.register(self.client, "passport-owner")
        create_response = self.client.post("/api/cases", json=CASE_PAYLOAD, headers={"Origin": "http://testserver"})
        self.assertEqual(create_response.status_code, 201, create_response.text)
        case_id = create_response.json()["case_id"]

        other = TestClient(main.app)
        try:
            self.register(other, "passport-other")
            self.assertEqual(other.get(f"/api/cases/{case_id}/passport.json").status_code, 404)
            self.assertEqual(other.get(f"/api/cases/{case_id}/passport/print").status_code, 404)
            self.assertEqual(other.put(f"/api/cases/{case_id}/outcome", json={"outcome_code": "resolved", "details": "", "reference": ""}, headers={"Origin": "http://testserver"}).status_code, 404)
            self.assertEqual(self.client.get(f"/api/cases/{case_id}/passport.json").status_code, 200)
        finally:
            other.close()

    def test_account_sessions_can_be_reviewed_and_other_sessions_revoked(self):
        email = self.register(self.client, "session-review")
        other = TestClient(main.app)
        try:
            login = other.post("/api/auth/login", json={"email": email, "password": "Synthetic-demo-pass-2026"}, headers={"Origin": "http://testserver"})
            self.assertEqual(login.status_code, 200, login.text)
            sessions = self.client.get("/api/auth/sessions")
            self.assertEqual(sessions.status_code, 200, sessions.text)
            self.assertEqual(sessions.json()["active_sessions"], 2)
            self.assertTrue(any(item["is_current"] for item in sessions.json()["sessions"]))
            revoked = self.client.post("/api/auth/sessions/revoke-others", headers={"Origin": "http://testserver"})
            self.assertEqual(revoked.status_code, 200, revoked.text)
            self.assertEqual(revoked.json()["revoked_sessions"], 1)
            self.assertEqual(other.get("/api/cases").status_code, 401)
        finally:
            other.close()

    def test_password_change_updates_hash_and_invalidates_other_sessions(self):
        email = self.register(self.client, "password-change")
        changed = self.client.post("/api/auth/password", json={
            "current_password": "Synthetic-demo-pass-2026", "new_password": "Synthetic-new-demo-pass-2026"
        }, headers={"Origin": "http://testserver"})
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertIn("Other active sessions", changed.json()["message"])
        with main.get_db() as con:
            user = con.execute("SELECT password_iterations, password_algorithm FROM users WHERE email=?", (email,)).fetchone()
        self.assertEqual(user["password_iterations"], main.PASSWORD_HASH_ITERATIONS)
        self.assertEqual(user["password_algorithm"], "pbkdf2_sha256")
        other = TestClient(main.app)
        try:
            old = other.post("/api/auth/login", json={"email": email, "password": "Synthetic-demo-pass-2026"}, headers={"Origin": "http://testserver"})
            self.assertEqual(old.status_code, 401)
            fresh = other.post("/api/auth/login", json={"email": email, "password": "Synthetic-new-demo-pass-2026"}, headers={"Origin": "http://testserver"})
            self.assertEqual(fresh.status_code, 200, fresh.text)
        finally:
            other.close()

    def test_account_deletion_requires_password_confirmation_and_removes_active_owned_data(self):
        email = self.register(self.client, "delete-account")
        user = self.client.get("/api/auth/me").json()["user"]
        created = self.client.post("/api/cases", json=CASE_PAYLOAD, headers={"Origin": "http://testserver"})
        self.assertEqual(created.status_code, 201, created.text)
        case_id = created.json()["case_id"]

        evidence_name = f"account-delete-{uuid.uuid4().hex}.pdf"
        evidence_path = main.UPLOAD_DIR / evidence_name
        evidence_path.write_bytes(b"%PDF-1.4 synthetic evidence")
        contact_hash = "delete-test-" + uuid.uuid4().hex
        with main.get_db() as con:
            con.execute(
                "INSERT INTO evidence (evidence_id, case_id, original_name, stored_name, mime_type, size_bytes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (uuid.uuid4().hex, case_id, "receipt.pdf", evidence_name, "application/pdf", evidence_path.stat().st_size, main.now_iso()),
            )
            con.execute(
                "INSERT INTO whatsapp_contacts (phone_hash, phone_ciphertext, owner_id, consent_at, enabled, created_at, updated_at) VALUES (?, ?, ?, ?, 1, ?, ?)",
                (contact_hash, "encrypted-test-value", user["user_id"], main.now_iso(), main.now_iso(), main.now_iso()),
            )
            con.execute(
                "INSERT INTO whatsapp_sessions (phone_hash, state, pending_story, active_case_id, updated_at) VALUES (?, 'collecting_story', 'synthetic pending story', ?, ?)",
                (contact_hash, case_id, main.now_iso()),
            )
            con.execute(
                "INSERT INTO whatsapp_webhook_messages (message_id, phone_hash, reply_text, case_id, status, created_at, reply_sent_at, lease_until, attempts, last_error_type) VALUES (?, ?, ?, ?, 'sent', ?, '', 0, 1, '')",
                ("delete-webhook-" + uuid.uuid4().hex, contact_hash, "synthetic private reply content", case_id, main.now_iso()),
            )

        wrong = self.client.request("DELETE", "/api/auth/account", json={"password": "Wrong-password"}, headers={"Origin": "http://testserver"})
        self.assertEqual(wrong.status_code, 403)
        self.assertEqual(self.client.get(f"/api/cases/{case_id}").status_code, 200)
        self.assertTrue(evidence_path.exists())

        deleted = self.client.request("DELETE", "/api/auth/account", json={"password": "Synthetic-demo-pass-2026"}, headers={"Origin": "http://testserver"})
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertTrue(deleted.json()["deleted"])
        self.assertIn("Downloaded/exported copies", deleted.json()["message"])
        self.assertIn("Set-Cookie", deleted.headers)
        self.assertIn("Max-Age=0", deleted.headers["set-cookie"])
        self.assertEqual(self.client.get("/api/auth/me").json()["user"], None)
        self.assertEqual(self.client.get("/api/cases").status_code, 401)
        self.assertFalse(evidence_path.exists())
        with main.get_db() as con:
            self.assertIsNone(con.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone())
            self.assertIsNone(con.execute("SELECT case_id FROM cases WHERE case_id = ?", (case_id,)).fetchone())
            self.assertIsNone(con.execute("SELECT phone_hash FROM whatsapp_contacts WHERE phone_hash = ?", (contact_hash,)).fetchone())
            self.assertIsNone(con.execute("SELECT message_id FROM whatsapp_webhook_messages WHERE phone_hash = ?", (contact_hash,)).fetchone())

    def test_account_deletion_reports_evidence_file_cleanup_failure_truthfully(self):
        self.register(self.client, "delete-cleanup")
        user = self.client.get("/api/auth/me").json()["user"]
        created = self.client.post("/api/cases", json=CASE_PAYLOAD, headers={"Origin": "http://testserver"})
        self.assertEqual(created.status_code, 201, created.text)
        case_id = created.json()["case_id"]
        # A directory at the stored filename forces unlink() to fail without relying on
        # platform-specific permission behavior. It is only synthetic test data.
        stored_name = "cleanup-blocker-" + uuid.uuid4().hex
        blocker_path = main.UPLOAD_DIR / stored_name
        blocker_path.mkdir()
        try:
            with main.get_db() as con:
                con.execute(
                    "INSERT INTO evidence (evidence_id, case_id, original_name, stored_name, mime_type, size_bytes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (uuid.uuid4().hex, case_id, "synthetic.pdf", stored_name, "application/pdf", 0, main.now_iso()),
                )
            response = self.client.request("DELETE", "/api/auth/account", json={"password": "Synthetic-demo-pass-2026"}, headers={"Origin": "http://testserver"})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["evidence_cleanup_pending"], 1)
            self.assertIn("Operator cleanup is required", response.json()["message"])
            with main.get_db() as con:
                self.assertIsNone(con.execute("SELECT user_id FROM users WHERE user_id = ?", (user["user_id"],)).fetchone())
        finally:
            blocker_path.rmdir()

    def test_account_deletion_requires_origin_and_sign_in(self):
        no_session = self.client.request("DELETE", "/api/auth/account", json={"password": "Synthetic-demo-pass-2026"}, headers={"Origin": "http://testserver"})
        self.assertEqual(no_session.status_code, 401)
        self.register(self.client, "delete-origin")
        missing_origin = self.client.request("DELETE", "/api/auth/account", json={"password": "Synthetic-demo-pass-2026"})
        self.assertEqual(missing_origin.status_code, 403)

    def test_api_responses_are_never_cached(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response.headers.get("cache-control", ""))
        self.assertIn("no-cache", response.headers.get("pragma", ""))

    def test_public_preview_works_before_sign_in_but_case_storage_stays_private(self):
        main._PREVIEW_ATTEMPTS.clear()
        headers = {"Origin": "http://testserver"}
        story = "My refund from Synthetic Shop is still pending after the promised date."
        resolution = self.client.post(
            "/api/resolution/preview",
            json={"issue_type": "Refund not received", "merchant": "Synthetic Shop", "description": story},
            headers=headers,
        )
        self.assertEqual(resolution.status_code, 200, resolution.text)
        self.assertIn("recommended_steps", resolution.json())

        extraction = self.client.post("/api/extraction/preview", json={"description": story}, headers=headers)
        self.assertEqual(extraction.status_code, 200, extraction.text)
        self.assertIn("extracted_facts", extraction.json())

        # Preview-only activity must not create a private case as a side effect.
        self.assertEqual(self.client.get("/api/cases").status_code, 401)
        create = self.client.post("/api/cases", json=CASE_PAYLOAD, headers=headers)
        self.assertEqual(create.status_code, 401, "saving must still require a session in authenticated mode")

    def test_public_preview_rate_limit_returns_retry_after(self):
        from starlette.requests import Request
        request = Request({"type": "http", "method": "POST", "path": "/api/resolution/preview", "headers": [], "client": ("preview-limit-test", 1234), "server": ("testserver", 80), "scheme": "http", "query_string": b""})
        key = "limit-test:preview-limit-test"
        main._PREVIEW_ATTEMPTS[key] = [main.time.monotonic()] * 2
        try:
            with self.assertRaises(main.HTTPException) as raised:
                main.enforce_public_preview_rate_limit(request, "limit-test", limit=2, window_seconds=60)
            self.assertEqual(raised.exception.status_code, 429)
            self.assertEqual(raised.exception.headers.get("Retry-After"), "60")
        finally:
            main._PREVIEW_ATTEMPTS.pop(key, None)



    def test_production_signup_requires_configured_email_delivery(self):
        from unittest.mock import patch
        previous = main.EMAIL_VERIFICATION_REQUIRED
        main.EMAIL_VERIFICATION_REQUIRED = True
        try:
            with patch.dict(os.environ, {"BOLKE_SMTP_HOST": "", "BOLKE_SMTP_FROM": "", "BOLKE_PUBLIC_ORIGIN": ""}):
                response = self.client.post("/api/auth/register", json={
                    "email": f"mail-missing-{uuid.uuid4().hex[:8]}@example.test",
                    "password": "Synthetic-demo-pass-2026",
                }, headers={"Origin": "http://testserver"})
            self.assertEqual(response.status_code, 503, response.text)
            self.assertIn("email verification is not configured", response.json()["detail"])
        finally:
            main.EMAIL_VERIFICATION_REQUIRED = previous

    def test_verification_link_activates_account_and_is_single_use(self):
        from unittest.mock import patch
        previous = main.EMAIL_VERIFICATION_REQUIRED
        main.EMAIL_VERIFICATION_REQUIRED = True
        sent = []
        try:
            with patch.object(main, "auth_email_delivery_capability", return_value={"configured": True}), \
                 patch.object(main, "send_auth_action_email", side_effect=lambda email, token, purpose: sent.append((email, token, purpose))):
                email = f"verify-{uuid.uuid4().hex[:8]}@example.test"
                created = self.client.post("/api/auth/register", json={"email": email, "password": "Synthetic-demo-pass-2026"}, headers={"Origin": "http://testserver"})
                self.assertEqual(created.status_code, 201, created.text)
                self.assertTrue(created.json()["verification_required"])
                self.assertFalse(self.client.cookies.get(main.SESSION_COOKIE_NAME))
                self.assertFalse(self.client.get("/api/auth/me").json().get("user"))
                login = self.client.post("/api/auth/login", json={"email": email, "password": "Synthetic-demo-pass-2026"}, headers={"Origin": "http://testserver"})
                self.assertEqual(login.status_code, 401)
                self.assertEqual(len(sent), 1)
                self.assertEqual(sent[0][2], "email_verification")
                verified = self.client.post("/api/auth/verify-email", json={"token": sent[0][1]}, headers={"Origin": "http://testserver"})
                self.assertEqual(verified.status_code, 200, verified.text)
                self.assertTrue(verified.json()["user"]["email_verified"])
                self.assertTrue(self.client.cookies.get(main.SESSION_COOKIE_NAME))
                self.assertTrue(self.client.get("/api/auth/me").json()["user"]["email_verified"])
                replay = self.client.post("/api/auth/verify-email", json={"token": sent[0][1]}, headers={"Origin": "http://testserver"})
                self.assertEqual(replay.status_code, 400)
        finally:
            main.EMAIL_VERIFICATION_REQUIRED = previous

    def test_password_reset_is_non_enumerating_and_revokes_existing_sessions(self):
        from unittest.mock import patch
        email = self.register(self.client, "reset-password")
        sent = []
        with patch.object(main, "auth_email_delivery_capability", return_value={"configured": True}), \
             patch.object(main, "send_auth_action_email", side_effect=lambda address, token, purpose: sent.append((address, token, purpose))):
            unknown = self.client.post("/api/auth/password-reset/request", json={"email": "unknown@example.test"}, headers={"Origin": "http://testserver"})
            known = self.client.post("/api/auth/password-reset/request", json={"email": email}, headers={"Origin": "http://testserver"})
            self.assertEqual(unknown.status_code, 200)
            self.assertEqual(unknown.json(), known.json())
            self.assertEqual(len(sent), 1)
            self.assertEqual(sent[0][2], "password_reset")
            reset = self.client.post("/api/auth/password-reset/confirm", json={"token": sent[0][1], "new_password": "Synthetic-new-reset-pass-2026"}, headers={"Origin": "http://testserver"})
            self.assertEqual(reset.status_code, 200, reset.text)
            replay = self.client.post("/api/auth/password-reset/confirm", json={"token": sent[0][1], "new_password": "Synthetic-another-reset-pass-2026"}, headers={"Origin": "http://testserver"})
            self.assertEqual(replay.status_code, 400)
        self.assertEqual(self.client.get("/api/cases").status_code, 401)
        login = self.client.post("/api/auth/login", json={"email": email, "password": "Synthetic-new-reset-pass-2026"}, headers={"Origin": "http://testserver"})
        self.assertEqual(login.status_code, 200, login.text)

if __name__ == "__main__":
    unittest.main()
