/**
 * BolKeResolve Gmail email bridge.
 *
 * Deploy as a Web app:
 *   Execute as: Me
 *   Who has access: Anyone (including anonymous access if shown)
 *
 * Set Script Property BOLKE_MAIL_BRIDGE_TOKEN to a random secret of at least
 * 32 characters. Set the exact same value in Render as BOLKE_GMAIL_SCRIPT_TOKEN.
 * Never commit the secret or place it in a browser/frontend.
 */
const TOKEN_PROPERTY = "BOLKE_MAIL_BRIDGE_TOKEN";
const MAX_BODY_CHARS = 12000;

function authorizeMailBridge() {
  // Run once from the editor to authorize the sending permission.
  MailApp.getRemainingDailyQuota();
}

function doGet() {
  return jsonOutput({ ok: true, service: "BolKeResolve Gmail bridge" });
}

function doPost(event) {
  try {
    const raw = event && event.postData && event.postData.contents
      ? String(event.postData.contents)
      : "";
    if (!raw || raw.length > MAX_BODY_CHARS) {
      return jsonOutput({ ok: false, error: "invalid_request" });
    }

    const payload = JSON.parse(raw);
    const expected = PropertiesService.getScriptProperties()
      .getProperty(TOKEN_PROPERTY) || "";
    const supplied = String(payload.token || "");

    if (expected.length < 32 || !constantTimeEquals(supplied, expected)) {
      return jsonOutput({ ok: false, error: "unauthorized" });
    }

    const recipient = String(payload.to || "").trim();
    const subject = String(payload.subject || "").trim();
    const body = String(payload.text || "");

    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(recipient) ||
        !subject || subject.length > 180 ||
        !body || body.length > 10000) {
      return jsonOutput({ ok: false, error: "invalid_message" });
    }

    if (MailApp.getRemainingDailyQuota() < 1) {
      return jsonOutput({ ok: false, error: "daily_quota_exceeded" });
    }

    MailApp.sendEmail({
      to: recipient,
      subject: subject,
      body: body,
      name: "BolKeResolve"
    });

    return jsonOutput({ ok: true });
  } catch (error) {
    // Do not return exception details to the public caller.
    console.error("BolKeResolve mail bridge failure: " +
      (error && error.name ? error.name : "Error"));
    return jsonOutput({ ok: false, error: "send_failed" });
  }
}

function constantTimeEquals(a, b) {
  if (a.length !== b.length) return false;
  let mismatch = 0;
  for (let i = 0; i < a.length; i++) {
    mismatch |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return mismatch === 0;
}

function jsonOutput(value) {
  return ContentService
    .createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}
