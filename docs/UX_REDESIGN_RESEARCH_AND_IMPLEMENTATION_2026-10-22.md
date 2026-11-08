# BolKeResolve — Focused UX Redesign & Implementation Report
**Date:** 22 October 2026  
**Baseline:** `BolKeResolve_Voice_First_Case_Support_2026-10-22.zip`  
**Scope:** Homepage clarity, guided chat usability, and concise post-creation case workspace.

## Executive summary

The screenshots show three concrete UX problems:
1. Guided chat visually imitates a phone/WhatsApp interface and places seven issue choices, voice controls, a composer and privacy messaging in a small vertical area. This makes the user work to understand what to do first and risks implying that this is an actual WhatsApp connection.
2. The homepage has a coherent palette and useful issue cards, but the hero needs a stronger value proposition and more evidence of the outcome users receive. The lower issue/how-it-works sections feel like a list of features rather than a compelling, concrete promise.
3. The saved case opens into several competing cards and a dense side rail. The recommended next action should dominate. Progress tracking, exports and history matter, but should be secondary until a user asks for them.

This update is a focused implementation, not a full brand rebuild. It keeps the existing backend, case model, official support directory, voice transcription endpoint, evidence handling, timeline, exports and provider adapters.

## Changes implemented

### 1. Homepage
- Added a compact “From confusion to a clear next step” outcome card over the hero image.
- Added a small “One case. One next move.” proof chip.
- Improved hero typography, spacing, trust pills, image shape and visual depth.
- Refined issue cards with clearer spacing, hover feedback and more comfortable tap targets.
- Strengthened the “Less form. More follow-through.” section and trust band.
- Added responsive behavior for small phones; the hero stacks instead of squeezing two columns.

### 2. Guided chat
- Changed the in-app chat title to **Your resolution guide** and explicitly labels it “Private guided chat · not WhatsApp”. This avoids suggesting a live WhatsApp integration where none is connected.
- Changed the visual from a narrow faux-phone frame to a wider, calm conversation surface.
- Reduced the initial issue choices to four common paths: refund missing, payment failed, UPI pending, and unknown payment.
- Moved less-common issue choices into an “Another issue” disclosure, reducing first-screen cognitive load.
- Preserved the existing language selector, voice capture/transcription, editable message composer, safety copy and save-case action.
- Made the chat and voice controls responsive on small devices.

### 3. Case after creation
- Preserved the primary recommended action and official support links.
- Made the support-route cards more compact and single-column, with concise action-oriented text.
- Reduced padding and type scale on the main action, resolution plan and “details to add” panel.
- Grouped case progress, export/portability actions and the honesty note into a collapsed **Track this case** disclosure. The user sees the immediate action first, but all existing tools remain available.
- Kept the workspace tabs so advanced details are still reachable.
- Bumped the service-worker cache from `bolkeresolve-shell-v2` to `v3`, forcing the public shell to refresh while preserving the rule that `/api/` and case data are never cached.

## Research basis and pattern extraction

I did not inspect 1,000 websites individually, and this report does not claim that. Instead, I checked a focused set of authoritative consumer support and service-design references that directly map to this product.

### Patterns from official support journeys
- **National Consumer Helpline (NCH):** multi-channel access, multiple Indian languages, official complaint registration, and a docket/reference after registration. Product implication: BolKeResolve should help prepare users and route them to the correct official channel; it should not imply that merely saving a BolKeResolve case is a formal complaint.  
  Source: https://consumeraffairs.gov.in/pages/nch
- **NCH Convergence Program:** a national grievance route spanning portal, app, UMANG, WhatsApp and phone; the official channel issues a docket and routes grievances to participating organisations. Product implication: show the right official route and help users keep its reference and follow-up date.  
  Source: https://consumerhelpline.gov.in/public/convergenceprogram
- **PhonePe grievance policy:** issue-specific entry points and a staged escalation ladder. Product implication: recommend the organisation’s own first-level route when appropriate, then make escalation legible rather than displaying every option at once.  
  Source: https://www.phonepe.com/grievance-policy/app
- **Google Pay complaint handling:** distinct complaint channels and escalation stages, with different hours and expected response windows. Product implication: make channel, stage and stated timeline specific to the organisation and avoid inventing a guarantee.  
  Source: https://pay.google.com/intl/en_in/about/business/policy/complaints-handling/

### Patterns from service-design guidance
- **U.S. Web Design System — Progress easily:** progressively disclose complex form questions, start with easier questions, give actionable validation and avoid overwhelming users. Product implication: show four common issue paths first and tuck secondary options away.  
  Source: https://designsystem.digital.gov/patterns/complete-a-complex-form/progress-easily/
