# BolKeResolve — Start Live Resolution Button Fix

**Date:** 2 November 2026

## Root cause

The frontend registered the Start Live Resolution button as:

```js
$('#liveRoomStartButton')?.addEventListener('click', startLiveRoom);
```

DOM event listeners invoke the callback with a `MouseEvent`. However, `startLiveRoom(existingCaseId = null)` interprets its first argument as an optional saved case ID. A click therefore entered the resume-existing-case branch and attempted to request `/api/cases/[object MouseEvent]` rather than creating a new live draft. The request failed before the workspace was opened.

The resulting error feedback was written into the hidden Live Room workspace, so the visible start card did not show the failure clearly.

## Fix

1. Register the click callback as `() => startLiveRoom()` so no DOM event is passed as the case ID.
2. Add a defensive type guard: non-string `existingCaseId` values are treated as `null`.
3. Display a toast for start failures as well as the in-workspace status message.
4. Bump the service-worker shell cache from v29 to v30 so browsers fetch the corrected frontend JavaScript.
5. Add a frontend regression test that asserts the safe click callback, defensive guard and visible error handling.

## Verification

- `node --check frontend/app.js` — passed.
- `python -m py_compile backend/main.py backend/adaptive_workflow.py backend/support_directory.py` — passed.
- `PYTHONPATH=. pytest -q` — **304 passed, 117 subtests passed**.

## What remains for device verification

Run the app on the target Windows device, open it on `http://127.0.0.1:8000` or its configured HTTPS origin, hard-refresh with `Ctrl+F5`, and click **Start live resolution**. The expected result is a newly created draft case, the Live Room workspace opening, and a microphone permission prompt. Microphone/provider availability still depends on browser permissions and the configured Gnani account.
