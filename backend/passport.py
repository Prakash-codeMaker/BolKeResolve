"""Portable Resolution Passport export helpers.

Exports deliberately label case facts as user-reported and do not imply any
external service has been queried. Evidence file bytes are never embedded.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from urllib.parse import quote
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def build_passport_export(case: dict[str, Any]) -> dict[str, Any]:
    resolution = case.get("resolution") or {}
    outcome = case.get("outcome") or None
    timeline = []
    allowed_metadata = {
        "reference_provided", "note", "due_date", "completed", "user_reported",
        "redacted_categories", "reference_redacted_categories", "cleared",
        "reply_review_category", "reply_review_label", "reply_review_engine",
        "reply_interpretation_confirmed", "raw_reply_retained", "inbound_message_id",
        "attachments_count", "review_required", "sender_identity_verified", "raw_document_text_retained",
        "confirmed_fields", "applied_fields", "capture_source", "captured_at_client",
        "evidence_id", "mime_type", "size_bytes", "sha256", "authenticity_verified",
    }
    for event in case.get("timeline") or []:
        metadata = event.get("metadata") or {}
        safe_metadata = {key: value for key, value in metadata.items() if key in allowed_metadata}
        timeline.append({
            "event_type": event.get("event_type", ""),
            "message": event.get("message", ""),
            "created_at": event.get("created_at", ""),
            "actor": event.get("actor", "system"),
            "channel": event.get("channel", "web"),
            "source": event.get("source", "bolkeresolve"),
            "metadata": safe_metadata,
        })
    commitment_exports = []
    for item in case.get("commitments") or []:
        safe_events = []
        for event in item.get("events") or []:
            safe_events.append({
                "event_type": event.get("event_type", ""),
                "relation": event.get("relation", "unknown"),
                "evidence_status": event.get("evidence_status", "user_reported"),
                "source_excerpt": event.get("source_excerpt_redacted", ""),
                "event_date_claimed": event.get("event_date_claimed", ""),
                "event_date_confirmed": event.get("event_date_confirmed", ""),
                "created_at": event.get("created_at", ""),
                "source_authenticity_verified": False,
            })
        commitment_exports.append({
            "commitment_id": item.get("commitment_id", ""),
            "source_type": item.get("source_type", ""),
            "source_label": item.get("source_label", ""),
            "source_excerpt_redacted": item.get("source_excerpt_redacted", ""),
            "source_hash": item.get("source_hash", ""),
            "source_authenticity_verified": False,
            "speech_act": item.get("speech_act", ""),
            "action_code": item.get("action_code", ""),
            "action_text": item.get("action_text", ""),
            "amount_minor_units": item.get("amount_minor_units"),
            "currency": item.get("currency", "INR"),
            "condition_text": item.get("condition_text", ""),
            "trigger_type": item.get("trigger_type", "unspecified"),
            "duration_value": item.get("duration_value"),
            "duration_max_value": item.get("duration_max_value"),
            "duration_unit": item.get("duration_unit", ""),
            "day_type": item.get("day_type", "unspecified"),
            "qualifier": item.get("qualifier", ""),
            "statement_date": item.get("statement_date", ""),
            "review_state": item.get("review_state", "candidate"),
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
            "evaluation": item.get("evaluation", {}),
            "events": safe_events,
        })
    return {
        "passport_format": "bolkeresolve-resolution-passport",
        "format_version": "1.5",
        "generated_at": now_iso(),
        "notice": (
            "This passport was generated from information supplied or recorded by the user. "
            "BolKeResolve has not independently verified any payment, merchant response, bank record, "
            "government record or complaint submission. Check sources and details before sharing."
        ),
        "case": {
            "case_id": case.get("case_id", ""),
            "created_at": case.get("created_at", ""),
            "updated_at": case.get("updated_at", ""),
            "issue_type": case.get("issue_type", ""),
            "merchant": case.get("merchant", ""),
            "amount": case.get("amount"),
            "payment_date": case.get("payment_date", ""),
            "language_code": case.get("language_code", ""),
            "description": case.get("description", ""),
            "case_stage": case.get("case_stage", "Needs next step"),
            "payment_status": case.get("payment_status", "unknown"),
            "contacted_support": case.get("contacted_support"),
            "fact_provenance": case.get("fact_provenance", []),
            "document_fact_sources": [
                {
                    "field": item.get("field_key", ""),
                    "value": item.get("value"),
                    "source_file": item.get("original_name", ""),
                    "source_label": item.get("source_label", "User-uploaded evidence; not independently verified"),
                    "applied_to_case": bool(item.get("applied_to_case")),
                    "confirmed_at": item.get("confirmed_at", ""),
                    "source_authenticity_verified": False,
                }
                for item in case.get("evidence_fact_sources", [])
            ],
            "recommended_first_action": (case.get("action_pack") or {}).get("first_action", ""),
            "resolution_plan": {
                "classification": resolution.get("classification", {}),
                "urgency": resolution.get("urgency", {}),
                "missing_information": resolution.get("missing_information", []),
                "recommended_steps": resolution.get("recommended_steps", []),
                "official_sources": resolution.get("official_sources", []),
                "generated_at": resolution.get("generated_at", ""),
            },
            "evidence_inventory": [
                {
                    "name": item.get("original_name", ""),
                    "mime_type": item.get("mime_type", ""),
                    "size_bytes": item.get("size_bytes", 0),
                    "added_at": item.get("created_at", ""),
                    "origin": item.get("origin", "Uploaded by user"),
                    "verification_status": item.get("verification_status", "Not independently verified"),
                    "evidence_id": item.get("evidence_id", ""),
                    "capture_source": item.get("capture_source", "user_upload"),
                    "captured_at_client": item.get("captured_at", ""),
                    "session_id": item.get("session_id", ""),
                    "sha256": item.get("sha256", ""),
                    "scan_status": item.get("scan_status", "not_scanned"),
                    "claim_links": [
                        {
                            "claim_key": link.get("claim_key", ""),
                            "claim_label": link.get("claim_label", ""),
                            "relation": link.get("relation", "context"),
                            "note": link.get("note", ""),
                            "created_at": link.get("created_at", ""),
                        }
                        for link in item.get("claim_links", [])
                    ],
                    "source_authenticity_verified": False,
                    "download_path": f"/api/cases/{case.get('case_id', '')}/evidence/{item.get('evidence_id', '')}" if item.get("evidence_id") else "",
                }
                for item in case.get("evidence", [])
            ],
            "fact_history": [
                {
                    "fact_id": item.get("fact_id", ""),
                    "fact_key": item.get("fact_key", ""),
                    "value": item.get("value"),
                    "source_type": item.get("source_type", ""),
                    "source_event_id": item.get("source_event_id", ""),
                    "source_excerpt_redacted": item.get("source_excerpt_redacted", ""),
                    "confidence": item.get("confidence"),
                    "is_current": bool(item.get("is_current")),
                    "created_at": item.get("created_at", ""),
                }
                for item in case.get("fact_ledger", [])
            ],
            "reconciliation_imports": [
                {
                    "import_id": item.get("import_id", ""),
                    "evidence_id": item.get("evidence_id", ""),
                    "provider": item.get("provider", ""),
                    "status": item.get("status", "previewed"),
                    "created_at": item.get("created_at", ""),
                    "confirmed_at": item.get("confirmed_at", ""),
                    "row_count": (item.get("preview") or {}).get("row_count", 0),
                    "confirmed_rows": (item.get("preview") or {}).get("confirmed_rows", []),
                    "user_confirmed": item.get("status") == "confirmed",
                }
                for item in case.get("reconciliation_imports", [])
            ],
            "checklist": (case.get("action_pack") or {}).get("evidence_checklist", []),
            "follow_up": case.get("follow_up", {}),
            "support_draft": case.get("support_draft", ""),
            "commitments": commitment_exports,
            "outcome": outcome,
            "timeline": timeline,
        },
    }


def render_printable_passport(case: dict[str, Any]) -> str:
    """Render a standalone, self-contained HTML page suitable for browser Print / Save as PDF."""
    pack = case.get("action_pack") or {}
    resolution = case.get("resolution") or {}
    steps = resolution.get("recommended_steps") or []
    sources = resolution.get("official_sources") or []
    checklist = pack.get("evidence_checklist") or []
    follow = case.get("follow_up") or {}
    outcome = case.get("outcome") or {}
    events = sorted(case.get("timeline") or [], key=lambda e: e.get("created_at", ""))
    amount = case.get("amount")
    amount_text = f"₹{float(amount):,.2f}" if amount is not None else "Not provided"
    known = [
        ("Merchant / organisation", case.get("merchant") or "Not provided"),
        ("Reported amount", amount_text),
        ("Payment date", case.get("payment_date") or "Not provided"),
        ("Status shown to you", case.get("payment_status") or "Not known"),
        ("Progress", case.get("case_stage") or "Needs next step"),
    ]
    known_html = "".join(f"<div class='fact'><small>{escape(str(label))}</small><b>{escape(str(value))}</b><span class='fact-origin'>Entered or reported by user · not independently verified</span></div>" for label, value in known)
    step_html = "".join(
        f"<li><b>{escape(str(s.get('title', 'Next step')))}</b><p>{escape(str(s.get('detail', '')))}</p>"
        f"{('<p class=why>' + escape(str(s['why'])) + '</p>') if s.get('why') else ''}</li>"
        for s in steps
    ) or "<li>Review the saved facts and refresh the guidance plan.</li>"
    source_html = "".join(
        f"<li><b>{escape(str(s.get('organization', 'Official source')))} — </b>"
        f"<a href='{escape(str(s.get('url', '')), quote=True)}'>{escape(str(s.get('title', s.get('url', ''))))}</a>"
        f"<small>Reviewed {escape(str(s.get('reviewed_on', 'date not recorded')))}</small></li>"
        for s in sources
    ) or "<li>No official source is attached to this plan.</li>"
    checklist_html = "".join(
        f"<li><span class='check'>{'✓' if item.get('checked') else '□'}</span>"
        f"<b>{escape(str(item.get('title', 'Item')))}</b><p>{escape(str(item.get('detail', '')))}</p></li>"
        for item in checklist
    ) or "<li>No checklist is available.</li>"
    events_html = "".join(
        f"<li><time>{escape(str(e.get('created_at', '')))}</time><b>{escape(str(e.get('event_type', 'Update')).replace('_', ' ').title())}</b>"
        f"<p>{escape(str(e.get('message', '')))}</p><small>{escape(str(e.get('actor', 'system')))} · {escape(str(e.get('channel', 'web')))} · self-reported unless explicitly marked otherwise</small></li>"
        for e in reversed(events)
    ) or "<li>No activity has been recorded yet.</li>"
    outcome_label = {
        "still_pending": "Still pending", "no_response": "No response", "partially_resolved": "Partially resolved",
        "resolved": "Resolved (user-reported)", "stopped": "I stopped pursuing this for now",
    }.get(str(outcome.get("outcome_code", "")), "Not recorded")
    follow_html = f"<p><b>Follow-up:</b> {escape(str(follow.get('due_date') or 'Not set'))}</p>"
    if follow.get("note"):
        follow_html += f"<p><b>Follow-up note:</b> {escape(str(follow.get('note')))}</p>"
    outcome_html = f"<p><b>Latest reported outcome:</b> {escape(outcome_label)}</p>"
    if outcome.get("details"):
        outcome_html += f"<p>{escape(str(outcome.get('details')))}</p>"
    if outcome.get("reference"):
        outcome_html += f"<p><b>Reference recorded by user:</b> {escape(str(outcome.get('reference')))}</p>"
    document_sources = case.get("evidence_fact_sources") or []
    fact_source_html = "".join(
        f"<li><b>{escape(str(item.get('field_key', 'Detail')).replace('_', ' ').title())}: {escape(str(item.get('value', '')))}</b> — "
        f"{escape(str(item.get('original_name', 'uploaded file')))}<p><small>{escape(str(item.get('source_label', 'User-confirmed candidate from uploaded evidence; not independently verified')))}</small></p></li>"
        for item in document_sources
    ) or "<li>No document-derived facts have been confirmed yet.</li>"
    fact_ledger = case.get("fact_ledger") or []
    fact_history_html = "".join(
        f"<li><b>{escape(str(item.get('fact_key', 'Fact')).replace('_', ' ').title())}: {escape(str(item.get('value', '')))}</b>"
        f"<p><small>{'Current value' if item.get('is_current') else 'Superseded value'} · {escape(str(item.get('source_type', 'user-provided')))} · {escape(str(item.get('created_at', '')))}</small></p>"
        f"<p class='muted'>{escape(str(item.get('source_excerpt_redacted', '')))}</p></li>"
        for item in fact_ledger
    ) or "<li>No versioned fact history has been recorded.</li>"
    reconciliation_rows = []
    for item in case.get("reconciliation_imports") or []:
        preview = item.get("preview") or {}
        rows = preview.get("confirmed_rows") or []
        reconciliation_rows.append(
            f"<li><b>{escape(str(item.get('provider', 'Payment provider')))} settlement report</b> — "
            f"{escape(str(item.get('status', 'previewed')))}; {len(rows)} user-confirmed row(s)"
            f"<small>Imported {escape(str(item.get('created_at', '')))} · source evidence {escape(str(item.get('evidence_id', '')))}</small></li>"
        )
    reconciliation_html = "".join(reconciliation_rows) or "<li>No reconciliation report has been imported.</li>"
    evidence_rows = case.get("evidence") or []
    evidence_html = "".join(
        "<tr>"
        f"<td>E-{index:03d}</td>"
        f"<td><b>{escape(str(item.get('original_name', 'Evidence file')))}</b><small>{escape(str(item.get('mime_type', '')))} · {int(item.get('size_bytes', 0) or 0):,} bytes</small></td>"
        f"<td>{escape(str(item.get('capture_source', 'user_upload')).replace('_', ' ').title())}<small>Added {escape(str(item.get('created_at', '')))}</small><small>Malware scan: {escape(str(item.get('scan_status', 'not_scanned')))}</small>" + "".join(f"<small>{escape(str(link.get('relation', 'context')))}: {escape(str(link.get('claim_label', link.get('claim_key', 'claim'))))}</small>" for link in item.get('claim_links', [])) + "</td>"
        f"<td><a href='/api/cases/{escape(str(case.get('case_id', '')), quote=True)}/evidence/{escape(str(item.get('evidence_id', '')), quote=True)}'>Open original ↗</a><small>SHA-256 {escape(str(item.get('sha256', 'not recorded')))}</small></td>"
        "</tr>"
        for index, item in enumerate(evidence_rows, start=1)
    ) or "<tr><td colspan='4'>No evidence files have been attached.</td></tr>"
    evidence_bundle_url = f"/api/cases/{quote(str(case.get('case_id', '')), safe='')}/evidence-bundle.zip"
    draft = case.get("support_draft") or "No support message has been prepared."
    commitments = case.get("commitments") or []
    commitment_html = "".join(
        f"<li><b>{escape(str(item.get('action_text', 'Commitment')))}</b> — {escape(str((item.get('evaluation') or {}).get('status_label', 'Needs review')))}"
        f"<p><b>Condition:</b> {escape(str(item.get('condition_text') or 'Not detected'))}</p>"
        f"<p><b>Timeframe:</b> {escape(str(item.get('duration_value') if item.get('duration_value') is not None else 'Not stated'))} {escape(str(item.get('day_type', '')))} {escape(str(item.get('duration_unit', '')))}; trigger: {escape(str(item.get('trigger_type', 'unspecified')))}</p>"
        f"<p class='story'>{escape(str(item.get('source_excerpt_redacted', '')))}</p>"
        f"<small>Source not independently verified · {escape(str(item.get('source_label', item.get('source_type', 'user-provided'))))}</small>"
        f"<p>{escape(str((item.get('evaluation') or {}).get('next_action', 'Review the source and current state.')))}</p>"
        f"<ul>" + "".join(
            f"<li><b>{escape(str(event.get('relation', 'update')).replace('_', ' ').title())}</b> — {escape(str(event.get('source_excerpt_redacted', '')))} <small>{escape(str(event.get('created_at', '')))} · user-reviewed, not independently verified</small></li>"
            for event in (item.get('events') or []) if event.get('source_excerpt_redacted')
        ) + "</ul></li>"
        for item in commitments
    ) or "<li>No commitment record has been saved.</li>"
    notice = "This document contains personal case details, notes, commitment statements and any recorded references. Review it before sharing. No payment or complaint status has been independently verified. Document-derived facts were extracted from user-uploaded files and confirmed by the user; file authenticity is not independently verified."
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Resolution Passport {escape(str(case.get('case_id', '')))}</title><style>
:root{{color-scheme:light;font-family:Arial,sans-serif;color:#17362f;background:#fff}}*{{box-sizing:border-box}}body{{margin:0}}.toolbar{{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:16px 24px;background:#eff7f1;border-bottom:1px solid #dbe7dc}}.toolbar button{{border:0;border-radius:999px;background:#073e37;color:white;padding:10px 16px;font-weight:700;cursor:pointer}}main{{max-width:900px;margin:28px auto;padding:0 24px 40px}}.brand{{color:#087763;font-size:12px;font-weight:800;letter-spacing:.14em}}h1{{font-size:34px;margin:8px 0}}h2{{font-size:18px;margin:25px 0 9px;border-bottom:1px solid #dce7df;padding-bottom:7px}}p{{line-height:1.55}}.muted{{color:#66756e}}.notice{{padding:12px 14px;background:#fff5df;border:1px solid #ebdfbd;border-radius:8px;font-size:12px;line-height:1.55}}.facts{{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}}.fact{{background:#f5f7f2;padding:11px;border-radius:8px;min-width:0}}.fact small{{display:block;color:#61736a;font-size:10px;margin-bottom:5px}}.fact b{{overflow-wrap:anywhere}}.fact-origin{{display:block;margin-top:7px;color:#7a897e;font-size:9px;line-height:1.4}}.story,.draft{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f8f8f4;padding:14px;border-radius:8px}}li{{margin:0 0 12px;line-height:1.5}}li p{{margin:4px 0}}.why,small{{color:#65766e}}a{{color:#087763;overflow-wrap:anywhere}}table{{width:100%;border-collapse:collapse;font-size:11px}}th,td{{text-align:left;vertical-align:top;padding:9px 7px;border-bottom:1px solid #e2e8df;overflow-wrap:anywhere}}th{{background:#f3f6f1;color:#5d7066}}td small{{display:block;margin-top:5px;font-size:9px}}.bundle-link{{display:inline-block;margin:8px 0;padding:9px 12px;border-radius:8px;background:#e9f4ec;color:#075447;font-weight:700;text-decoration:none}}.check{{display:inline-block;width:22px}}.event{{border-left:2px solid #dce9df;padding-left:12px}}time{{font-size:10px;color:#69786f;display:block;margin-bottom:4px}}footer{{margin-top:28px;border-top:1px solid #ddd;padding-top:14px;font-size:11px;color:#61736a}}@media(max-width:600px){{.facts{{grid-template-columns:1fr 1fr}}main{{padding:0 16px}}}}@media print{{.toolbar{{display:none}}main{{margin:0 auto;padding:0;max-width:none}}body{{font-size:10pt}}h2{{break-after:avoid}}li,.fact,.story,.draft{{break-inside:avoid}}a{{color:#17362f;text-decoration:none}}}}
</style></head><body><div class='toolbar'><b>BolKeResolve · Portable Resolution Passport</b><button onclick='window.print()'>Print / Save as PDF</button></div><main>
<div class='brand'>BOLKERESOLVE · RESOLUTION PASSPORT</div><h1>{escape(str(case.get('issue_type', 'Consumer issue')))}</h1><p class='muted'>Case {escape(str(case.get('case_id', '')))} · Created {escape(str(case.get('created_at', '')))} · Updated {escape(str(case.get('updated_at', '')))}</p>
<div class='notice'>{escape(notice)}</div><h2>Case details — user-reported unless noted</h2><div class='facts'>{known_html}</div><p class='muted'>Source labels describe how information entered the case; they do not prove that a payment or organisation action happened. Uploaded files and their authenticity have not been independently checked.</p><h2>Your story</h2><div class='story'>{escape(str(case.get('description', '')))}</div><h2>Facts confirmed from uploaded evidence</h2><ul>{fact_source_html}</ul><h2>Fact history &amp; corrections</h2><p class='muted'>Current and superseded fact values are shown with source excerpts to preserve how the case evolved.</p><ul>{fact_history_html}</ul><h2>Evidence register</h2><p class='muted'>Each exhibit is listed with its file hash and capture source. A hash helps detect byte changes after export; it does not prove the original file's authenticity or capture date.</p><table><thead><tr><th>Exhibit</th><th>File</th><th>Capture / upload</th><th>Access</th></tr></thead><tbody>{evidence_html}</tbody></table><a class='bundle-link' href='{escape(evidence_bundle_url, quote=True)}'>Download complete case + evidence bundle ↗</a>
<h2>Settlement / reconciliation imports</h2><p class='muted'>Imported report rows are not treated as verified account data. Only rows explicitly confirmed by the user are listed below.</p><ul>{reconciliation_html}</ul><h2>Recommended first action</h2><p>{escape(str(pack.get('first_action', 'Review the next step in the saved case.')))}</p><h2>Guided next steps</h2><ol>{step_html}</ol><h2>Preparation checklist</h2><ul>{checklist_html}</ul><h2>Official sources to review</h2><ul>{source_html}</ul>
<h2>Support message draft (not sent)</h2><div class='draft'>{escape(str(draft))}</div><h2>Commitments &amp; conditions</h2><p class='muted'>Statements are user-reviewed candidates. Sources and company claims are not independently verified. Estimated business-day dates exclude public holidays.</p><ul>{commitment_html}</ul><h2>Follow-up</h2>{follow_html}<h2>Outcome</h2>{outcome_html}<h2>Case timeline</h2><ul>{events_html}</ul>
<footer>Generated {escape(now_iso())}. This is a user-controlled case summary, not a bank statement, legal opinion, official complaint acknowledgement or proof that an organisation acted. Store and share it carefully.</footer></main></body></html>"""
