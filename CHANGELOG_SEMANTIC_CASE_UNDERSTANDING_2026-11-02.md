# Semantic Case Understanding — 2026-11-02

- Added opt-in structured interpretation of the complete saved case conversation for mixed-language answers, corrections, new details and new issue detection.
- Added strict JSON Schema output with a JSON fallback for configured models that do not support strict schema mode. All semantic fact updates still require an exact supporting quote in saved user text and pass field-specific validation.
- Kept workflow stage selection, evidence requests and official destinations within the reviewed deterministic backend. Added a constrained response composer that can only explain the selected question/action.
- Added a reversible in-session AI privacy control and an explicit status showing whether semantic interpretation was used. Consent for case interpretation remains separate from translation consent and per-image visual analysis consent.
- Added tests for strict-schema fallback and rejection of unquoted fact updates.
- Bumped the service-worker shell cache to v33.

AI understanding requires a server-side `OPENAI_API_KEY`, a supported configured model, and the user's explicit opt-in. Without them, the app falls back to rule-based matching.
