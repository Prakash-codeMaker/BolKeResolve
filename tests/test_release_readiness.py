import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_release_readiness as release_checks  # noqa: E402


class ReleaseReadinessHelperTests(unittest.TestCase):
    def test_https_origin_rejects_path_query_credentials_and_http(self):
        self.assertTrue(release_checks.https_origin("https://bolke.example"))
        self.assertTrue(release_checks.https_origin("https://bolke.example/"))
        for bad in (
            "http://bolke.example",
            "https://bolke.example/app",
            "https://bolke.example?next=app",
            "https://user:pass@bolke.example",
            "bolke.example",
        ):
            with self.subTest(value=bad):
                self.assertFalse(release_checks.https_origin(bad))

    def test_email_delivery_status_requires_tls_and_https_origin_in_production(self):
        ready_config = {
            "BOLKE_SMTP_HOST": "smtp.example.test", "BOLKE_SMTP_PORT": "587",
            "BOLKE_SMTP_FROM": "noreply@example.test", "BOLKE_SMTP_USE_STARTTLS": "true",
            "BOLKE_PUBLIC_ORIGIN": "https://bolke.example",
        }
        ready, _ = release_checks.email_delivery_status(ready_config, production=True)
        self.assertTrue(ready)
        insecure = dict(ready_config, BOLKE_PUBLIC_ORIGIN="http://bolke.example")
        ready, detail = release_checks.email_delivery_status(insecure, production=True)
        self.assertFalse(ready)
        self.assertIn("encrypted SMTP", detail)
        no_tls = dict(ready_config, BOLKE_SMTP_USE_STARTTLS="false", BOLKE_SMTP_USE_SSL="false")
        self.assertFalse(release_checks.email_delivery_status(no_tls, production=True)[0])

    def test_privacy_notice_status_rejects_operator_draft_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "privacy.html"
            page.write_text("<h1>Privacy Notice</h1><p>DRAFT FOR THE OPERATOR</p><p>[REPLACE WITH contact]</p>", encoding="utf-8")
            ready, detail = release_checks.privacy_notice_status(page)
            self.assertFalse(ready)
            self.assertIn("placeholders", detail)

    def test_privacy_notice_status_passes_template_without_known_placeholders_but_requires_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "privacy.html"
            page.write_text("<h1>Privacy Notice</h1><p>Published operator policy.</p>", encoding="utf-8")
            ready, detail = release_checks.privacy_notice_status(page)
            self.assertTrue(ready)
            self.assertIn("legal/operator review is still required", detail)

    def test_privacy_notice_status_fails_when_file_is_missing(self):
        ready, detail = release_checks.privacy_notice_status(Path("/no/such/privacy.html"))
        self.assertFalse(ready)
        self.assertIn("cannot be read", detail)


if __name__ == "__main__":
    unittest.main()
