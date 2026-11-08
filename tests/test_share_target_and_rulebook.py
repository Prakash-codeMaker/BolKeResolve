"""Regression coverage for Share-to-Case, the dated NCH snapshot and rulebook metadata.

All shared data and payment stories in this file are synthetic. No live provider is called.
"""
from __future__ import annotations

import base64
import json
import os
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from backend import main
from backend.rulebook import RULEBOOK_REVIEWED_ON, RULEBOOK_VERSION, rulebook_metadata
from backend.support_directory import find_nch_convergence_match


_PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lRkAAAAASUVORK5CYII="
)


class ShareTargetAndRulebookTests(unittest.TestCase):
    def setUp(self):
        self.auth_before = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        self.old_env = {
            key: os.environ.get(key)
            for key in (
                "BOLKE_SHARE_INTAKE_ENCRYPTION_KEY",
                "BOLKE_SHARE_INTAKE_RETENTION_MINUTES",
            )
        }
        os.environ["BOLKE_SHARE_INTAKE_ENCRYPTION_KEY"] = Fernet.generate_key().decode("ascii")
        os.environ["BOLKE_SHARE_INTAKE_RETENTION_MINUTES"] = "30"
        self.client = TestClient(main.app)
        created = self.client.post("/api/cases", json={
            "issue_type": "Refund not received",
            "merchant": "Zomato",
            "amount": 950,
            "payment_date": "2026-10-20",
            "language_code": "en-IN",
            "payment_status": "refund_pending",
            "contacted_support": True,
            "description": "Zomato refund of INR 950 was promised but has not arrived.",
        })
        self.assertEqual(created.status_code, 201, created.text)
        self.case_id = created.json()["case_id"]

    def tearDown(self):
        try:
            self.client.delete(f"/api/cases/{self.case_id}")
        except Exception:
            pass
        self.client.close()
        main.AUTH_REQUIRED = self.auth_before
        for key, val in self.old_env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def create_share(self, *, title="Receipt", text="Refund of INR 950 was promised.", url="https://www.zomato.com/orders/123?session=private-token", file=None):
        data = {"title": title, "text": text, "url": url}
        files = None
        if file:
            files = {"shared_file": file}
        response = self.client.post("/share-target", data=data, files=files, follow_redirects=False)
        return response

    def token_from_location(self, response):
        self.assertEqual(response.status_code, 303, response.text)
        parsed = urlsplit(response.headers["location"])
        # Fragment tokens never go back to the web server in a GET request/referrer.
        query = parse_qs(parsed.fragment)
        self.assertIn("shared_intake", query)
        self.assertNotIn("shared_intake", parsed.query)
        self.assertEqual(response.headers.get("referrer-policy"), "no-referrer")
        return query["shared_intake"][0]

    def test_share_target_stages_encrypted_preview_then_explicitly_attaches_to_case(self):
        response = self.create_share(file=("receipt.png", _PNG_1PX, "image/png"))
        token = self.token_from_location(response)
        preview = self.client.get("/api/shared-intake/preview", headers={"X-Share-Intake-Token": token})
        self.assertEqual(preview.status_code, 200, preview.text)
        data = preview.json()
        self.assertEqual(data["title"], "Receipt")
        self.assertEqual(data["source_domain"], "www.zomato.com")
        self.assertTrue(data["has_file"])
        self.assertNotIn("session=private-token", preview.text)
        self.assertNotIn("/orders/123", preview.text)
        self.assertFalse(data.get("attached", False))

        # Attach uses a constant route. Case identity/options stay in the JSON body;
        # the one-time capability stays in a request header rather than the URL.
        legacy_path_response = self.client.post(f"/api/shared-intake/attach/{self.case_id}?include_context=true", headers={"X-Share-Intake-Token": token})
        self.assertNotEqual(legacy_path_response.status_code, 200)
        attached = self.client.post("/api/shared-intake/attach", json={"case_id": self.case_id, "include_context": True}, headers={"X-Share-Intake-Token": token})
        self.assertEqual(attached.status_code, 200, attached.text)
        body = attached.json()
        self.assertTrue(body["attached"])
        self.assertFalse(body["raw_share_content_retained"])
        self.assertTrue(body["evidence_id"])
        evidence = self.client.get(f"/api/cases/{self.case_id}").json()["evidence"]
        self.assertTrue(any(item["evidence_id"] == body["evidence_id"] for item in evidence))
        again = self.client.get("/api/shared-intake/preview", headers={"X-Share-Intake-Token": token})
        self.assertEqual(again.status_code, 404)
        with main.get_db() as con:
            row = con.execute("SELECT title_ciphertext,text_ciphertext,url_ciphertext,filename_ciphertext,file_ciphertext,consumed_at FROM pending_share_intakes").fetchone()
        self.assertEqual(row["title_ciphertext"], "")
        self.assertEqual(row["text_ciphertext"], "")
        self.assertEqual(row["url_ciphertext"], "")
        self.assertEqual(row["filename_ciphertext"], "")
        self.assertIsNone(row["file_ciphertext"])
        self.assertTrue(row["consumed_at"])

    def test_share_text_redacts_sensitive_values_and_private_url_components(self):
        response = self.create_share(
            title="Support link https://merchant.example/reset?token=super-secret",
            text="Please review https://merchant.example/ticket/ABC?auth=super-secret and never use 123456 as OTP.",
            url="https://merchant.example/orders/123?auth=super-secret",
        )
        token = self.token_from_location(response)
        preview = self.client.get("/api/shared-intake/preview", headers={"X-Share-Intake-Token": token})
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertNotIn("super-secret", preview.text)
        self.assertNotIn("/ticket/ABC", preview.text)
        self.assertNotIn("/reset", preview.text)
        self.assertNotIn("/orders/123", preview.text)
        self.assertNotIn("123456", preview.text)
        self.client.delete("/api/shared-intake/discard", headers={"X-Share-Intake-Token": token})

    def test_share_target_rejects_bad_file_signature_and_unsupported_type(self):
        bad_signature = self.create_share(file=("fake.png", b"not a png", "image/png"))
        self.assertEqual(bad_signature.status_code, 400, bad_signature.text)
        unsupported = self.create_share(file=("private.exe", b"MZnotallowed", "application/octet-stream"))
        self.assertEqual(unsupported.status_code, 415, unsupported.text)

    def test_share_capability_is_sent_in_header_not_logged_api_path(self):
        token = self.token_from_location(self.create_share(text="Header token test"))
        # The fixed endpoint path avoids carrying the bearer token in reverse-proxy access logs.
        self.assertEqual(self.client.get("/api/shared-intake/preview").status_code, 404)
        self.assertEqual(self.client.get(f"/api/shared-intake/{token}").status_code, 404)
        self.assertEqual(self.client.get("/api/shared-intake/preview", headers={"X-Share-Intake-Token": token}).status_code, 200)
        self.client.delete("/api/shared-intake/discard", headers={"X-Share-Intake-Token": token})

    def test_share_target_discards_by_bearer_token(self):
        token = self.token_from_location(self.create_share(text="Only a sample message"))
        removed = self.client.delete("/api/shared-intake/discard", headers={"X-Share-Intake-Token": token})
        self.assertEqual(removed.status_code, 200, removed.text)
        self.assertTrue(removed.json()["discarded"])
        self.assertEqual(self.client.get("/api/shared-intake/preview", headers={"X-Share-Intake-Token": token}).status_code, 404)

    def test_share_target_expired_rows_are_not_previewable(self):
        token = self.token_from_location(self.create_share(text="Short-lived sample"))
        with main.get_db() as con:
            con.execute("UPDATE pending_share_intakes SET expires_at=0 WHERE token_hash=?", (__import__("hashlib").sha256(token.encode()).hexdigest(),))
        self.assertEqual(self.client.get("/api/shared-intake/preview", headers={"X-Share-Intake-Token": token}).status_code, 404)

    def test_share_target_requires_configured_encryption_in_production(self):
        prior_env = main.DEPLOYMENT_ENV
        original_key = os.environ.pop("BOLKE_SHARE_INTAKE_ENCRYPTION_KEY", None)
        try:
            main.DEPLOYMENT_ENV = "production"
            response = self.client.post("/share-target", data={"text": "a synthetic shared item"}, follow_redirects=False)
            self.assertEqual(response.status_code, 503, response.text)
            self.assertIn("encryption key is not configured", response.text)
        finally:
            main.DEPLOYMENT_ENV = prior_env
            if original_key is not None:
                os.environ["BOLKE_SHARE_INTAKE_ENCRYPTION_KEY"] = original_key

    def test_rulebook_distinguishes_failed_upi_from_merchant_refund(self):
        failed = rulebook_metadata("UPI payment failed", "failed", "UPI debit shown as failed")
        refund = rulebook_metadata("Refund not received", "refund_pending", "Zomato refund pending")
        self.assertEqual(failed["version"], RULEBOOK_VERSION)
        self.assertEqual(failed["reviewed_on"], RULEBOOK_REVIEWED_ON)
        self.assertEqual(failed["matched_rules"][0]["id"], "failed_upi_debit_npci_faq")
        self.assertEqual(refund["matched_rules"][0]["id"], "merchant_refund_policy_first")
        self.assertIn("not automatically apply", refund["matched_rules"][0]["scope"])
        self.assertTrue(all(item["sources"] for item in (failed["matched_rules"][0], refund["matched_rules"][0])))

    def test_resolution_preview_includes_versioned_rules_and_source_caveat(self):
        response = self.client.post("/api/resolution/preview", json={
            "issue_type": "Refund not received",
            "merchant": "Zomato",
            "amount": 950,
            "payment_status": "refund_pending",
            "contacted_support": True,
            "description": "Zomato refund of INR 950 is still pending after support promised it.",
        })
        self.assertEqual(response.status_code, 200, response.text)
        rulebook = response.json()["rulebook"]
        self.assertEqual(rulebook["version"], RULEBOOK_VERSION)
        self.assertTrue(rulebook["matched_rules"][0]["sources"])
        self.assertIn("not a live transaction check", rulebook["notice"])
        match = response.json()["nch_directory_match"]
        self.assertEqual(match["status"], "listed_in_reviewed_snapshot")
        self.assertEqual(match["reviewed_on"], "2026-10-23")

    def test_official_directory_api_discloses_snapshot_limitations(self):
        listed = self.client.get("/api/support-directory", params={"merchant": "Zomato"})
        self.assertEqual(listed.status_code, 200, listed.text)
        data = listed.json()
        self.assertEqual(data["nch_directory_match"]["legal_name"], "ETERNAL LIMITED")
        self.assertIn("small reviewed snapshot", data["notice"])
        unknown = self.client.get("/api/support-directory", params={"merchant": "Definitely Not Listed Corp"}).json()
        self.assertEqual(unknown["nch_directory_match"]["status"], "not_matched_in_reviewed_snapshot")
        self.assertIn("does not mean", unknown["nch_directory_match"]["message"])

    def test_nch_snapshot_match_requires_a_conservative_exact_alias(self):
        self.assertEqual(find_nch_convergence_match("Zomato")["status"], "listed_in_reviewed_snapshot")
        self.assertEqual(find_nch_convergence_match("my-zomato-ish-fantasy")["status"], "not_matched_in_reviewed_snapshot")

    def test_share_target_is_rate_limited_at_the_public_intake_boundary(self):
        with patch("backend.main.enforce_public_preview_rate_limit") as throttle:
            response = self.create_share(text="A synthetic item for throttle test")
            token = self.token_from_location(response)
            throttle.assert_called_once()
            self.assertEqual(throttle.call_args.args[1], "share-target")
            self.assertGreaterEqual(throttle.call_args.args[2], 3)
            self.assertLessEqual(throttle.call_args.args[2], 60)
        self.client.delete("/api/shared-intake/discard", headers={"X-Share-Intake-Token": token})

    def test_manifest_declares_pwa_share_target_and_supported_file_types(self):
        manifest = json.loads((main.FRONTEND_DIR / "manifest.webmanifest").read_text(encoding="utf-8"))
        share_target = manifest["share_target"]
        self.assertEqual(share_target["action"], "/share-target")
        self.assertEqual(share_target["method"], "POST")
        accepted = share_target["params"]["files"][0]["accept"]
        self.assertEqual(accepted, [".png", ".jpg", ".jpeg", ".webp", ".pdf"])

    def test_share_token_is_scrubbed_by_head_script_before_app_bundle(self):
        index = (main.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        head_script = (main.FRONTEND_DIR / "share-token.js").read_text(encoding="utf-8")
        app_script = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        self.assertLess(index.index('<script src="/share-token.js"></script>'), index.index('<link rel="stylesheet"'))
        self.assertIn("history.replaceState", head_script)
        self.assertIn("url.searchParams.delete('shared_intake')", head_script)
        self.assertIn("hashParams.delete('shared_intake')", head_script)
        self.assertIn("sessionStorage.setItem('bolke_pending_share_token', token)", head_script)
        self.assertIn("X-Share-Intake-Token", app_script)
        self.assertNotIn("/api/shared-intake/attach/${encodeURIComponent", app_script)
        self.assertIn("api('/api/shared-intake/attach'", app_script)
        served = self.client.get('/share-token.js')
        self.assertEqual(served.status_code, 200, served.text)
        self.assertIn('no-store', served.headers.get('cache-control', ''))

    def test_constant_attach_endpoint_validates_case_id_in_request_body(self):
        token = self.token_from_location(self.create_share(text="constant route validation"))
        invalid = self.client.post("/api/shared-intake/attach", json={"case_id": "../../etc/passwd", "include_context": True}, headers={"X-Share-Intake-Token": token})
        self.assertEqual(invalid.status_code, 422, invalid.text)
        # Failed validation must not consume the capability.
        preview = self.client.get("/api/shared-intake/preview", headers={"X-Share-Intake-Token": token})
        self.assertEqual(preview.status_code, 200, preview.text)
        self.client.delete("/api/shared-intake/discard", headers={"X-Share-Intake-Token": token})


if __name__ == "__main__":
    unittest.main()
