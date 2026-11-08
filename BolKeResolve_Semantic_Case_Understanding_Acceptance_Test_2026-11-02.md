# Acceptance Test — Semantic Case Understanding

## Before testing

1. Extract this project into a fresh folder.
2. Copy the existing `.env` into the folder without sharing it.
3. Confirm `OPENAI_API_KEY` is configured on the server and `BOLKE_MULTIMODAL_MODEL` names a model enabled for the account.
4. Start the app with `run_windows.bat` and open `http://127.0.0.1:8000`.
5. Hard refresh with `Ctrl + F5`.
6. Start a new Live Resolution and enable **Let AI understand my case and personalise each response**. The feature is opt-in; without consent or a configured provider the app uses rule-based matching.

## Scenario A — natural-language Meesho refund

Say or type:

> I ordered products from Meesho for ₹3,000. The order was cancelled because some products were unavailable. It has been over a week. I contacted support and they said the refund is being processed.

Finish the initial story. Expected:

- The case summary should mention Meesho, ₹3,000, order cancellation, support contact and pending/in-process refund as user-reported facts.
- It should not ask again whether support was contacted or whether the refund was initiated if that information was understood.
- It should ask only the next missing fact that changes the next action (for example, the promised refund date or number of working days).
- The AI status should say semantic interpretation was used only if the provider call actually succeeded.

Answer:

> The refund covers the whole order, ma'am.

Expected:

- The workflow should accept full-order scope.
- It must not repeat the full-order vs partial-refund question.
- It should advance to the next missing fact.

## Scenario B — a genuinely different issue in the same conversation

After the Meesho story, say:

> This is actually a separate Google Pay UPI transfer. The money was debited but the shop did not receive it.

Expected:

- It recognises a new payment-transaction issue rather than forcing it into the old Meesho refund workflow.
- The new issue-specific amount/status/merchant facts do not silently inherit from the previous refund.
- The historical Meesho conversation remains in the case timeline.
- It asks for the next material transaction detail and does not invent a support route.

## Scenario C — correction

Say:

> Sorry, I said seven days earlier. It has actually been twelve working days.

Expected:

- The case records this as a correction/newer value, retaining history rather than hiding the earlier statement.
- The next question/action reflects twelve working days.

## Scenario D — consent control

1. Open **AI and privacy** while a case is active.
2. Disable AI case understanding.
3. Send a new case update.
4. Confirm the status says rule-based guidance is being used.
5. Re-enable consent and send another update.
6. Confirm the setting is saved to that case and the UI reports whether interpretation was actually used.

## Scenario E — provider unavailable

Temporarily remove the server-side key in a test environment and restart.

Expected:

- The app explains that semantic case understanding is unavailable.
- The app does not claim the user's story was understood by AI.
- Existing deterministic rule-based guidance, text input and evidence capture remain usable.

## Safety checks

- Never enter OTPs, UPI PINs, passwords, full card numbers or remote-access codes.
- Do not treat a model-generated fact as independently verified.
- Do not allow the model to create a phone number, support URL, refund deadline or legal claim.
- Keep raw audio/image processing under their separate, explicit feature permissions.
