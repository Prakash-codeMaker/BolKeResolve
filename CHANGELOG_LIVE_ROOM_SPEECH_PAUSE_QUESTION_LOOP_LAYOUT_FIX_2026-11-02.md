# Live Room speech pause, adaptive question and layout fix — 2 November 2026

## Defects addressed

- An adaptive question could advance correctly in the workflow but be replaced in the case response by a stale legacy question when the adaptive workflow had no current action step.
- Conversational answer variants such as “whole order ma'am” must advance from refund scope to the next unanswered refund fact.
- Transcript segments close to one another could be processed as separate user answers, potentially advancing the next question in the middle of one spoken thought.
- Browser-side `commit` could fire after provider VAD had already closed a segment.
- The default live microphone silence threshold delayed completed transcript delivery more than needed for natural turn-taking.
- The Live Room's nested sticky sidebar could remain visible after the main conversation ended, leaving a large blank area and requiring a second scroll region.
- The camera placeholder needed an explicit, accessible open/close control.

## Implementation

- The adaptive workflow is authoritative whenever present, including intentional `null` question/action states. Legacy case rendering is synchronized from the adaptive workflow rather than allowed to restore an old question.
- Live turn persistence carries newly extracted facts into workflow calculation; refund status phrases such as “in the procedure to give the refund back” are captured as pending, and “contacted their support” / “support said” are captured as prior contact.
- Nearby Gnani final transcript segments are buffered and combined into one user turn for 750 ms before saving and advancing. The pending buffer is flushed before Finish explaining, microphone restart, or session end.
- A short post-transcript grace period advances story/update collection automatically after silence. Existing complete cases continue to recalculate after each saved answer.
- Browser fallback commit is shortened to 1 second and cancelled when provider VAD reports `processing`, avoiding a second commit for the same segment.
- Gnani VAD settings now use 600 ms laptop, 550 ms quiet and 750 ms noisy silence windows; the default short-segment floor is 100 ms for one-word answers.
- The right-hand column uses normal page scrolling instead of its own sticky nested scrollbar. The explicit camera button reports its open/closed state with `aria-pressed`.
- Service-worker shell cache bumped to v32.

## Validation

- Full Python unittest suite: 310 passed.
- `node --check frontend/app.js`: passed.
- `python -m compileall -q backend tests`: passed.
- Includes API-level regression covering the screenshot flow: Flipkart refund in process → user says “Whole order ma'am” → next question becomes refund timeline; the old refund-scope question does not return.
- No live Gnani account or physical microphone/camera session was available in this environment. Hardware/provider acceptance testing is still required.

## Provider basis

Gnani's realtime STT documentation states that its server-side VAD detects speech boundaries and emits a transcript for each completed segment; `x-min-silence-ms` controls segment-close latency, 600–900 ms is suggested for natural conversation, 300–400 ms for short commands, and `x-min-segment-ms` near 100 ms helps retain one-word answers. The docs also confirm that `commit` immediately closes the open utterance. See https://docs.gnani.ai/api/STT/stt-websocket.