- **Home Office User-Centred Design Manual:** visible labels, useful hints, grouped related controls and avoiding placeholder-only instructions. Product implication: keep voice language selection and text input labelled and maintain a typed fallback.  
  Source: https://design.homeoffice.gov.uk/accessibility/interactivity/forms
- **GOV.UK WCAG 2.2 guidance:** understandable, operable, perceivable and robust interactions; support keyboard, screen reader and different input modes. Product implication: voice must supplement, not replace, text and clear controls; tap targets and disclosures should remain accessible.  
  Source: https://www.gov.uk/service-manual/helping-people-to-use-your-service/understanding-wcag?level=0
- **Microsoft speech disclosure guidance:** voice experiences need clear capability disclosure, transparent cues and accessible alternatives. Product implication: clearly label this as an in-app guided chat and state that voice is transcribed after recording stops.  
  Source: https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/speech-service/text-to-speech/concepts/disclosure-patterns

## Product strategy: what creates defensible user value

A generic LLM can explain consumer rights or draft a message. BolKeResolve should focus on the workflow around the problem:
1. **Official route matching:** choose a trusted official support destination based on the organisation, issue and risk; preserve source and review date.
2. **One-tap message preparation:** use confirmed facts, not guesses, to generate an editable message; offer copy, email draft and WhatsApp handoff without claiming it was sent.
3. **Evidence readiness:** show only the two or three pieces of evidence relevant to this issue; allow marking them ready without claiming that the file itself was verified.
4. **Follow-up memory:** remind the user what they did, what the organisation said, the ticket/reference number they entered and when they planned to follow up. Notifications must be explicitly configured.
5. **Escalation readiness:** if the first channel fails or its stated timeline passes, show the next legitimate route and the information the user needs to carry forward.
6. **Honest status:** distinguish user-reported actions from external verification. Never show a refund as confirmed unless the user reports it or a properly integrated authoritative source confirms it.
7. **Safety-first branch:** for suspected unauthorised payments, prioritize the bank/payment provider’s official fraud reporting route and appropriate official cybercrime reporting, rather than an ordinary merchant message.

The moat is not “AI chat”. It is **a reliable, source-backed, low-friction action and follow-up system**.

## What remains future work

These items are deliberately not represented as completed in this ZIP:
- Real automated sending or ticket creation with organisations. Most providers do not expose a universal public complaint-submission API. Until a formal integration/partnership exists, the product prepares the message and opens the official channel for the user.
- Guaranteed push/email/SMS reminders. A due date can be saved, but delivery requires a configured notification provider and consent.
- Merchant support directory coverage at scale. Each entry needs official-source verification, a last-reviewed timestamp and a safe fallback when no reliable route is known.
- Live browser visual QA on multiple devices and a user test with people unfamiliar with the product.
- Live Gnani transcription testing using the operator’s own API credentials.
- Public deployment checks: privacy notice, production HTTPS, backup/retention policy, rate limiting, monitoring and access control.

## Validation status

- Existing automated suite: run from project root with `PYTHONPATH=. pytest -q`.
- Python compile: `python -m compileall -q backend`.
- JavaScript syntax: `node --check frontend/app.js`.
- Browser/device validation is still required after extraction. A local Chromium walkthrough was not available in this environment, so this report does not claim visual QA passed.

## Manual acceptance test

1. Open the homepage at 1440px and 390px widths. Check hero copy, image overlay, issue cards and absence of horizontal overflow.
2. Open Guided chat. Confirm the label says “Private guided chat · not WhatsApp”, only four common issue choices appear initially, and “Another issue” expands.
3. Test typed intake and voice input. Select Hindi or Marathi, record a short fictional complaint, stop, review/correct the transcript, and submit.
4. Create a fictional refund case. Confirm the primary next action and matched official support destinations are the visual focus.
5. Confirm “Track this case” is collapsed initially and expands to reveal progress, portability and exports.
6. Verify case tabs, draft preparation, evidence, progress updates, export and delete still work.
7. In Chrome DevTools, test 390px, 768px and desktop widths. Check keyboard focus, disclosure state, microphone permission errors and console errors.
8. Test a suspected-fraud scenario; safety guidance must appear before ordinary merchant contact.

## Bottom line

This iteration is intentionally quieter: fewer choices on first view, clearer distinction between in-app chat and WhatsApp, a more outcome-focused homepage, and a saved-case screen that prioritizes the next action. It keeps the existing engine and exposes supporting complexity only when the user needs it.
