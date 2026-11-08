"""Smoke tests that the site shell and its first-party design assets are served locally."""
import os
import tempfile
import unittest

_FRONTEND_TEST_DATA = tempfile.TemporaryDirectory(prefix="bolke-frontend-test-")
os.environ["BOLKE_DATA_DIR"] = _FRONTEND_TEST_DATA.name

from fastapi.testclient import TestClient  # noqa: E402
from backend import main  # noqa: E402


class FrontendAssetTests(unittest.TestCase):
    def setUp(self):
        self.auth_state = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        self.client = TestClient(main.app)

    def tearDown(self):
        self.client.close()
        main.AUTH_REQUIRED = self.auth_state

    def test_intake_layout_has_responsive_overflow_guardrails(self):
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn(".workspace-shell,.form-layout,.form-card,.side-rail,.intake-helper-rail", css)
        self.assertIn("@media(max-width:900px){.workspace-title{align-items:flex-start}.form-layout{grid-template-columns:minmax(0,1fr);gap:18px}", css)
        self.assertIn("@media(max-width:620px){.workspace-shell{width:calc(100% - 28px)}", css)

    def test_adaptive_language_picker_exposes_all_ten_native_script_choices(self):
        index = (main.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        app_js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="languagePickerTrigger"', index)
        self.assertIn('role="dialog" aria-label="Choose voice language"', index)
        self.assertIn('id="languageCode"', index)
        for code in ("hi-IN", "en-IN", "mr-IN", "bn-IN", "gu-IN", "kn-IN", "ml-IN", "pa-IN", "ta-IN", "te-IN"):
            with self.subTest(language=code):
                self.assertIn(f'data-voice-lang="{code}"', index)
                self.assertIn(f'"{code}"', app_js)
        self.assertIn('Escape', app_js)

    def test_site_shell_and_javascript_are_served(self):
        home = self.client.get("/")
        js = self.client.get("/app.js")
        css = self.client.get("/design-v2.css")
        homepage_polish = self.client.get("/homepage-polish.css")
        self.assertEqual(home.status_code, 200)
        self.assertIn("BolKeResolve", home.text)
        self.assertIn("resolutionPreview", home.text)
        self.assertIn('value="Other payment issue" selected', home.text, "new cases must start with a neutral issue selection")
        self.assertIn("/assets/bolke-guide-avatar.webp", home.text)
        self.assertIn('data-wa-pick="UPI payment pending / recipient not credited"', home.text)
        self.assertNotIn("openclipart.org/image/800px/285004", home.text)
        self.assertEqual(js.status_code, 200)
        self.assertIn("refine-resolution", js.text)
        self.assertIn("delete-case", js.text)
        self.assertIn("UPI payment pending / recipient not credited", js.text)
        self.assertIn("function detectLanguageCode(text)", js.text)
        self.assertIn("case-workspace-tabs", js.text)
        self.assertIn("Choose for me · 10 languages", home.text)
        self.assertNotIn("Requires Gnani access", home.text)
        self.assertIn("no-store", home.headers.get("cache-control", ""))
        self.assertIn("configResponse=await fetch('/api/config'", js.text)
        self.assertEqual(css.status_code, 200)
        self.assertIn("guide-photo-character", css.text)
        self.assertEqual(homepage_polish.status_code, 200)
        self.assertIn("home-issue-picker.wrap", homepage_polish.text)
        self.assertIn("live-room-ai-consent[hidden]", homepage_polish.text)



    def test_case_detail_type_scale_is_not_the_legacy_microtype_system(self):
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn("--type-body: 1rem", css)
        self.assertIn("--type-copy: .9375rem", css)
        self.assertIn(".case-detail-v2 .case-step-body p", css)
        self.assertIn("font-size: var(--type-copy) !important", css)
        self.assertIn(".case-detail-v2 .case-field-v2 input", css)
        self.assertIn("@media (max-width: 760px)", css)

    def test_live_room_has_pause_commit_and_visible_user_controlled_camera(self):
        index = (main.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "live-room.css").read_text(encoding="utf-8")
        sw = (main.FRONTEND_DIR / "sw.js").read_text(encoding="utf-8")
        self.assertIn('id="liveRoomOpenCameraButton"', index)
        self.assertIn('id="liveRoomCaseAIActiveConsent"', index)
        self.assertIn('id="authForgotPassword"', index)
        self.assertIn('id="accountRecoveryDialog"', index)
        self.assertIn('id="passwordResetConfirmForm"', index)
        self.assertIn('data-case-filter="waiting"', index)
        self.assertIn('id="casesSearch"', index)
        self.assertIn("async function handleAuthActionUrl()", js)
        self.assertIn("function renderCasesList()", js)
        self.assertIn('id="liveRoomCaseAIStatus"', index)
        self.assertIn('id="liveRoomCaseAIUnavailable"', index)
        self.assertIn('id="liveRoomTranslationUnavailable"', index)
        self.assertIn('id="liveRoomWorkspaceCaseId"', index)
        self.assertIn('id="liveRoomExportDialog"', index)
        self.assertIn('id="liveRoomTranscriptEditDialog"', index)
        self.assertIn("function liveRoomUpdateCaseAIConsent(allowed)", js)
        self.assertIn("function liveRoomRenderCaseAIStatus(used=null)", js)
        self.assertIn("function liveRoomSetOptionalConsent(selector,available,statusSelector)", js)
        self.assertIn("label.style.setProperty('display','none','important')", js)
        self.assertIn('class="live-room-ai-consent" hidden', index)
        self.assertNotIn("microphone audio is streamed to Gnani", index)
        self.assertIn("function liveRoomOpenExportDialog()", js)
        self.assertIn("function liveRoomRestoreConversation(c)", js)
        self.assertIn("/conversation-turns/", js)
        self.assertIn("/blueprint-upgrade.css", index)
        self.assertIn("function liveRoomHandleLocalSilence(rms)", js)
        self.assertIn("JSON.stringify({type:'commit'})", js)
        self.assertIn("Provider VAD has already closed this segment", js)
        self.assertIn("function liveRoomScheduleAutoAdvance()", js)
        self.assertIn("function liveRoomQueueSpeechSegment(text,languageCode)", js)
        self.assertIn("async function liveRoomFlushSpeechBuffer", js)
        self.assertIn("liveRoomFinishStory({automatic:true})", js)
        self.assertIn("const q=hasAdaptive?workflow.next_question:resolution.next_question", js)
        self.assertIn(".live-room-camera-toggle", css)
        self.assertIn('aria-pressed="false"', index)
        self.assertIn("position:static;max-height:none;overflow:visible", css)
        self.assertIn("bolkeresolve-shell-v47", sw)
        self.assertIn(".live-room-transcript{max-height:min(56vh,520px);min-height:160px;overflow:auto", css)
        self.assertIn(".live-room-camera-stage:has(.live-room-camera-placeholder:not([hidden])){height:108px", css)
        self.assertIn("@media(max-width:1120px)", css)
        self.assertIn(".live-room-transcript{max-height:min(52vh,440px);min-height:150px;overflow:auto", css)
        self.assertIn(".live-room-turn{max-width:min(88%,760px)", css)
        self.assertIn("root.scrollTop=root.scrollHeight", js)

    def test_live_room_uses_readable_type_and_full_width_transcript_review(self):
        css = (main.FRONTEND_DIR / "live-room.css").read_text(encoding="utf-8")
        sw = (main.FRONTEND_DIR / "sw.js").read_text(encoding="utf-8")
        self.assertIn("#liveRoomAudioTranscript", css)
        self.assertIn("width: 100%", css)
        self.assertIn("font-size: .95rem", css)
        self.assertIn("line-height: 1.65", css)
        self.assertIn("@media (max-width: 620px)", css)
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn("bolkeresolve-shell-v47", sw)

    def test_live_room_capture_and_filler_turns_do_not_replay_guidance(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "live-room.css").read_text(encoding="utf-8")
        # Short fillers and capture intents are not case answers. In particular,
        # they must not fall through to the old auto-finish path and replay a plan.
        self.assertIn("function liveRoomIsLowInformationUtterance(text)", js)
        self.assertIn("return {suppressAutoAdvance:true}", js)
        self.assertIn("if(autoAdvance&&!turnResult?.suppressAutoAdvance)", js)
        self.assertIn("const captureIntent=liveRoomOfferCaptureFromIntent(clean)", js)
        self.assertIn("camera:'Choose Open camera", js)
        self.assertIn("screen:'Choose the relevant tab or window", js)
        self.assertIn("function liveRoomWorkflowSignature(workflow)", js)
        self.assertIn("if(!repeatedState)liveRoomSpeak", js)
        self.assertIn("const displayedGuidance=new Set()", js)
        self.assertIn(".live-room-evidence-filters button{display:inline-flex", css)
        self.assertIn("writing-mode:horizontal-tb", css)
        self.assertIn(".live-room-support-draft-card textarea", css)
        self.assertIn("@media(max-width:760px)", css)


    def test_site_typography_uses_readable_scale_for_case_details_and_live_room(self):
        design = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        live = (main.FRONTEND_DIR / "live-room.css").read_text(encoding="utf-8")
        sw = (main.FRONTEND_DIR / "sw.js").read_text(encoding="utf-8")
        self.assertIn("--type-body: 1rem", design)
        self.assertIn("--type-copy: .9375rem", design)
        self.assertIn(".case-detail-v2 .case-step-body p", design)
        self.assertIn("font-size: var(--type-copy) !important", design)
        self.assertIn(".live-room-view .live-room-turn { font-size: 1rem", live)
        self.assertIn("bolkeresolve-shell-v47", sw)

    def test_homepage_includes_safe_interactive_sample_resolution_demo(self):
        index = (main.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        for marker in ("sampleCaseDemo", "data-demo-case=\"failed-upi\"", "data-demo-case=\"refund-delayed\"", "sampleDemoResult", "aria-live=\"polite\""):
            with self.subTest(marker=marker):
                self.assertIn(marker, index)
        self.assertIn("/api/resolution/preview", js)
        self.assertIn("sampleDemoResultMarkup", js)
        self.assertIn("No case was created", js)
        self.assertIn("No payment was checked", js)
        self.assertIn("sample-demo-layout", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn('data-scroll="sampleCaseDemo">See a sample case', index)

    def test_fastest_safe_path_uses_inline_decision_chips_and_preserves_confirmed_answers(self):
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn("result.next_question||null", js)
        self.assertIn('data-action="use-fastpath-answer"', js)
        self.assertIn("previewResolution({skipExtraction:true})", js)
        self.assertIn("result.fastest_path?.label", js)
        self.assertIn(".fastest-path-options", css)
        self.assertIn(".fastest-path-option:focus-visible", css)
        self.assertIn("prefers-reduced-motion:reduce", css)

    def test_saved_case_fastest_path_questions_are_interactive_and_recalculate_guidance(self):
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn("function savedCaseFastPathQuestionMarkup(resolution)", js)
        self.assertIn('data-action="answer-case-fastpath"', js)
        self.assertIn("activeCaseSnapshot=c", js)
        self.assertIn("async function answerSavedCaseFastPath(button)", js)
        self.assertIn("await loadCase(currentCaseId);await refreshCaseCountOnly()", js)
        self.assertIn("No bank, payment app or merchant records were checked", js)
        self.assertIn("${savedCaseFastPathQuestionMarkup(resolution)}", js)
        self.assertIn(".case-fastpath-saved", css)

    def test_homepage_and_guided_chat_prioritise_outcomes_and_progressive_disclosure(self):
        index = (main.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn("From confusion to a clear next step", index)
        self.assertIn("Private guided chat · not WhatsApp", index)
        self.assertIn('class="wa-more-issues"', index)
        self.assertIn('data-wa-pick="Suspected fraud or unauthorised transaction"', index)
        self.assertIn(".hero-outcome-card", css)
        self.assertIn(".wa-more-issues", css)

    def test_case_page_uses_focused_workspace_tabs_and_compact_sticky_summary(self):
        app_js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        for selector in ("case-snapshot-strip", "case-tools-menu", "case-workspace-tabs", "case-guided-focus", "caseFullPlanDisclosure", "caseOverviewDetailsDisclosure", "data-tab-panel"):
            with self.subTest(selector=selector):
                self.assertIn(selector, app_js)
        self.assertIn(".case-workspace-tabs", css)
        self.assertIn(".case-tools-menu", css)
        self.assertIn(".case-guided-primary", css)
        self.assertIn("@media(max-width:760px)", css)
        self.assertIn("async function saveCaseDetails", app_js)
        self.assertIn("refresh-guidance", app_js)

    def test_case_workspace_selection_keeps_tabs_visible_and_scrolls_panel_into_view(self):
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn("if(toolsMenu)toolsMenu.open=tab!=='overview'", js)
        self.assertIn("requestAnimationFrame(()=>target?.scrollIntoView({behavior:'auto',block:'start'}))", js)
        self.assertNotIn("if(toolsMenu)toolsMenu.open=false;return;", js)
        self.assertIn("#casePanelPrep,#casePanelProgress{width:100%;max-width:min(1280px,100%);margin-inline:auto;min-width:0;}", css)
        self.assertIn(".case-combined-panel-intro{width:100%;max-width:none;margin:0 0 12px;", css)

    def test_anchor_sections_and_view_switches_avoid_sticky_header_clipping(self):
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn("window.scrollTo({top:0,behavior:'auto'})", js)
        self.assertIn(".home-issue-picker,\n.home-how,\n.home-sample-demo,", css)
        self.assertIn("scroll-margin-top:calc(var(--site-header-height) + 18px)", css)
        self.assertIn(".wa-intro{position:static;align-self:start;}", css)

    def test_sample_demo_columns_stretch_and_case_panels_share_grid_alignment(self):
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn(".sample-demo-layout{align-items:stretch;gap:clamp(12px,1.6vw,20px);}", css)
        self.assertIn(".sample-demo-controls{display:flex;flex-direction:column;align-self:stretch;}", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn("@keyframes casePanelEnter", css)

    def test_case_workspace_has_three_simple_destinations_and_keeps_secondary_actions_accessible(self):
        from pathlib import Path
        js = (Path(__file__).resolve().parents[1] / "frontend" / "app.js").read_text(encoding="utf-8")
        tabs = js.split('<nav class="case-workspace-tabs"', 1)[1].split('</nav>', 1)[0]
        self.assertEqual(tabs.count('role="tab" data-case-tab='), 3)
        for label in ("Plan &amp; details", "Prepare &amp; contact", "Progress"):
            with self.subTest(label=label):
                self.assertIn(label, tabs)
        self.assertIn('id="caseEvidenceDisclosure"', js)
        self.assertIn('id="caseMessageDisclosure"', js)
        self.assertIn('id="caseActivityDisclosure"', js)
        self.assertIn("const aliases={evidence:'prep',draft:'prep',outcome:'progress',activity:'progress',tracking:'progress'}", js)
        self.assertIn("switchCaseTab('activity')", js)

    def test_provenance_and_reply_review_are_compact_and_user_confirmed(self):
        index = (main.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        for marker in ("caseProvenanceDisclosure", "Where these details came from", "caseReplyReviewDisclosure", "caseReplyReviewForm", "caseReplyReviewResult", "Save interpretation to timeline"):
            with self.subTest(marker=marker):
                self.assertIn(marker, js)
        self.assertIn("/reply-review/preview", js)
        self.assertIn("/reply-review/confirm", js)
        self.assertIn("Nothing is saved yet", js)
        self.assertIn("The preview does not save the pasted reply", js)
        self.assertIn(".case-provenance-disclosure", css)
        self.assertIn(".case-reply-review-result", css)
        self.assertIn("@media(max-width:620px){.case-provenance-grid", css)

    def test_living_passport_and_case_inbox_bridge_are_integrated_as_optional_case_tools(self):
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        for marker in ("Check details", "caseInboxBridgeDisclosure", "Case Inbox Bridge", "review-evidence", "create-case-inbox", "review-inbound-email", "Confirm interpretation and clear email copy", "Attachments (not imported)"):
            with self.subTest(marker=marker):
                self.assertIn(marker, js)
        self.assertIn("/evidence-review/confirm", js)
        self.assertIn("/inbox/messages/", js)
        self.assertIn(".case-inbox-address-card", css)
        self.assertIn(".case-evidence-review-results", css)

    def test_unconfigured_email_bridge_has_a_working_manual_reply_import_fallback(self):
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn('id="caseInboxManualReplyForm"', js)
        self.assertIn('id="caseInboxManualReplyText"', js)
        self.assertIn("async function reviewManualInboxReply(event)", js)
        self.assertIn("origin:'case-inbox-manual'", js)
        self.assertIn("/reply-review/preview", js)
        self.assertIn("/reply-review/confirm", js)
        self.assertIn("raw reply is not saved to the case database", js)
        self.assertIn(".case-inbox-manual-import", css)

    def test_service_worker_bumps_shell_and_keeps_api_network_only(self):
        from pathlib import Path
        sw = (Path(__file__).resolve().parents[1] / "frontend" / "sw.js").read_text(encoding="utf-8")
        self.assertIn("bolkeresolve-shell-v47", sw)
        self.assertNotIn("const CACHE_NAME = 'bolkeresolve-shell-v29'", sw)
        self.assertIn("if (url.pathname.startsWith('/api/')) return;", sw)
        self.assertIn("/styles.css", sw)
        self.assertIn("/design-v2.css", sw)
        self.assertIn("/share-token.js", sw)

    def test_start_live_resolution_click_does_not_pass_dom_event_as_case_id(self):
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        self.assertIn("$('#liveRoomStartButton')?.addEventListener('click',()=>startLiveRoom());", js)
        self.assertIn("if(typeof existingCaseId!=='string')existingCaseId=null;", js)
        self.assertIn("showToast(message,'error')", js)
        self.assertNotIn("$('#liveRoomStartButton')?.addEventListener('click',startLiveRoom);", js)

    def test_live_room_has_retryable_microphone_profiles_and_video_frame_validation(self):
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        html = (main.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "live-room.css").read_text(encoding="utf-8")
        for marker in ("liveRoomRetryVoiceButton", "liveRoomPopulateMicDevices", "liveRoomApplyMicSettings", "liveRoomWaitForVideoFrame", "voice_profile=${encodeURIComponent(voiceProfile)}", "message.code||message.error_code"):
            with self.subTest(marker=marker):
                self.assertIn(marker, js)
        self.assertIn('id="liveRoomMicProfile"', html)
        self.assertIn('id="liveRoomMicDevice"', html)
        self.assertIn(".live-room-voice-settings-popover", css)
        self.assertIn("liveRoomStopTracks(recordStream)", js)

    def test_live_room_has_explicit_speech_commit_and_saved_voice_note_fallback(self):
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        html = (main.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "live-room.css").read_text(encoding="utf-8")
        for marker in (
            'id="liveRoomFinishSpeakingButton"', 'id="liveRoomVoiceNoteButton"',
            "function liveRoomFinishSpeaking()", "JSON.stringify({type:'commit'})",
            "async function liveRoomBlobToWav(blob)", "new OfflineContextClass(1,frameCount,sampleRate)",
            "async function liveRoomStartVoiceNote()", "async function liveRoomStopVoiceNote()",
            "liveRoomUploadFile(original,'audio_recording',{skipAudioTranscription:true})", "originalType.includes('ogg')", "originalType.includes('mp4')", "await liveRoomStopVoiceNote()",
            "liveRoomMuted=true", "liveRoomRestoreMicAfterVoiceNote", "function liveRoomVideoHasVisibleImage(video)",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, js if marker not in ('id="liveRoomFinishSpeakingButton"', 'id="liveRoomVoiceNoteButton"') else html)
        self.assertIn(".live-room-voice-note.is-recording", css)
        self.assertIn("String(file.type||'').startsWith('audio/')", js)
        self.assertIn("['webm','mp4'].includes(ext)?await liveRoomBlobToWav(file):file", js)
        self.assertIn("!options.skipAudioTranscription", js)

    def test_case_overview_exposes_saved_evidence_and_one_click_open_all_action(self):
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "live-room.css").read_text(encoding="utf-8")
        for marker in (
            "const overviewEvidenceHtml=files.length?", "case-overview-evidence-items",
            "data-action=\"open-evidence\"", "else if(action==='open-evidence')",
            "case-overview-evidence-item", "View all ${files.length}",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, js)
        self.assertIn(".case-overview-evidence-items", css)

    def test_saved_case_evidence_uses_inline_previews_for_images_video_audio_and_pdf(self):
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        self.assertIn("const inlineUrl=`${rawUrl}?inline=true`", js)
        self.assertIn("case-evidence-image-preview", js)
        self.assertIn("case-evidence-video-preview", js)
        self.assertIn("case-evidence-audio-preview", js)
        self.assertIn("case-evidence-pdf-preview", js)
        self.assertIn("Download original ↓", js)

    def test_original_guide_art_is_locally_available_as_webp(self):
        large = self.client.get("/assets/bolke-guide.webp")
        avatar = self.client.get("/assets/bolke-guide-avatar.webp")
        self.assertEqual(large.status_code, 200)
        self.assertEqual(avatar.status_code, 200)
        self.assertIn("image/webp", large.headers.get("content-type", ""))
        self.assertIn("image/webp", avatar.headers.get("content-type", ""))
        self.assertGreater(len(large.content), 10_000)
        self.assertGreater(len(avatar.content), 5_000)

    def test_payment_facts_local_fallback_is_served_as_svg(self):
        fallback = self.client.get("/assets/payment-facts-fallback.svg")
        self.assertEqual(fallback.status_code, 200)
        self.assertIn("image/svg+xml", fallback.headers.get("content-type", ""))
        self.assertIn(b"Review transaction details", fallback.content)

    def test_guided_chat_has_multilingual_voice_input_and_read_aloud_controls(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn('id="waVoiceButton"', html)
        self.assertIn('id="waLanguageCode"', html)
        self.assertIn('id="waVoiceStatus"', html)
        for code in ("hi-IN", "en-IN", "mr-IN", "bn-IN", "gu-IN", "kn-IN", "ml-IN", "pa-IN", "ta-IN", "te-IN"):
            with self.subTest(language=code):
                self.assertIn(f'value="{code}"', html)
        self.assertIn("/api/voice/transcribe", js)
        self.assertIn("waSpeak(text)", js)
        self.assertIn("waVoiceTick()", js)
        self.assertIn("Stop and transcribe", js)
        self.assertIn("Nothing is sent for transcription until you stop", js)
        self.assertIn("Voice is ready. Your transcript will appear for review before you send it.", js)
        self.assertIn("Voice input is not available in this session. You can type your story instead.", js)
        self.assertNotIn("anonymous production voice also requires", js)
        self.assertNotIn("BOLKE_PUBLIC_VOICE_ENABLED=true", js)
        self.assertIn(".wa-voice-controls", css)
        self.assertIn("@media(max-width:760px)", css)
        self.assertIn("Your words are transcribed for you to review before saving.", html)
        self.assertNotIn("Microphone audio is streamed to Gnani", html)

    def test_guided_case_screen_prioritises_one_action_and_collapses_secondary_tools(self):
        from pathlib import Path
        js = (Path(__file__).resolve().parents[1] / "frontend" / "app.js").read_text(encoding="utf-8")
        overview = js.split('<section id="casePanelOverview"', 1)[1].split('</section>\n      <section id="casePanelPrep"', 1)[0]
        self.assertIn('id="caseToolsMenu"', js)
        self.assertIn('id="caseFullPlanDisclosure"', overview)
        self.assertIn('id="caseOverviewDetailsDisclosure"', overview)
        self.assertIn('id="casePrimaryAction"', js)
        self.assertIn('case-guided-primary" data-case-tab="${completionTarget}"', js.split('const primaryActionCard = `', 1)[1].split('`;', 1)[0])
        self.assertIn("if(primaryAction)primaryAction.hidden=tab!=='overview'", js)
        self.assertNotIn('case-guided-primary" data-case-tab="draft"', overview)
        self.assertNotIn('${supportRoutesHtml}', overview)
        self.assertIn('${supportRoutesHtml}', js.split('<section id="casePanelPrep"', 1)[1].split('<section id="casePanelProgress"', 1)[0])
        self.assertIn('id="caseActionPackDisclosure"', js)
        self.assertIn('data-case-tab="overview">← Back to your next step', js)

    def test_visual_alignment_pass_keeps_palette_and_reorders_primary_case_action(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        self.assertLess(js.index("${primaryActionCard}"), js.index('<section class="case-snapshot-strip"'))
        self.assertIn(".case-primary-next-action[hidden]{display:none!important;}", css)
        self.assertIn(".whatsapp-shell{", css)
        self.assertIn(".wa-composer input{height:48px;border:1px solid", css)
        self.assertIn(".sample-demo-layout{grid-template-columns:minmax(300px,.86fr)", css)
        self.assertIn(".case-snapshot-strip{grid-template-columns:repeat(2,minmax(0,1fr));}", css)

    def test_sample_demo_auto_loads_and_recalculates_when_scenario_changes(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        self.assertIn("runSampleDemo();", js.split("$$('[data-demo-case]')", 1)[1].split("function sampleDemoResultMarkup", 1)[0])
        self.assertIn("if($('#sampleDemoResult'))runSampleDemo();", js)
        self.assertIn("panel.setAttribute('aria-busy','true')", js)
        self.assertIn("Preparing the selected example.", html)
        self.assertNotIn("Choose a scenario and reveal how BolKeResolve", html)

    def test_case_workspace_surfaces_specific_official_support_destinations(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn("supportDestinations=Array.isArray(resolution.support_destinations)", js)
        self.assertIn("Official support for your situation", js)
        self.assertIn("MATCHED TO YOUR CASE", js)
        self.assertIn("safeHttpsUrl(destination.url)", js)
        self.assertIn("data-case-tab=\"draft\">Prepare message", js)
        self.assertIn(".case-support-route-grid", css)
        self.assertIn(".case-support-route.is-urgent", css)
        self.assertIn("@media(max-width:760px){.case-support-routes", css)

    def test_voice_ui_does_not_expose_provider_configuration_details(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        app_js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("Gnani access", html)
        self.assertNotIn("Requires Gnani access", html)
        self.assertNotIn("This Gnani key does not accept", app_js)
        self.assertIn("/api/extraction/preview", app_js)
        self.assertIn("scheduleTextExtraction", app_js)

    def test_live_room_audio_transcript_editor_is_full_width(self):
        css = (main.FRONTEND_DIR / "live-room.css").read_text(encoding="utf-8")
        sw = (main.FRONTEND_DIR / "sw.js").read_text(encoding="utf-8")
        self.assertIn("#liveRoomEvidenceReview #liveRoomAudioTranscript", css)
        self.assertIn("width: 100% !important", css)
        self.assertIn("font: 400 1rem/1.7", css)
        self.assertIn("bolkeresolve-shell-v47", sw)

if __name__ == "__main__":
    unittest.main()


class LanguageFallbackInteractionTests(unittest.TestCase):
    def test_auto_detection_rejection_preserves_audio_and_retries_after_language_choice(self):
        from pathlib import Path
        app_js = (Path(__file__).resolve().parents[1] / "frontend" / "app.js").read_text(encoding="utf-8")
        self.assertIn("pendingTranscriptionBlob=wav", app_js)
        self.assertIn("transcribeRecordedAudio(audio,choice.dataset.voiceLang)", app_js)
        self.assertIn("Choose the language you spoke, and we’ll try this same recording again.", app_js)
        self.assertNotIn("We couldn’t match the spoken language", app_js)
        self.assertIn("lastExtractionText=''", app_js)
        self.assertIn("/api/extraction/preview", app_js)
        self.assertNotIn("This Gnani key does not accept Auto-detect", app_js)

class AdaptiveIntakeAndWhatsAppUiTests(unittest.TestCase):
    def test_new_case_form_is_a_true_two_stage_wizard(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        self.assertEqual(html.count('data-intake-panel="'), 2)
        self.assertEqual(html.count('data-intake-progress="'), 2)
        self.assertIn('STEP 1 OF 2', html)
        self.assertIn('STEP 2 OF 2', js)
        self.assertNotIn('data-intake-panel="3"', html)
        for identifier in ("intakeNextButton", "intakeBackButton", "intakeActionBar", "intakeStageStatus", "intakeEvidenceToggle", "intakeEvidencePanel"):
            with self.subTest(identifier=identifier):
                self.assertIn(f'id="{identifier}"', html)
        self.assertIn("function setIntakeStep(step", js)
        self.assertIn("[data-intake-panel]", js)
        self.assertIn(".intake-action-bar", css)
        self.assertIn("[hidden]{display:none!important}", css)

    def test_homepage_uses_a_compact_issue_first_hierarchy(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn('id="commonIssues"', html)
        self.assertIn('class="home-issue-grid"', html)
        self.assertIn('class="home-how-grid"', html)
        # The three explainer cards must use different task-aligned photo sources,
        # descriptive alt text and distinct local fallbacks (no duplicate portrait).
        for photo_id in ("4307713", "6613956", "5237652"):
            with self.subTest(photo_id=photo_id):
                self.assertIn(f"/photos/{photo_id}/pexels-photo-{photo_id}.jpeg", html)
        self.assertIn('data-fallback="/assets/man-fallback.jpg"', html)
        self.assertIn('data-fallback="/assets/payment-facts-fallback.svg"', html)
        self.assertIn('data-fallback-alt="Illustration of a payment receipt and verified transaction details"', html)
        self.assertIn('data-fallback="/assets/hero-fallback.jpg"', html)
        self.assertIn(".home-how-image-story img", css)
        self.assertIn("scroll-snap-type:x mandatory", css)
        self.assertNotIn('class="step-grid step-grid-photo"', html)
        self.assertNotIn('class="scene-grid"', html)
        self.assertIn(".home-issue-grid{grid-template-columns:repeat(3", css)
        self.assertIn('class="home-issue-more"', html)
        self.assertIn('class="home-issue-secondary-grid"', html)
        self.assertIn("@media(max-width:760px)", css)

    def test_issue_cards_sync_to_case_type_and_message_uses_case_context(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn('data-start-issue="Refund not received"', html)
        self.assertIn('data-issue-choice value="Refund not received"', html)
        self.assertIn("function syncIssueChoiceFromSelect()", js)
        self.assertIn("if(key==='issue_type')syncIssueChoiceFromSelect()", js)
        self.assertIn("draft-context-strip", js)
        self.assertIn("Message text", js)
        self.assertIn(".draft-context-strip", css)
        self.assertIn("message-language-heading", js)

    def test_whatsapp_handoff_never_falls_back_to_generic_wa_me(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="whatsappIntegrationNote"', html)
        self.assertIn('id="openWhatsAppButton"', html)
        self.assertIn("if(!whatsappCloudApiReady||!whatsappBusinessNumber)", js)
        self.assertIn("Continue here instead", js)
        self.assertIn("You can start your case in this chat instead", js)
        self.assertIn("/api/cases/${encodeURIComponent(currentCaseId)}/whatsapp-link", js)
        self.assertNotIn(":'https://wa.me/'", js)
        self.assertIn('data-case-event="response_received"', js)

class CaseWorkspaceVisualHierarchyTests(unittest.TestCase):
    def test_home_payment_issue_choices_use_consistent_first_party_vector_icons(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        cards = html.split('class="home-issue-grid"', 1)[1].split('</div>', 1)[0]
        secondary = html.split('class="home-issue-secondary-grid"', 1)[1].split('</div>', 1)[0]
        self.assertGreaterEqual(cards.count('<svg viewBox="0 0 24 24">'), 2)
        self.assertGreaterEqual(secondary.count('class="home-issue-card'), 5)
        self.assertIn('data-start-issue="Suspected fraud or unauthorised transaction"', cards)
        self.assertIn(".home-issue-icon svg", css)
        self.assertIn(".home-issue-card:hover .home-issue-arrow", css)

    def test_prep_kit_is_split_into_overview_checklist_and_followup_panels(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        for token in ("action-pack-overview-grid", "action-pack-checklist-section", "action-pack-lower-grid", "action-pack-sources-grid"):
            with self.subTest(token=token):
                self.assertIn(token, js)
                self.assertIn(token, css)
        self.assertIn('role="progressbar"', js)
        self.assertIn("aria-valuenow", js)

    def test_activity_timeline_has_latest_first_filterable_events_and_private_note(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn('data-activity-filter="all"', js)
        self.assertIn('data-activity-filter="progress"', js)
        self.assertIn('data-activity-kind="${activityKind(e)}"', js)
        self.assertIn("No updates in this category yet.", js)
        self.assertIn("Newest first", js)
        self.assertIn(".sort((a,b)=>", js)
        self.assertIn("case-activity-summary-card", js)
        self.assertIn(".case-activity-item:before", css)
        self.assertIn(".case-activity-filter[aria-pressed=true]", css)
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr))", css)
        self.assertIn(".case-activity-filter-empty:not([hidden])", css)


class ResolutionSprintExperienceTests(unittest.TestCase):
    def test_first_pass_result_lives_in_story_step_and_full_plan_is_collapsible(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        panel_one = html.split('data-intake-panel="1"', 1)[1].split('data-intake-panel="2"', 1)[0]
        panel_two = html.split('data-intake-panel="2"', 1)[1].split('id="intakeActionBar"', 1)[0]
        self.assertIn('id="previewResolutionButton"', panel_one)
        self.assertIn('id="resolutionPreview"', panel_one)
        self.assertNotIn('id="previewResolutionButton"', panel_two)
        self.assertIn("Get your next step before filling in the details", panel_one)
        self.assertIn('id="backToSprintResultButton"', panel_two)
        self.assertIn('id="paymentStatus"', panel_two)
        self.assertIn('id="contactedSupport"', panel_two)
        self.assertIn('id="intakeEvidenceToggle"', panel_two)
        self.assertIn('id="safeDataCheck"', panel_two)
        self.assertIn('id="createCaseButton"', html)
        self.assertNotIn('data-intake-panel="3"', html)
        self.assertIn('<details class="resolution-full-plan"', js)
        self.assertIn("YOUR FIRST-PASS NEXT MOVE", js)
        self.assertIn("resolutionPreviewSequence", js)
        self.assertIn(".resolution-sprint-launch", css)
        self.assertIn(".resolution-first-move", css)

    def test_focuses_common_issues_without_removing_secondary_issue_paths(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        primary = html.split('class="home-issue-grid"', 1)[1].split('</div>', 1)[0]
        secondary = html.split('class="home-issue-secondary-grid"', 1)[1].split('</div>', 1)[0]
        self.assertEqual(primary.count('class="home-issue-card'), 3)
        self.assertIn('data-start-issue="Refund not received"', primary)
        self.assertIn('data-start-issue="Failed UPI payment"', primary)
        self.assertIn('data-start-issue="Suspected fraud or unauthorised transaction"', primary)
        self.assertGreaterEqual(secondary.count('class="home-issue-card'), 5)
        self.assertIn('.home-issue-more>summary', css)
        self.assertIn('.home-issue-secondary-grid', css)

    def test_homepage_promises_immediate_value_and_case_view_has_direct_actions(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn("Know your next move", html)
        self.assertIn("Get my next step", html)
        self.assertIn('case-guided-primary', js)
        self.assertIn('Prepare support message', js)
        self.assertIn('data-case-tab="prep"', js)
        self.assertIn('data-case-tab="progress"', js)
        self.assertNotIn('data-case-tab="evidence">Check evidence', js)
        self.assertNotIn('data-case-tab="outcome">Record outcome', js)
        self.assertIn(".case-guided-primary", css)

    def test_anonymous_preview_is_explicitly_public_but_case_routes_remain_private(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        main_py = (root / "backend" / "main.py").read_text(encoding="utf-8")
        app_js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        self.assertIn('"/api/extraction/preview", "/api/resolution/preview"', main_py)
        self.assertIn("enforce_public_preview_rate_limit", main_py)
        self.assertIn("name==='cases'||name==='detail'||name==='liveRoom'", app_js)
        self.assertIn("pendingAuthAction='create-case'", app_js)
        self.assertIn("Sign in or create a private account to save this Resolution Passport", app_js)

class PrivacyAndAccountDeletionUXTests(unittest.TestCase):
    def test_account_deletion_controls_are_secondary_confirmed_and_disclose_limits(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        html = (root / "frontend" / "index.html").read_text(encoding="utf-8")
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn('id="accountDataControls"', html)
        self.assertIn('id="deleteAccountDialog"', html)
        self.assertIn('id="deleteAccountPassword"', html)
        self.assertIn('id="deleteAccountConfirm"', html)
        self.assertIn("/api/auth/account", js)
        self.assertIn("Signed in as", html)
        self.assertIn("cannot recall downloaded exports", html)
        self.assertIn(".account-delete-dialog::backdrop", css)
        self.assertIn(".account-delete-submit:disabled", css)

    def test_privacy_page_discloses_self_service_deletion_and_stays_marked_as_draft(self):
        from pathlib import Path
        page = (Path(__file__).resolve().parents[1] / "frontend" / "privacy.html").read_text(encoding="utf-8")
        self.assertIn("DRAFT FOR THE OPERATOR", page)
        self.assertIn("Account &amp; privacy", page)
        self.assertIn("does not recall downloaded or exported copies", page)

class CommitmentReconciliationFrontendTests(unittest.TestCase):
    def test_commitment_workflow_is_integrated_into_existing_case_tools(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        js = (root / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (root / "frontend" / "design-v2.css").read_text(encoding="utf-8")
        main_py = (root / "backend" / "main.py").read_text(encoding="utf-8")
        passport_py = (root / "backend" / "passport.py").read_text(encoding="utf-8")
        for marker in (
            "Commitments &amp; conditions", "Find a possible commitment", "CONDITION-AWARE COMMITMENT RECONCILIATION",
            "data-commitment-relation", "source authenticity not independently verified",
            "transcribe-commitment-audio", "preview-commitment", "confirm-commitment",
            "reconcile-commitment", "delete-commitment",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, js)
        for route in (
            "/commitments/preview", "/commitments/confirm", "/commitments/{commitment_id}/reconcile",
        ):
            with self.subTest(route=route):
                self.assertIn(route, main_py)
        self.assertIn("commitment_exports", passport_py)
        self.assertIn(".commitment-card", css)


    def test_optional_ai_checkboxes_are_hidden_when_the_provider_is_unavailable(self):
        index = (main.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "experience-refresh.css").read_text(encoding="utf-8")
        final_css = (main.FRONTEND_DIR / "homepage-polish.css").read_text(encoding="utf-8")
        self.assertIn('id="liveRoomCaseAIUnavailable"', index)
        self.assertIn('id="liveRoomTranslationUnavailable"', index)
        self.assertIn("label.hidden=!enabled", js)
        self.assertIn("label.style.setProperty('display','none','important')", js)
        self.assertIn('class="live-room-ai-consent" hidden', index)
        self.assertIn('.live-room-ai-consent[hidden]', css)
        self.assertIn('display: none !important', css)
        self.assertIn('.live-room-option-unavailable[hidden]', css)
        self.assertIn('.live-room-ai-consent-card .live-room-ai-option label.live-room-ai-consent[hidden]', final_css)
        self.assertIn('data-available="false"', final_css)

    def test_account_access_is_visible_and_local_auth_is_enabled(self):
        index = (main.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        env = (main.FRONTEND_DIR.parent / ".env.example").read_text(encoding="utf-8")
        self.assertIn('id="accountAccessButton"', index)
        self.assertIn('id="authGateCloseButton"', index)
        self.assertIn('id="authModeToggle"', index)
        self.assertIn('aria-modal="true" role="dialog"', index)
        self.assertIn("authGateElement?.addEventListener('keydown'", js)
        self.assertIn("$('#accountAccessButton')?.addEventListener", js)
        self.assertIn("accountsEnabled=state.accounts_enabled!==false", js)
        self.assertIn("BOLKE_ACCOUNTS_ENABLED=true", env)
        self.assertIn("BOLKE_AUTH_REQUIRED=true", env)

    def test_homepage_uses_slow_photo_sequence_and_respects_reduced_motion(self):
        index = (main.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        css = (main.FRONTEND_DIR / "experience-refresh.css").read_text(encoding="utf-8")
        final_css = (main.FRONTEND_DIR / "homepage-polish.css").read_text(encoding="utf-8")
        self.assertIn('href="/homepage-polish.css"', index)
        self.assertIn(".home-issue-picker.wrap", final_css)
        self.assertIn("linear-gradient(132deg, #0a3d35", final_css)
        self.assertIn(".home-issue-card:hover", final_css)
        self.assertIn('hero-photo-slide-story', index)
        self.assertIn('hero-photo-slide-evidence', index)
        self.assertIn('hero-photo-slide-next', index)
        self.assertIn('pexels.com/photos/4307713/', index)
        self.assertIn('pexels.com/photos/6613956/', index)
        self.assertIn('pexels.com/photos/5237652/', index)
        self.assertIn('animation: bolkeHeroPhoto 24s', css)
        self.assertIn('@media (prefers-reduced-motion: reduce)', css)
        self.assertIn('id="heroPhotoPause"', index)
        self.assertIn('.hero-photo-sequence.is-paused .hero-photo-slide', css)
        self.assertIn("heroPhotoPause?.addEventListener('click'", js)
        self.assertIn('.hero-photo-pause { display: none !important; }', css)
        self.assertIn("'/experience-refresh.css'", (main.FRONTEND_DIR / "sw.js").read_text(encoding="utf-8"))
