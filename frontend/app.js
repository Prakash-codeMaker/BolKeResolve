const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => [...root.querySelectorAll(s)];
let deferredInstallPrompt=null;
const installAppButton=$('#installAppButton');
window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();deferredInstallPrompt=event;if(installAppButton)installAppButton.hidden=false;});
installAppButton?.addEventListener('click',async()=>{if(!deferredInstallPrompt){showToast('To install, use your browser menu and choose Install app or Add to Home screen.');return;}deferredInstallPrompt.prompt();try{const result=await deferredInstallPrompt.userChoice;if(result?.outcome==='accepted')showToast('BolKeResolve install requested.');else showToast('You can install BolKeResolve later from your browser menu.');}catch(_){showToast('Use your browser menu to install BolKeResolve.');}deferredInstallPrompt=null;if(installAppButton)installAppButton.hidden=true;});
window.addEventListener('appinstalled',()=>{deferredInstallPrompt=null;if(installAppButton)installAppButton.hidden=true;showToast('BolKeResolve was installed. Case data still requires a connection and is not stored offline.');});
if('serviceWorker' in navigator && (location.protocol==='https:'||location.hostname==='localhost'||location.hostname==='127.0.0.1')){window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));}
// Keep photo-led sections visually complete if a third-party image host is blocked or offline.
function attachImageFallbacks(){
  $$('img[data-fallback]').forEach(img=>{
    const fallback=()=>{
      const path=img.dataset.fallback;
      if(!path || img.dataset.fallbackUsed==='1') return;
      img.dataset.fallbackUsed='1'; img.removeEventListener('error',fallback); if(img.dataset.fallbackAlt) img.alt=img.dataset.fallbackAlt; img.src=path;
    };
    img.addEventListener('error',fallback,{once:true});
    if(img.complete && img.naturalWidth===0) fallback();
  });
}
attachImageFallbacks();
const heroPhotoSequence=$('.hero-photo-sequence');
const heroPhotoPause=$('#heroPhotoPause');
heroPhotoPause?.addEventListener('click',()=>{
  const paused=heroPhotoSequence?.classList.toggle('is-paused')||false;
  heroPhotoPause.setAttribute('aria-pressed',String(paused));
  heroPhotoPause.setAttribute('aria-label',paused?'Play homepage photo sequence':'Pause homepage photo sequence');
  heroPhotoPause.innerHTML=paused?'▶ <span>Play</span>':'Ⅱ <span>Pause</span>';
});
const languageNames = {"auto":"Choose for me · 10 languages","hi-IN":"Hindi / Hinglish","en-IN":"English (India)","mr-IN":"Marathi","bn-IN":"Bengali","gu-IN":"Gujarati","kn-IN":"Kannada","ml-IN":"Malayalam","pa-IN":"Punjabi","ta-IN":"Tamil","te-IN":"Telugu"};
const adaptiveLanguageLabels={"auto":"✦ Choose for me","hi-IN":"हिंदी · Hinglish","en-IN":"English · India","mr-IN":"मराठी · Marathi","bn-IN":"বাংলা · Bengali","gu-IN":"ગુજરાતી · Gujarati","kn-IN":"ಕನ್ನಡ · Kannada","ml-IN":"മലയാളം · Malayalam","pa-IN":"ਪੰਜਾਬੀ · Punjabi","ta-IN":"தமிழ் · Tamil","te-IN":"తెలుగు · Telugu"};
function closeLanguagePicker(){const panel=$('#languagePickerPanel'),trigger=$('#languagePickerTrigger');if(panel)panel.hidden=true;if(trigger)trigger.setAttribute('aria-expanded','false');}
function openLanguagePicker(){const panel=$('#languagePickerPanel'),trigger=$('#languagePickerTrigger');if(panel)panel.hidden=false;if(trigger)trigger.setAttribute('aria-expanded','true');}
function syncLanguagePicker(){const code=$('#languageCode')?.value||'auto';const label=$('#selectedLanguageLabel');if(label)label.textContent=adaptiveLanguageLabels[code]||languageNames[code]||code;$$('[data-voice-lang]').forEach(button=>{const selected=button.dataset.voiceLang===code;button.classList.toggle('active',selected);button.setAttribute('aria-pressed',String(selected));});}
$('#languagePickerTrigger')?.addEventListener('click',()=>$('#languagePickerPanel')?.hidden?openLanguagePicker():closeLanguagePicker());
$('#languagePickerClose')?.addEventListener('click',()=>{closeLanguagePicker();$('#languagePickerTrigger')?.focus();});
$('#languagePickerPanel')?.addEventListener('click',event=>{const choice=event.target.closest('[data-voice-lang]');if(!choice)return;const select=$('#languageCode');if(select){select.value=choice.dataset.voiceLang;select.dispatchEvent(new Event('change',{bubbles:true}));}syncLanguagePicker();closeLanguagePicker();$('#languagePickerTrigger')?.focus();if(pendingTranscriptionBlob&&choice.dataset.voiceLang!=='auto'){const audio=pendingTranscriptionBlob;pendingTranscriptionBlob=null;transcribeRecordedAudio(audio,choice.dataset.voiceLang);}});
document.addEventListener('click',event=>{if(!event.target.closest('.language-picker-adaptive'))closeLanguagePicker();});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!$('#languagePickerPanel')?.hidden){closeLanguagePicker();$('#languagePickerTrigger')?.focus();}});
syncLanguagePicker();
let currentCaseId = null, activeCaseSnapshot = null, cachedCases = [], selectedEvidenceFiles = [], whatsappBusinessNumber = '', whatsappCloudApiReady = false, whatsappTwilioSandboxConfigured = false, whatsappReminderTemplateConfigured = false, lastDetectedSpeechLanguageCode = null, activeCaseTab = 'overview', pendingTranscriptionBlob = null, currentIntakeStep = 1;
let authRequired = false, accountsEnabled = true, authMode = 'login', signedInUser = null, pendingAuthAction = null, pendingVerificationEmail = '', resolutionPreviewSequence = 0, reviewedReplyDraft = null;
let pendingSharedIntakeToken = '', pendingSharedIntakeData = null, pendingSharedIntakeAttachCaseId = '', preloadedSharedIntakeToken = '';
let audioContext=null, mediaStream=null, processorNode=null, audioSourceNode=null, gainNode=null;
let liveRoomActive=false, liveRoomSessionStartedAt='', liveRoomSessionStartRecorded=false, liveRoomStream=null, liveRoomScreenStream=null, liveRoomAudioContext=null, liveRoomAudioSource=null, liveRoomWorklet=null, liveRoomGain=null, liveRoomSocket=null, liveRoomCaseId=null, liveRoomSessionId='', liveRoomClipRecorder=null, liveRoomClipChunks=[], liveRoomClipTimer=null, liveRoomClipStopPromise=null, liveRoomResolveClipStop=null, liveRoomVoiceNoteRecorder=null, liveRoomVoiceNoteChunks=[], liveRoomVoiceNoteTimer=null, liveRoomVoiceNoteStopPromise=null, liveRoomResolveVoiceNoteStop=null, liveRoomVoiceNoteTracks=null, liveRoomPendingReviewId='', liveRoomSegmentIds=new Set(), liveRoomMuted=false, liveRoomWasMutedBeforeVoiceNote=false, liveRoomScreenCaptureReady=false, liveRoomProcessing=false, liveRoomReconnectTimer=null, liveRoomReconnectAttempts=0, liveRoomAudioFrameCount=0, liveRoomAudioSignalSeen=false, liveRoomTranscriptionTimer=null, liveRoomSpeechProcessingAt=0, liveRoomSpeechStartedAt=0, liveRoomLastVoiceAt=0, liveRoomSilenceCommitTimer=null, liveRoomAutoAdvanceTimer=null, liveRoomCommitSent=false, liveRoomPendingSpeechText='', liveRoomPendingSpeechLanguage='', liveRoomSpeechFlushTimer=null;
let liveRoomTurnQueue=Promise.resolve();
let liveRoomLastAssistantSignature='';
let liveRoomMultilingualAvailable=false, liveRoomVisionAvailable=false, liveRoomAiConsent=false, liveRoomCaseAIAvailable=false, liveRoomCaseAIConsent=false, liveRoomGuidanceOverride=null, liveRoomPendingAiAnalysisId='';
let liveRoomEvidenceFilter='all', liveRoomPendingChecklistKey='', liveRoomSupportDraftEdited='';
let recordingBuffers=[], recordingRate=16000, recordingStartedAt=0, recordingTimer=null, recording=false, toastTimer=null;
function escapeHtml(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function safeHttpsUrl(value){try{const url=new URL(String(value||''));return url.protocol==='https:'?url.href:'';}catch(_){return '';}}
function prettyDate(v){if(!v)return '—';const d=new Date(v);return Number.isNaN(d.getTime())?v:d.toLocaleString(undefined,{day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'});}
function money(v){return v===null||v===undefined||v===''?'Not provided':'₹'+Number(v).toLocaleString('en-IN',{maximumFractionDigits:2});}
function showToast(message,type='success'){const t=$('#toast');t.textContent=message;t.classList.toggle('error',type==='error');t.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.hidden=true,4800);}
async function api(path, options={}){let r;try{r=await fetch(path,{credentials:'same-origin',...options});}catch(_){throw new Error('BolKeResolve could not reach the server. You may be offline; case records and evidence are deliberately not cached offline. Reconnect to load or save a case.');}const ct=r.headers.get('content-type')||'';if(ct.includes('application/json')){const b=await r.json();if(r.status===401&&(authRequired||signedInUser))showAuthGate('Your session may have expired. Sign in again to continue.');if(!r.ok)throw new Error(b.detail||`Request failed (${r.status}).`);return b;}if(!r.ok)throw new Error(`Request failed (${r.status}).`);return r;}
function updateAuthMode(){const registering=authMode==='register';$('#authHeading').textContent=registering?'Create your private space.':'Welcome back.';$('#authIntro').textContent=registering?'Create an account to keep your cases and evidence separated from other users.':'Sign in to keep your cases, evidence and next steps private.';$('#authSubmit').innerHTML=registering?'Create account <span>↗</span>':'Sign in <span>↗</span>';$('#authModeToggle').textContent=registering?'Already have an account? Sign in':'New here? Create an account';$('#authPassword').autocomplete=registering?'new-password':'current-password';$('#authPassword').minLength=registering?12:1;$('#authPasswordHint').textContent=registering?'Use at least 12 characters. Do not reuse your bank password.':'For security, do not use your bank password here.';const forgot=$('#authForgotPassword');if(forgot)forgot.hidden=registering;}
function showAuthGate(message=''){
  if(!authRequired&&!accountsEnabled)return;
  const gate=$('#authGate');if(!gate)return;
  gate.hidden=false;document.body.classList.toggle('auth-locked',!!authRequired);
  const err=$('#authError');if(err){err.textContent=message;err.hidden=!message;}
  const close=$('#authGateCloseButton');if(close)close.hidden=!!authRequired;
  updateAuthMode();
  $('#logoutButton').hidden=true;$('#signedInLabel').hidden=true;
  const securityButton=$('#accountSecurityButton');if(securityButton)securityButton.hidden=true;
  const accessButton=$('#accountAccessButton');if(accessButton)accessButton.hidden=true;
  const accountControls=$('#accountDataControls');if(accountControls)accountControls.hidden=true;
  $('#authEmail')?.focus({preventScroll:true});
}
function hideAuthGate(){
  const gate=$('#authGate');if(gate)gate.hidden=true;document.body.classList.remove('auth-locked');
  const isSignedIn=!!signedInUser;
  $('#logoutButton').hidden=!isSignedIn;$('#signedInLabel').hidden=!isSignedIn;$('#signedInLabel').textContent=signedInUser?.email||'';
  const securityButton=$('#accountSecurityButton');if(securityButton)securityButton.hidden=!isSignedIn;
  const accessButton=$('#accountAccessButton');if(accessButton)accessButton.hidden=!accountsEnabled||isSignedIn;
  const close=$('#authGateCloseButton');if(close)close.hidden=!!authRequired;
  const accountControls=$('#accountDataControls');if(accountControls)accountControls.hidden=!isSignedIn;
  const accountEmail=$('#accountPrivacyEmail');if(accountEmail)accountEmail.textContent=signedInUser?.email||'';
}
async function initialiseApplication(){
  try{
    const r=await fetch('/api/auth/me',{credentials:'same-origin'});
    if(!r.ok)throw new Error(`Session status request failed (${r.status}).`);
    const state=await r.json();
    if(typeof state.auth_required!=='boolean')throw new Error('The server did not return authentication configuration.');
    authRequired=state.auth_required;accountsEnabled=state.accounts_enabled!==false;signedInUser=state.user||null;
    hideAuthGate();loadHealth();loadPublicConfig();
    if(authRequired&&!signedInUser)$('#navCaseCount').textContent='—';else refreshCaseCountOnly();
  }catch(_){
    // Recover the intended mode from public config. Never silently turn a protected
    // deployment into guest mode when the session endpoint is unavailable.
    try{
      const configResponse=await fetch('/api/config',{credentials:'same-origin'});
      if(!configResponse.ok)throw new Error('Public configuration could not be loaded.');
      const config=await configResponse.json();
      if(typeof config.auth_required!=='boolean')throw new Error('Auth mode is unavailable.');
      authRequired=config.auth_required;accountsEnabled=config.accounts_enabled!==false;signedInUser=null;
      hideAuthGate();loadHealth();loadPublicConfig();
      if(authRequired)$('#navCaseCount').textContent='—';else refreshCaseCountOnly();
    }catch(__){
      authRequired=true;accountsEnabled=true;signedInUser=null;
      showAuthGate('Could not verify account status. Check that the server is running, then refresh this page.');
      $('#authForm').hidden=true;$('#authModeToggle').hidden=true;
    }
  }
}
const authGateElement=$('#authGate');
authGateElement?.addEventListener('keydown',event=>{
  if(event.key==='Escape'){
    if(!authRequired){event.preventDefault();pendingAuthAction=null;hideAuthGate();showToast('You can continue as a guest. Sign in any time to use your private account.');}
    else event.preventDefault();
    return;
  }
  if(event.key!=='Tab')return;
  const focusable=$$('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])',authGateElement).filter(el=>!el.hidden&&el.getClientRects().length>0);
  if(!focusable.length){event.preventDefault();authGateElement.focus();return;}
  const first=focusable[0],last=focusable[focusable.length-1];
  if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
  else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
});
$('#accountAccessButton')?.addEventListener('click',()=>{authMode='login';showAuthGate('');});
$('#authGateCloseButton')?.addEventListener('click',()=>{pendingAuthAction=null;hideAuthGate();showToast('You can continue as a guest. Sign in any time to use your private account.');});
$('#authModeToggle')?.addEventListener('click',()=>{authMode=authMode==='login'?'register':'login';$('#authError').hidden=true;$('#authPassword').value='';$('#authVerificationNotice').hidden=true;$('#authResendVerification').hidden=true;pendingVerificationEmail='';updateAuthMode();});
$('#authForm')?.addEventListener('submit',async event=>{
  event.preventDefault();
  const email=$('#authEmail').value.trim(),password=$('#authPassword').value,err=$('#authError'),button=$('#authSubmit');
  err.hidden=true;
  if(!email||!password){err.textContent='Enter your email address and password.';err.hidden=false;return;}
  if(authMode==='register'&&password.length<12){err.textContent='Use at least 12 characters.';err.hidden=false;return;}
  button.disabled=true;button.textContent=authMode==='register'?'Creating account…':'Signing in…';
  try{
    const response=await fetch(`/api/auth/${authMode}`,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
    const body=await response.json();if(!response.ok)throw new Error(body.detail||'Authentication did not complete.');
    if(body.verification_required){pendingVerificationEmail=email;$('#authVerificationNotice').textContent=body.message||'Check your inbox for the verification link.';$('#authVerificationNotice').hidden=false;$('#authResendVerification').hidden=false;$('#authPassword').value='';err.hidden=true;return;}
    authRequired=body.auth_required===true;accountsEnabled=body.accounts_enabled!==false;signedInUser=body.user||null;
    const nextAction=pendingAuthAction;pendingAuthAction=null;
    hideAuthGate();loadHealth();loadPublicConfig();await refreshCaseCountOnly();
    if(nextAction==='live-room'){showView('liveRoom');}
    else if(nextAction==='create-case'){await createCase();}
    else if(nextAction==='cases'){showView('cases');}
    else{showView('home');}
    showToast(authMode==='register'?'Account created. Your cases are private to this account.':'You are signed in.');
  }catch(error){err.textContent=error.message||'Authentication did not complete.';err.hidden=false;}
  finally{button.disabled=false;updateAuthMode();}
});
$('#authResendVerification')?.addEventListener('click',async()=>{
  if(!pendingVerificationEmail)return;
  const button=$('#authResendVerification');button.disabled=true;
  try{const result=await api('/api/auth/verification/resend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:pendingVerificationEmail})});$('#authVerificationNotice').textContent=result.message||'If the account needs verification, an email will be sent.';$('#authVerificationNotice').hidden=false;}
  catch(error){$('#authVerificationNotice').textContent=error.message||'Could not request another verification email.';$('#authVerificationNotice').hidden=false;}
  finally{button.disabled=false;}
});
const accountRecoveryDialog=$('#accountRecoveryDialog');
$('#authForgotPassword')?.addEventListener('click',()=>{
  $('#passwordResetRequestForm').hidden=false;$('#passwordResetConfirmForm').hidden=true;$('#passwordResetRequestFeedback').textContent='';$('#passwordResetConfirmFeedback').textContent='';$('#passwordResetRequestForm').reset();
  if(typeof accountRecoveryDialog?.showModal==='function')accountRecoveryDialog.showModal();else showToast('This browser cannot open account recovery.','error');
});
$('#passwordResetRequestForm')?.addEventListener('submit',async event=>{
  event.preventDefault();const email=$('#passwordResetEmail').value.trim(),feedback=$('#passwordResetRequestFeedback'),button=event.currentTarget.querySelector('[type="submit"]');feedback.textContent='';feedback.classList.remove('is-error');button.disabled=true;button.textContent='Requesting…';
  try{const result=await api('/api/auth/password-reset/request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email})});feedback.textContent=result.message||'If an account exists for that address, a password reset link will be sent.';}
  catch(error){feedback.textContent=error.message||'The reset request could not be completed.';feedback.classList.add('is-error');}
  finally{button.disabled=false;button.textContent='Send reset link';}
});
$('#passwordResetConfirmForm')?.addEventListener('submit',async event=>{
  event.preventDefault();const token=$('#passwordResetConfirmForm').dataset.token||'',password=$('#resetNewPassword').value,confirm=$('#resetConfirmPassword').value,feedback=$('#passwordResetConfirmFeedback'),button=event.currentTarget.querySelector('[type="submit"]');feedback.textContent='';feedback.classList.remove('is-error');
  if(password.length<12||password!==confirm){feedback.textContent=password.length<12?'Use at least 12 characters.':'The two passwords do not match.';feedback.classList.add('is-error');return;}
  button.disabled=true;button.textContent='Saving…';
  try{const result=await api('/api/auth/password-reset/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,new_password:password})});feedback.textContent=result.message||'Password reset. Sign in with your new password.';$('#passwordResetConfirmForm').reset();$('#passwordResetConfirmForm').dataset.token='';setTimeout(()=>accountRecoveryDialog?.close(),900);authMode='login';updateAuthMode();showAuthGate('Your password was reset. Sign in with your new password.');}
  catch(error){feedback.textContent=error.message||'This reset link could not be used. Request a new one.';feedback.classList.add('is-error');}
  finally{button.disabled=false;button.textContent='Save new password';}
});
accountRecoveryDialog?.addEventListener('click',event=>{if(event.target===accountRecoveryDialog)accountRecoveryDialog.close();});
async function handleAuthActionUrl(){
  const url=new URL(window.location.href);const verificationToken=url.searchParams.get('verify_email');const resetToken=url.searchParams.get('reset_password');
  if(verificationToken){
    try{const result=await api('/api/auth/verify-email',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:verificationToken})});authRequired=result.auth_required===true;accountsEnabled=result.accounts_enabled!==false;signedInUser=result.user||null;pendingVerificationEmail='';pendingAuthAction=null;hideAuthGate();loadHealth();loadPublicConfig();await refreshCaseCountOnly();showToast('Your email is verified. Your private account is ready.');}
    catch(error){showAuthGate(error.message||'This verification link is invalid or has expired. Request a new one.');}
    url.searchParams.delete('verify_email');history.replaceState({},'',url.pathname+url.search+url.hash);
  }
  if(resetToken){$('#passwordResetRequestForm').hidden=true;$('#passwordResetConfirmForm').hidden=false;$('#passwordResetConfirmForm').dataset.token=resetToken;url.searchParams.delete('reset_password');history.replaceState({},'',url.pathname+url.search+url.hash);if(typeof accountRecoveryDialog?.showModal==='function')accountRecoveryDialog.showModal();}
}
$('#logoutButton')?.addEventListener('click',async()=>{try{await fetch('/api/auth/logout',{method:'POST',credentials:'same-origin'});}finally{signedInUser=null;cachedCases=[];currentCaseId=null;activeCaseSnapshot=null;hideAuthGate();if(authRequired)showAuthGate('You have signed out.');else{showView('home');refreshCaseCountOnly();showToast('You have signed out. You can continue as a guest.');}}});
const accountSecurityDialog=$('#accountSecurityDialog');
async function loadAccountSessions(){
  const host=$('#accountSessionsList');if(!host)return;
  host.innerHTML='<p>Loading active sessions…</p>';
  try{
    const data=await api('/api/auth/sessions');
    const sessions=Array.isArray(data.sessions)?data.sessions:[];
    host.innerHTML=sessions.length?sessions.map((session,index)=>`<div class="account-session-row"><span class="account-session-dot ${session.is_current?'is-current':''}"></span><div><b>${session.is_current?'This device':'Signed-in session '+(index+1)}</b><small>Signed in: ${escapeHtml(prettyDate(session.created_at))} · Expires: ${escapeHtml(new Date(Number(session.expires_at)*1000).toLocaleString())}</small></div><em>${session.is_current?'Current':'Other session'}</em></div>`).join(''):'<p>No active sessions were found.</p>';
  }catch(error){host.innerHTML=`<p class="blueprint-inline-error">${escapeHtml(error.message||'Could not load sessions.')}</p>`;}
}
$('#accountSecurityButton')?.addEventListener('click',()=>{
  if(!signedInUser){showAuthGate('Sign in to manage your account security.');return;}
  $('#accountSecurityFeedback').textContent='';$('#changePasswordForm')?.reset();
  if(typeof accountSecurityDialog?.showModal==='function'){accountSecurityDialog.showModal();loadAccountSessions();}else showToast('This browser cannot open the account security panel.','error');
});
$('#refreshAccountSessionsButton')?.addEventListener('click',loadAccountSessions);
$('#revokeOtherSessionsButton')?.addEventListener('click',async()=>{
  const button=$('#revokeOtherSessionsButton');if(button)button.disabled=true;
  try{const result=await api('/api/auth/sessions/revoke-others',{method:'POST'});showToast(`${Number(result.revoked_sessions||0)} other session(s) signed out.`);await loadAccountSessions();}
  catch(error){showToast(error.message||'Could not revoke sessions.','error');}
  finally{if(button)button.disabled=false;}
});
$('#changePasswordForm')?.addEventListener('submit',async event=>{
  event.preventDefault();const current=$('#currentAccountPassword').value,newPassword=$('#newAccountPassword').value,confirm=$('#confirmAccountPassword').value,feedback=$('#accountSecurityFeedback'),button=event.currentTarget.querySelector('[type="submit"]');
  feedback.textContent='';feedback.classList.remove('is-error');
  if(newPassword.length<12){feedback.textContent='Use at least 12 characters for the new password.';feedback.classList.add('is-error');return;}
  if(newPassword!==confirm){feedback.textContent='The new password and confirmation do not match.';feedback.classList.add('is-error');return;}
  button.disabled=true;button.textContent='Updating…';
  try{await api('/api/auth/password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password:current,new_password:newPassword})});event.currentTarget.reset();feedback.textContent='Password updated. Other active sessions were signed out.';await loadAccountSessions();showToast('Password updated successfully.');}
  catch(error){feedback.textContent=error.message||'Password update failed.';feedback.classList.add('is-error');}
  finally{button.disabled=false;button.textContent='Update password';}
});
accountSecurityDialog?.addEventListener('click',event=>{if(event.target===accountSecurityDialog)accountSecurityDialog.close();});
const deleteAccountDialog=$('#deleteAccountDialog');
$('#deleteAccountOpenButton')?.addEventListener('click',()=>{
  if(!signedInUser){showToast('Sign in before changing account data.','error');return;}
  const form=$('#deleteAccountForm');form?.reset();const error=$('#deleteAccountError');if(error){error.hidden=true;error.textContent='';}
  if(typeof deleteAccountDialog?.showModal==='function')deleteAccountDialog.showModal();else showToast('This browser cannot open the account deletion dialog. Update your browser to continue.','error');
  $('#deleteAccountPassword')?.focus();
});
$('#deleteAccountCancelButton')?.addEventListener('click',()=>deleteAccountDialog?.close());
deleteAccountDialog?.addEventListener('click',event=>{if(event.target===deleteAccountDialog)deleteAccountDialog.close();});
$('#deleteAccountForm')?.addEventListener('submit',async event=>{
  event.preventDefault();
  const password=$('#deleteAccountPassword')?.value||'',confirmed=!!$('#deleteAccountConfirm')?.checked,error=$('#deleteAccountError'),button=$('#deleteAccountSubmitButton');
  if(!password){error.textContent='Enter your current password to confirm this request.';error.hidden=false;return;}
  if(!confirmed){error.textContent='Confirm that you understand this action cannot be undone.';error.hidden=false;return;}
  button.disabled=true;button.textContent='Deleting account…';error.hidden=true;
  try{
    const result=await api('/api/auth/account',{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({password})});
    deleteAccountDialog.close();signedInUser=null;cachedCases=[];currentCaseId=null;activeCaseSnapshot=null;pendingAuthAction=null;
    const list=$('#casesList');if(list)list.replaceChildren();const detail=$('#caseDetailContent');if(detail)detail.replaceChildren();
    $('#navCaseCount').textContent='—';hideAuthGate();showView('home');
    if(Number(result.evidence_cleanup_pending||0)>0){showToast('Your account is deleted, but the server could not remove one or more evidence files. Contact the site operator for cleanup.','error');}
    else{showToast('Account and active case data deleted. Previously exported copies, external-provider data, and host backups may remain.');}
    $('#authEmail').value='';$('#authPassword').value='';
  }catch(err){error.textContent=err.message||'Account deletion failed. Nothing was confirmed as deleted.';error.hidden=false;}
  finally{const passwordInput=$('#deleteAccountPassword');if(passwordInput)passwordInput.value='';button.disabled=false;button.textContent='Delete account and data';}
});
deleteAccountDialog?.addEventListener('close',()=>{const passwordInput=$('#deleteAccountPassword');if(passwordInput)passwordInput.value='';const confirmInput=$('#deleteAccountConfirm');if(confirmInput)confirmInput.checked=false;});
function setIntakeStep(step,{scroll=true}={}){
  currentIntakeStep=Math.max(1,Math.min(2,Number(step)||1));
  $$('[data-intake-panel]').forEach(panel=>{panel.hidden=Number(panel.dataset.intakePanel)!==currentIntakeStep;});
  $$('[data-intake-progress]').forEach(node=>{const n=Number(node.dataset.intakeProgress);node.classList.toggle('active',n===currentIntakeStep);node.classList.toggle('completed',n<currentIntakeStep);if(n===currentIntakeStep)node.setAttribute('aria-current','step');else node.removeAttribute('aria-current');});
  const labels={1:['STEP 1 OF 2','Tell your story'],2:['STEP 2 OF 2','Review & save']};
  const status=$('#intakeStageStatus');if(status){const [stepLabel,heading]=labels[currentIntakeStep];status.innerHTML=`${stepLabel}<b>${heading}</b>`;}
  const back=$('#intakeBackButton'),next=$('#intakeNextButton'),save=$('#createCaseButton');if(back)back.hidden=currentIntakeStep===1;if(next){next.hidden=currentIntakeStep===2;next.innerHTML='Continue to review &amp; save <span>↗</span>'; }if(save)save.hidden=currentIntakeStep!==2;
  const error=$('#formError');if(error)error.hidden=true;
  if(scroll){const target=$(`[data-intake-panel="${currentIntakeStep}"]`);target?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});}
}
function syncIssueChoiceFromSelect(){const selected=$('#issueType')?.value||'Other payment issue';let secondarySelected=false;$$('[data-issue-choice]').forEach(input=>{input.checked=input.value===selected;if(input.checked&&input.closest('.intake-more-issues'))secondarySelected=true;});const more=$('.intake-more-issues');if(more)more.open=secondarySelected;}
$$('[data-issue-choice]').forEach(input=>input.addEventListener('change',()=>{if(!input.checked)return;const select=$('#issueType');if(select)select.value=input.value;syncIssueChoiceFromSelect();markPreviewStale();}));
syncIssueChoiceFromSelect();
$$('[data-start-issue]').forEach(button=>button.addEventListener('click',()=>{const issue=button.dataset.startIssue||'Other payment issue';showView('new');const select=$('#issueType');if(select&&[...select.options].some(option=>option.value===issue))select.value=issue;syncIssueChoiceFromSelect();setIntakeStep(1,{scroll:false});}));
function showView(name){
  if(name!=='whatsapp'&&waVoiceRecording)waStopVoiceRecording();
  if(authRequired&&!signedInUser&&(name==='cases'||name==='detail'||name==='liveRoom')){pendingAuthAction=name==='liveRoom'?'live-room':'cases';showAuthGate(name==='liveRoom'?'Sign in to keep your live conversation, documents and guidance in a private case.':'Sign in or create a private account to view saved cases. You can still get a first-pass suggestion without signing in.');return;}
  if(name!=='liveRoom'&&liveRoomActive){endLiveRoom({silent:true});}
  const ids={home:'homeView',new:'newView',whatsapp:'whatsappView',liveRoom:'liveRoomView',cases:'casesView',detail:'detailView'};
  const wasNew=$('#newView')?.classList.contains('view-active');
  $$('.view').forEach(v=>v.classList.remove('view-active'));
  $('#'+ids[name])?.classList.add('view-active');
  $$('.nav-link').forEach(b=>b.classList.toggle('active',b.dataset.view===name||(name==='detail'&&b.dataset.view==='cases')));
  $('.main-nav')?.classList.remove('open');
  if(name==='new'&&!wasNew)setIntakeStep(1,{scroll:false});
  window.scrollTo({top:0,behavior:'auto'});
  if(name==='cases')refreshCases();if(name==='detail'&&currentCaseId)loadCase(currentCaseId);if(name==='whatsapp')$('#waMessage')?.focus({preventScroll:true});
}

$('#intakeNextButton')?.addEventListener('click',()=>{
  if(currentIntakeStep===1){const story=$('#description')?.value?.trim()||'';if(story.length<8){setVoiceFeedback('Tell us a little more about what happened, or record your story first.',true);$('#description')?.focus();return;}setIntakeStep(2);return;}
  if(currentIntakeStep===2){const amount=$('#amount');if(amount?.value&&!amount.checkValidity()){amount.reportValidity();return;}return;}
});
$('#intakeBackButton')?.addEventListener('click',()=>setIntakeStep(currentIntakeStep-1));
$('#intakeEvidenceToggle')?.addEventListener('click',()=>{const panel=$('#intakeEvidencePanel'),button=$('#intakeEvidenceToggle');if(!panel||!button)return;panel.hidden=!panel.hidden;button.setAttribute('aria-expanded',String(!panel.hidden));button.classList.toggle('is-open',!panel.hidden);if(!panel.hidden)panel.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'nearest'});});
setIntakeStep(1,{scroll:false});
$$('[data-view]').forEach(b=>b.addEventListener('click',e=>{const v=e.currentTarget.dataset.view;if(v)showView(v);}));
$$('[data-scroll]').forEach(b=>b.addEventListener('click',e=>{
  e.preventDefault(); const target=e.currentTarget.dataset.scroll;
  if(!$('#homeView')?.classList.contains('view-active')) showView('home');
  requestAnimationFrame(()=>$('#'+target)?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'}));
}));
$('#mobileMenu')?.addEventListener('click',()=>$('.main-nav')?.classList.toggle('open'));
function looksLikeEnglishRenderedInDevanagari(text){
  const words=(String(text||'').toLowerCase().match(/[\u0900-\u097f]+/g)||[]);
  const englishSoundalikes=new Set(['आई','आइ','हेव','हैव','नॉट','नोट','गॉट','गोट','दी','द','फ्रॉम','फ्राम','बैक','प्लीज','प्लीज़','माई','हैज़','हैज','बीन','डेज़','डेज','कैन','यू','व्हाट','वॉट','ऑर्डर','फूड','कैंसल','कस्टमर','सपोर्ट','कॉन्टैक्ट','रिफंड']);
  return words.filter(word=>englishSoundalikes.has(word)).length>=3;
}
function inferLanguageCodeFromText(text){
  const value=String(text||'');
  // Some recognition engines render spoken English as Devanagari phonetics. Treat
  // that as likely English for reply/draft language instead of assuming Hindi.
  if(looksLikeEnglishRenderedInDevanagari(value))return 'en-IN';
  if(/[\u0B80-\u0BFF]/.test(value))return 'ta-IN';
  if(/[\u0C00-\u0C7F]/.test(value))return 'te-IN';
  if(/[\u0C80-\u0CFF]/.test(value))return 'kn-IN';
  if(/[\u0D00-\u0D7F]/.test(value))return 'ml-IN';
  if(/[\u0A00-\u0A7F]/.test(value))return 'pa-IN';
  if(/[\u0A80-\u0AFF]/.test(value))return 'gu-IN';
  if(/[\u0980-\u09FF]/.test(value))return 'bn-IN';
  if(/[\u0900-\u097F]/.test(value))return 'hi-IN';
  if(/\b(hai|hain|mera|meri|mere|mujhe|nahi|nahin|paise|paisa|kat gaya|refund nahi|kal|tha|the|ho gaya|kar diya)\b/i.test(value))return 'hi-IN';
  return value.trim()?'en-IN':'en-IN';
}
function caseLanguageCodeFromUI(text){
  // A pinned language choice expresses the user's preferred response language too.
  // Only infer from the story when the user leaves the choice on recognition mode.
  const chosen=$('#languageCode')?.value||'auto';
  if(chosen!=='auto')return chosen;
  if(text&&text.trim())return inferLanguageCodeFromText(text);
  return lastDetectedSpeechLanguageCode||'en-IN';
}
function getResolutionPayload(){
  const supportValue=$('#contactedSupport')?.value??'';
  const amountRaw=$('#amount')?.value?.trim()||'';
  return {
    issue_type:$('#issueType')?.value||'Other payment issue',
    merchant:$('#merchant')?.value?.trim()||'',
    amount:amountRaw&&Number.isFinite(Number(amountRaw))?Number(amountRaw):null,
    payment_date:$('#paymentDate')?.value||'',
    language_code:caseLanguageCodeFromUI($('#description')?.value||''),
    payment_status:$('#paymentStatus')?.value||'unknown',
    contacted_support:supportValue===''?null:supportValue==='yes',
    description:$('#description')?.value?.trim()||''
  };
}
function nchDirectoryMarkup(match){
  if(!match||!match.merchant_input)return '';
  const listed=match.status==='listed_in_reviewed_snapshot';
  const url=safeHttpsUrl(match.source_url||'https://consumerhelpline.gov.in/public/convergencepartners');
  return `<div class="nch-directory-match ${listed?'is-listed':'is-unmatched'}"><span class="nch-directory-match-icon" aria-hidden="true">${listed?'✓':'i'}</span><div class="nch-directory-match-copy"><b>${listed?'Listed in reviewed NCH snapshot':'NCH directory match not confirmed'}</b>${listed&&match.legal_name?`<p>Listed name: ${escapeHtml(match.legal_name)}</p>`:''}<p>${escapeHtml(match.message||'Check the official directory before acting.')}</p><small>Snapshot reviewed ${escapeHtml(match.reviewed_on||'date not recorded')} · not a live lookup</small>${url?`<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Search the full official directory ↗</a>`:''}</div></div>`;
}
function rulebookMarkup(rulebook,extraClass=''){
  if(!rulebook||!rulebook.version)return '';
  const rules=Array.isArray(rulebook.matched_rules)?rulebook.matched_rules:[];
  const items=rules.map(rule=>{const links=(rule.sources||[]).map(source=>{const href=safeHttpsUrl(source.url);return href?`<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">Open official source ↗</a>`:'';}).filter(Boolean).join(' · ');return `<article><h4>${escapeHtml(rule.title||'Applicable guidance')}</h4><p>${escapeHtml(rule.scope||'')}</p><p>${escapeHtml(rule.next_action||'')}</p>${links?`<div>${links}</div>`:''}</article>`;}).join('');
  return `<details class="rulebook-disclosure ${extraClass}"><summary><span>Why this guidance applies <small class="rulebook-summary-meta">Rulebook ${escapeHtml(rulebook.version)} · reviewed ${escapeHtml(rulebook.reviewed_on||'date not recorded')}</small></span><span aria-hidden="true">⌄</span></summary><div class="rulebook-disclosure-body">${items||'<p class="rulebook-caveat">No specific rule matched; this is general guidance.</p>'}<p class="rulebook-caveat">${escapeHtml(rulebook.notice||'Guidance is based on user-reported facts, not a live transaction check.')} Rules and source pages can change; open the official source before relying on timings.</p></div></details>`;
}

function resolutionMarkup(result,canRefine=true){
  if(!result||!result.recommended_steps)return '<p class="muted-note">A resolution plan will appear here.</p>';
  const isUrgent=result.urgency?.level==='urgent';
  const sourceMap=Object.fromEntries((result.official_sources||[]).map(source=>[source.id,source]));
  const steps=(result.recommended_steps||[]).map((item,index)=>{
    const refs=(item.source_ids||[]).map(id=>sourceMap[id]).filter(Boolean).map(source=>`<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.organization)} ↗</a>`).join(' · ');
    return `<li class="resolution-step ${item.priority==='urgent'?'step-urgent':''}"><span class="resolution-step-number">${index+1}</span><div><h4>${escapeHtml(item.title)}</h4><p>${escapeHtml(item.detail)}</p>${item.why?`<small>${escapeHtml(item.why)}</small>`:''}${refs?`<div class="resolution-step-sources">Source: ${refs}</div>`:''}</div></li>`;
  }).join('');
  const first=result.recommended_steps[0]||{};
  const firstRefs=(first.source_ids||[]).map(id=>sourceMap[id]).filter(Boolean).map(source=>`<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.organization)} ↗</a>`).join(' · ');
  const sources=(result.official_sources||[]).map(source=>`<a class="source-chip" href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer"><span>${escapeHtml(source.organization)}</span><b>${escapeHtml(source.title)} ↗</b><small>Reviewed ${escapeHtml(source.reviewed_on||'date not recorded')} · opens official website</small></a>`).join('');
  const missing=(result.missing_information||[]).length?`<div class="resolution-missing"><b>Details that could make this more specific</b><ul>${result.missing_information.map(value=>`<li>${escapeHtml(value)}</li>`).join('')}</ul></div>`:'<p class="case-quiet-copy">No additional information is needed for this first-pass suggestion.</p>';
  const privacy=result.privacy_notice?`<div class="resolution-privacy-notice"><b>Privacy protection applied</b><p>${escapeHtml(result.privacy_notice.message||'Sensitive-looking values were redacted.')}</p><small>Redacted categories: ${escapeHtml((result.privacy_notice.redacted_types||[]).join(', '))}. Check your original wording before saving.</small></div>`:'';
  const routeMatch=result.nch_directory_match?.merchant_input?nchDirectoryMarkup(result.nch_directory_match):'';
  const rulebook=rulebookMarkup(result.rulebook,'resolution-rulebook');
  const nextQuestion=result.next_question||null;
  const questionPrompt=nextQuestion?.prompt||result.clarifying_question||'';
  const questionOptions=(nextQuestion?.options||[]).map(option=>`<button type="button" class="fastest-path-option" data-action="use-fastpath-answer" data-field="${escapeHtml(nextQuestion.field||'')}" data-value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</button>`).join('');
  const question=questionPrompt?`<div class="resolution-question fastest-path-question"><div class="fastest-path-question-heading"><span>ONE QUESTION THAT CAN CHANGE THE NEXT STEP</span><p>${escapeHtml(questionPrompt)}</p></div>${nextQuestion?.why_it_matters?`<small class="fastest-path-why">${escapeHtml(nextQuestion.why_it_matters)}</small>`:''}${questionOptions?`<div class="fastest-path-options" role="group" aria-label="Answer the clarification question">${questionOptions}</div>`:canRefine?`<button type="button" class="button button-outline resolution-refine-button" data-action="refine-resolution" data-field="${escapeHtml(nextQuestion?.field||'')}" data-step="${escapeHtml(nextQuestion?.step||'')}">Add this detail ↗</button>`:''}</div>`:'';
  const rationale=`<p class="resolution-rationale">${escapeHtml(result.classification?.rationale||'')}</p>`;
  const alert=`<div class="resolution-alert ${isUrgent?'urgent':''}"><b>${escapeHtml(result.urgency?.label||'Next steps')}</b><p>${escapeHtml(result.urgency?.message||'')}</p></div>`;
  return `<div class="resolution-result ${isUrgent?'resolution-urgent':''}">
    <div class="resolution-result-heading"><span class="resolution-kicker">${escapeHtml(result.fastest_path?.label||(isUrgent?'SAFETY FIRST':'YOUR FIRST-PASS NEXT MOVE'))}</span><span class="resolution-confidence">${escapeHtml(result.classification?.confidence||'unrated')} confidence</span></div>
    <p class="resolution-issue-label">Suggested issue · ${escapeHtml(result.classification?.issue_type||'Payment issue')}</p>
    ${privacy}
    <section class="resolution-first-move"><span class="resolution-first-move-index">${result.fastest_path?.mode==='clarify'?'ONE DETAIL FIRST':'START HERE'}</span><h3>${escapeHtml(result.fastest_path?.mode==='clarify'?(result.fastest_path.title||'Confirm one detail'):(first.title||'Review the details and choose a next step'))}</h3><p>${escapeHtml(result.fastest_path?.mode==='clarify'?(result.fastest_path.reason||'Your answer helps choose the appropriate route.'):(first.detail||'Review the guidance below and open the official source before acting.'))}</p>${result.fastest_path?.mode==='clarify'?'':first.why?`<small>${escapeHtml(first.why)}</small>`:''}${result.fastest_path?.mode==='clarify'?'':firstRefs?`<div class="resolution-step-sources">Source: ${firstRefs}</div>`:''}</section>
    ${alert}
    ${question}
    <div class="resolution-sprint-actions"><button type="button" class="button button-dark" data-action="sprint-review-details">Review details to save my Passport ↗</button><button type="button" class="button button-outline" data-action="sprint-edit-story">Edit my story</button></div>
    <p class="resolution-preview-trust">This is a first-pass suggestion based on your words. BolKeResolve has not checked your bank, payment app or merchant records, and has not submitted a complaint.</p>
    <details class="resolution-full-plan" ${isUrgent?'open':''}><summary>See all recommended steps, missing details and official sources</summary><div class="resolution-full-plan-body">${rationale}<ol class="resolution-step-list">${steps}</ol>${missing}${sources?`<div class="resolution-sources"><h4>Official sources</h4><div class="resolution-source-grid">${sources}</div></div>`:''}${routeMatch}${rulebook}<p class="resolution-safety"><strong>Safety note:</strong> ${escapeHtml(result.safety_message||'Never share OTPs, payment PINs or passwords.')}</p><div class="resolution-limits">${(result.limits||[]).map(value=>`<span>• ${escapeHtml(value)}</span>`).join('')}</div></div></details>
  </div>`;
}
async function previewResolution({skipExtraction=false}={}){
  const panel=$('#resolutionPreview'),button=$('#previewResolutionButton'),story=$('#description')?.value?.trim()||'';
  if(!panel||!button)return;
  if(story.length<8){panel.hidden=false;panel.innerHTML='<p class="inline-feedback error">Tell us a little more first (at least 8 characters). You can type or record your story; nothing is saved yet.</p>';$('#description')?.focus();return;}
  const requestSequence=++resolutionPreviewSequence;
  button.disabled=true;button.dataset.loading='1';button.innerHTML='<span class="button-spinner"></span> Finding your next step…';panel.hidden=false;panel.innerHTML='<div class="resolution-loading"><span class="loading-orbit"></span><div><b>Finding an appropriate next step</b><p>Checking the facts we can safely extract, then matching your issue to a guided playbook and official sources.</p></div></div>';
  try{
    // On the first run, use reviewable extraction candidates. Inline quick answers have
    // already updated an explicit field and should not be overwritten by extracting the story again.
    if(!skipExtraction){clearTimeout(extractionTimer);await runTextExtraction(story);}
    if(requestSequence!==resolutionPreviewSequence)return;
    const payload=getResolutionPayload();
    const result=await api('/api/resolution/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if(requestSequence!==resolutionPreviewSequence)return;
    panel.innerHTML=resolutionMarkup(result);panel.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'nearest'});
  }catch(err){
    if(requestSequence!==resolutionPreviewSequence)return;
    panel.innerHTML=`<div class="resolution-preview-error"><p class="inline-feedback error">${escapeHtml(err.message)} Your story is still here. You can edit it, try again, or continue to details.</p><button type="button" class="button button-outline" data-action="sprint-review-details">Continue to details ↗</button></div>`;
  }finally{
    if(requestSequence===resolutionPreviewSequence){delete button.dataset.loading;button.disabled=($('#description')?.value?.trim()||'').length<8;button.innerHTML='<span>Get my next step</span><span aria-hidden="true">↗</span>';}
  }
}
$('#resolutionPreview')?.addEventListener('click',event=>{
  const button=event.target.closest('[data-action]');if(!button)return;
  if(button.dataset.action==='sprint-review-details'){setIntakeStep(2);return;}
  if(button.dataset.action==='sprint-edit-story'){setIntakeStep(1);window.setTimeout(()=>$('#description')?.focus({preventScroll:true}),160);return;}
  if(button.dataset.action==='use-fastpath-answer'){
    const field=button.dataset.field||'',value=button.dataset.value||'';
    const selectorMap={payment_status:'#paymentStatus',contacted_support:'#contactedSupport',issue_type:'#issueType'};
    const target=$(selectorMap[field]||'');
    if(!target){showToast('Please update this detail in the case form instead.','error');return;}
    target.value=value;
    if(field==='issue_type')syncIssueChoiceFromSelect();
    // Refresh from the exact confirmed input without rerunning extraction over it.
    previewResolution({skipExtraction:true});
    return;
  }
  if(button.dataset.action!=='refine-resolution')return;
  const field=button.dataset.field||'';
  const selectorMap={description:'#description',issue_type:'#issueType',merchant:'#merchant',amount:'#amount',payment_date:'#paymentDate',payment_status:'#paymentStatus',contacted_support:'#contactedSupport'};
  const target=$(selectorMap[field]||'');
  const step=Number(button.dataset.step)||(target?.id==='description'?1:2);
  setIntakeStep(step);
  window.setTimeout(()=>{if(target?.id==='issueType') $('[data-issue-choice]')?.focus({preventScroll:true});else target?.focus({preventScroll:true});},160);
});
$('#previewResolutionButton')?.addEventListener('click',previewResolution);
$('#backToSprintResultButton')?.addEventListener('click',()=>{setIntakeStep(1);if($('#resolutionPreview')?.hidden)showToast('Your details changed. Run Get my next step again to refresh the suggestion.');else $('#resolutionPreview')?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});});

// Public challenge demo: fictitious stories go through the same deterministic,
// source-backed preview endpoint, but never create or store a consumer case.
const sampleDemoScenarios={
  'failed-upi':{
    issue_type:'Failed UPI payment', merchant:'Sample UPI transaction', amount:1200, payment_date:'', payment_status:'failed', contacted_support:false,
    description:'Mere ₹1,200 account se debit hue, lekin UPI app mein transaction failed dikh raha hai. Refund abhi nahi aaya.'
  },
  'refund-delayed':{
    issue_type:'Refund not received', merchant:'Sample online merchant', amount:850, payment_date:'', payment_status:'refund_pending', contacted_support:true,
    description:'Maine ₹850 ka order cancel kiya tha. Merchant ne refund initiated bola, lekin refund abhi tak account mein nahi aaya. Support ko pehle contact kiya hai.'
  }
};
let activeSampleDemoScenario='failed-upi', sampleDemoRequestSequence=0;
const sampleDemoStories={
  'failed-upi':'“Mere ₹1,200 account se debit hue, lekin UPI app mein payment failed dikh raha hai.”',
  'refund-delayed':'“Maine ₹850 ka order cancel kiya. Merchant says refund initiated, lekin amount abhi tak nahi aaya.”'
};
$$('[data-demo-case]').forEach(button=>button.addEventListener('click',()=>{
  activeSampleDemoScenario=button.dataset.demoCase in sampleDemoScenarios?button.dataset.demoCase:'failed-upi';
  $$('[data-demo-case]').forEach(item=>{const selected=item===button;item.classList.toggle('is-selected',selected);item.setAttribute('aria-pressed',String(selected));});
  const story=$('#sampleDemoStory');if(story)story.textContent=sampleDemoStories[activeSampleDemoScenario];
  sampleDemoRequestSequence++;
  // Keep the result synchronised with the selected scenario; never leave a selected card beside a contradictory empty state.
  runSampleDemo();
}));
function sampleDemoResultMarkup(result){
  const steps=(result?.recommended_steps||[]).slice(0,2);
  const stepMarkup=steps.map((step,index)=>`<li><span class="sample-demo-step-number">${index+1}</span><div><b>${escapeHtml(step.title||'Recommended next step')}</b><p>${escapeHtml(step.detail||'Review the details and choose an official contact route.')}</p></div></li>`).join('');
  const sources=(result?.official_sources||[]).slice(0,3).map(source=>{const href=safeHttpsUrl(source.url);return href?`<a class="sample-demo-source" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer"><span>${escapeHtml(source.organization||'Official source')}</span><b>${escapeHtml(source.title||'Read the guidance')} ↗</b><small>Reviewed ${escapeHtml(source.reviewed_on||'date not recorded')}</small></a>`:'';}).filter(Boolean).join('');
  const missing=(result?.missing_information||[]).slice(0,3);
  const urgency=result?.urgency?.level==='urgent';
  const classification=result?.classification?.issue_type||'Payment or refund issue';
  const confidence=result?.classification?.confidence||'not rated';
  const rationale=result?.classification?.rationale||'';
  const why=result?.recommended_steps?.[0]?.why||'';
  const routeMatch=result?.nch_directory_match?.merchant_input?nchDirectoryMarkup(result.nch_directory_match):'';
  const rulebook=rulebookMarkup(result?.rulebook,'sample-demo-rulebook');
  return `<div class="sample-demo-result-inner"><div class="sample-demo-result-top"><span class="sample-demo-label">ILLUSTRATIVE FIRST-PASS GUIDANCE</span><span class="sample-demo-status ${urgency?'is-urgent':''}">${urgency?'Act promptly':'Review before acting'}</span></div><div class="sample-demo-classification"><span>${escapeHtml(classification)}</span><small>${escapeHtml(confidence)} confidence · based on fictional details</small></div><h3>${escapeHtml(result?.recommended_steps?.[0]?.title||'Review the payment details')}</h3><p class="sample-demo-result-intro">${escapeHtml(result?.recommended_steps?.[0]?.detail||'Confirm the transaction type and the relevant details before choosing a support route.')}</p>${why?`<div class="sample-demo-why"><b>Why this step?</b><p>${escapeHtml(why)}</p></div>`:''}<div class="sample-demo-result-note"><span aria-hidden="true">ⓘ</span><p>${escapeHtml(result?.facts?.statement||'This suggestion is based on the fictional story supplied for this demo.')}</p></div>${rationale?`<details class="sample-demo-rationale"><summary>Why BolKeResolve classified it this way</summary><p>${escapeHtml(rationale)}</p></details>`:''}${routeMatch}${rulebook}${stepMarkup?`<ol class="sample-demo-steps">${stepMarkup}</ol>`:''}${missing.length?`<div class="sample-demo-missing"><b>What would make this more specific?</b><ul>${missing.map(item=>`<li>${escapeHtml(item)}</li>`).join('')}</ul></div>`:''}${sources?`<div class="sample-demo-sources"><h4>Check the official guidance</h4><div>${sources}</div></div>`:''}<div class="sample-demo-assurance"><span>✓</span> This result is illustrative. No payment was checked, no case was created and no complaint was sent.</div></div>`;
}
async function runSampleDemo(){
  const panel=$('#sampleDemoResult'),button=$('#runSampleDemoButton');if(!panel||!button)return;
  const scenario=sampleDemoScenarios[activeSampleDemoScenario]||sampleDemoScenarios['failed-upi'];
  const sequence=++sampleDemoRequestSequence;
  button.disabled=true;button.dataset.loading='1';button.innerHTML='<span class="button-spinner" aria-hidden="true"></span> Building sample plan…';
  panel.setAttribute('aria-busy','true');
  panel.innerHTML='<div class="sample-demo-loading"><span class="loading-orbit" aria-hidden="true"></span><div><h3>Preparing your selected example</h3><p>Matching this fictional story to the relevant resolution playbook and official guidance.</p></div></div>';
  try{
    const result=await api('/api/resolution/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(scenario)});
    if(sequence!==sampleDemoRequestSequence)return;
    panel.innerHTML=sampleDemoResultMarkup(result);
  }catch(error){
    if(sequence!==sampleDemoRequestSequence)return;
    panel.innerHTML=`<div class="sample-demo-empty sample-demo-error"><span class="sample-demo-result-icon" aria-hidden="true">!</span><h3>The sample could not load.</h3><p>${escapeHtml(error.message||'The guidance service is unavailable right now.')}</p><p>Please try again. No case was created.</p></div>`;
  }finally{
    if(sequence===sampleDemoRequestSequence){panel.removeAttribute('aria-busy');delete button.dataset.loading;button.disabled=false;button.innerHTML='Refresh example result <span aria-hidden="true">↻</span>';}
  }
}
$('#runSampleDemoButton')?.addEventListener('click',runSampleDemo);
// The default scenario is selected, so show its first-pass result immediately.
if($('#sampleDemoResult'))runSampleDemo();
async function loadHealth(){try{const h=await api('/api/health');$('#recordState').textContent=h.voice_input_configured?'Voice is ready when you are':'Voice is unavailable right now';const status=$('#serviceSummary');if(status)status.textContent=h.voice_input_configured?'Voice input available':'Typing is available';const attribution=$('#gnaniModelAttribution');if(attribution){attribution.hidden=!h.voice_input_configured;attribution.textContent=h.voice_input_configured?'Gnani AI voice transcription is configured. Live automatic language detection uses Prisma v3.0; review the transcript before saving.':'Voice transcription is not configured in this environment.';}}catch(_){$('#recordState').textContent='Ready when you are';const attribution=$('#gnaniModelAttribution');if(attribution){attribution.hidden=false;attribution.textContent='Voice-provider status could not be checked. Type your story or check configuration before recording.';}}}
function setVoiceFeedback(msg,isError=false){const b=$('#voiceFeedback');b.textContent=msg;b.classList.toggle('error',isError);b.hidden=false;}
function formatDuration(sec){sec=Math.max(0,Math.floor(sec));return `${String(Math.floor(sec/60)).padStart(2,'0')}:${String(sec%60).padStart(2,'0')}`;}
function updateRecordingTimer(){const sec=(Date.now()-recordingStartedAt)/1000;$('#recordTimer').textContent=`${formatDuration(sec)} / 01:00`;if(sec>=60)stopRecording();}
async function startRecording(){if(!navigator.mediaDevices?.getUserMedia){setVoiceFeedback('Microphone recording is unavailable here. Open the app on http://127.0.0.1:8000 or type your complaint.',true);return;}try{mediaStream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true}});const Ctx=window.AudioContext||window.webkitAudioContext;audioContext=new Ctx({sampleRate:16000});await audioContext.resume();recordingRate=audioContext.sampleRate;audioSourceNode=audioContext.createMediaStreamSource(mediaStream);processorNode=audioContext.createScriptProcessor(4096,1,1);gainNode=audioContext.createGain();gainNode.gain.value=0;recordingBuffers=[];processorNode.onaudioprocess=e=>{if(recording)recordingBuffers.push(new Float32Array(e.inputBuffer.getChannelData(0)));};audioSourceNode.connect(processorNode);processorNode.connect(gainNode);gainNode.connect(audioContext.destination);recording=true;recordingStartedAt=Date.now();$('#recordButton').classList.add('recording');$('#recordIcon').textContent='■';$('#recordLabel').textContent='Stop and transcribe';$('#recordState').textContent='Listening… speak naturally';$('#waveBars').classList.add('active');$('#voiceFeedback').hidden=true;recordingTimer=setInterval(updateRecordingTimer,250);setVoiceFeedback('Recording on this device. Audio is sent for transcription only after you stop recording.');}catch(err){cleanupRecording();setVoiceFeedback('We couldn’t start the microphone. Check browser microphone permission or type your complaint instead.',true);}}
function concatenate(buffers){const n=buffers.reduce((s,b)=>s+b.length,0),out=new Float32Array(n);let off=0;for(const b of buffers){out.set(b,off);off+=b.length;}return out;}
function resample(input,fromRate,toRate){if(fromRate===toRate)return input;const ratio=fromRate/toRate,n=Math.max(1,Math.floor(input.length/ratio)),out=new Float32Array(n);for(let i=0;i<n;i++){const start=Math.floor(i*ratio),end=Math.min(Math.floor((i+1)*ratio),input.length);let sum=0,count=0;for(let j=start;j<end;j++){sum+=input[j];count++;}out[i]=count?sum/count:input[Math.min(start,input.length-1)]||0;}return out;}
function encodeWav(samples,sr){const ab=new ArrayBuffer(44+samples.length*2),v=new DataView(ab),ws=(off,s)=>[...s].forEach((c,i)=>v.setUint8(off+i,c.charCodeAt(0)));ws(0,'RIFF');v.setUint32(4,36+samples.length*2,true);ws(8,'WAVE');ws(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,sr,true);v.setUint32(28,sr*2,true);v.setUint16(32,2,true);v.setUint16(34,16,true);ws(36,'data');v.setUint32(40,samples.length*2,true);let off=44;for(let i=0;i<samples.length;i++,off+=2){const x=Math.max(-1,Math.min(1,samples[i]));v.setInt16(off,x<0?x*32768:x*32767,true);}return new Blob([v],{type:'audio/wav'});}
function cleanupRecording(){recording=false;clearInterval(recordingTimer);recordingTimer=null;try{processorNode?.disconnect();}catch(_){}try{audioSourceNode?.disconnect();}catch(_){}try{gainNode?.disconnect();}catch(_){}mediaStream?.getTracks().forEach(t=>t.stop());mediaStream=null;processorNode=null;audioSourceNode=null;gainNode=null;if(audioContext)audioContext.close().catch(()=>{});audioContext=null;$('#recordButton').classList.remove('recording');$('#recordIcon').textContent='●';$('#recordLabel').textContent='Start recording';$('#waveBars').classList.remove('active');}
async function transcribeRecordedAudio(wav,languageCode){
  $('#recordState').textContent='Transcribing your recording…';
  setVoiceFeedback('Working on your transcript. Please wait…');
  $('#recordButton').disabled=true;
  try{
    const f=new FormData();
    f.append('audio_file',new File([wav],'complaint.wav',{type:'audio/wav'}));
    f.append('language_code',languageCode);
    const out=await api('/api/voice/transcribe',{method:'POST',body:f});
    const transcript=String(out.transcript||'').trim();
    $('#description').value=transcript;
    syncSprintPreviewAvailability();markPreviewStale();
    lastDetectedSpeechLanguageCode=out.detected_language_code||inferLanguageCodeFromText(transcript);
    lastExtractionText='';
    extractionRequestSequence++;
    updateCharCount();
    // Re-run extraction against the final transcript via the same endpoint used by typed input.
    // This prevents UI autofill from depending on optional provider response fields.
    let extracted=out.extracted_facts||{};
    try{
      const preview=await api('/api/extraction/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({description:transcript})});
      if(preview?.extracted_facts)extracted=preview.extracted_facts;
    }catch(_){/* Keep the extraction already returned with the transcript. */}
    lastExtractionText=transcript;
    const autofill=applyExtractedFacts(extracted);
    renderExtractedFacts(extracted,autofill);
    $('#recordState').textContent='Your words are ready to review';
    if(out.redacted_types?.length){
      setVoiceFeedback('Your words are ready. We hid some sensitive-looking details; please check the wording before saving.');
    }else if(autofill.filled){
      setVoiceFeedback(`Your words are ready. We filled ${autofill.filled} detail${autofill.filled===1?'':'s'} for you to review.`);
    }else if(autofill.items.length){
      setVoiceFeedback('Your words are ready. Review the suggested details below and choose “Use” where needed.');
    }else{
      setVoiceFeedback('Your words are ready. Check the text and add any missing details below.');
    }
  }catch(err){
    $('#recordState').textContent='Let’s try that again';
    const message=String(err?.message||'');
    const shouldOfferLanguageChoice=languageCode==='auto'&&!/temporarily unavailable|busy right now|not configured|connect to the app/i.test(message);
    if(shouldOfferLanguageChoice){
      pendingTranscriptionBlob=wav;
      setVoiceFeedback('Choose the language you spoke, and we’ll try this same recording again.');
      openLanguagePicker();
    }else{
      const friendly=/not configured|aren.t configured|temporarily unavailable|busy right now|Request failed|could not connect/i.test(message)
        ?'Voice input is unavailable for the moment. You can try again or type your complaint.'
        :'We couldn’t get clear words from that recording. Try again, choose another language, or type your complaint.';
      setVoiceFeedback(friendly,true);
    }
  }finally{$('#recordButton').disabled=false;}
}
async function stopRecording(){
  if(!recording)return;
  recording=false;clearInterval(recordingTimer);
  const sr=recordingRate,samples=concatenate(recordingBuffers);cleanupRecording();
  if(!samples.length){setVoiceFeedback('No audio captured. Try again or type your complaint.',true);return;}
  const pcm=resample(samples,sr,16000),wav=encodeWav(pcm,16000),duration=Math.round(pcm.length/16000);
  $('#recordTimer').textContent=`${formatDuration(duration)} / 01:00`;
  if(duration<1){setVoiceFeedback('That recording was too short. Try again or type your complaint.',true);return;}
  await transcribeRecordedAudio(wav,$('#languageCode').value||'hi-IN');
  recordingBuffers=[];
}
function applyExtractedFacts(extraction){
  const fields=extraction?.fields||{};
  const config={
    issue_type:{id:'#issueType',label:'Issue type',default:['Other payment issue',''],format:v=>v},
    merchant:{id:'#merchant',label:'Merchant / app',default:[''],format:v=>v},
    amount:{id:'#amount',label:'Amount',default:[''],format:v=>String(v)},
    payment_date:{id:'#paymentDate',label:'Payment date',default:[''],format:v=>v},
    payment_status:{id:'#paymentStatus',label:'Payment status',default:['unknown',''],format:v=>v},
    contacted_support:{id:'#contactedSupport',label:'Support contacted',default:['','unknown'],format:v=>v===true?'yes':v===false?'no':''}
  };
  const outcome={filled:0,items:[],conflicts:[]};
  for(const [key,field] of Object.entries(fields)){
    const meta=config[key]; if(!meta||field.value===null||field.value===undefined||field.value==='')continue;
    const el=$(meta.id); if(!el)continue;
    const current=el.value;
    const candidate=meta.format(field.value);
    // Only replace untouched/default values: speech should not silently erase an answer
    // the user already typed or selected.
    const canFill=meta.default.includes(current);
    if(canFill && candidate!=='' && [...el.options||[]].every(option=>option.value!==candidate) && el.tagName==='SELECT'){
      outcome.items.push({key,label:meta.label,value:candidate,field,applied:false,current});
      continue;
    }
    if(canFill && candidate!==''){
      el.value=candidate;
      if(key==='issue_type')syncIssueChoiceFromSelect();
      outcome.filled++;
      outcome.items.push({key,label:meta.label,value:field.value,field,applied:true,current});
    }else if(String(current)!==String(candidate) && candidate!==''){
      outcome.items.push({key,label:meta.label,value:field.value,field,applied:false,current});
      outcome.conflicts.push({key,current,value:field.value,label:meta.label});
    }
  }
  return outcome;
}
function renderExtractedFacts(extraction,outcome={filled:0,items:[],conflicts:[]}){
  const panel=$('#extractedFactsPanel'); if(!panel)return;
  const fields=extraction?.fields||{};
  const labels={issue_type:'Issue type',merchant:'Merchant / app',amount:'Amount',payment_date:'Payment date',payment_status:'Payment status',contacted_support:'Support contacted'};
  const showValue=(key,value)=>key==='amount'?money(value):key==='contacted_support'?(value===true?'Yes':value===false?'Not yet':String(value)):key==='payment_status'?({unknown:'Not sure',failed:'Failed',pending:'Pending',successful:'Successful',refund_pending:'Refund pending',unauthorized:'Unrecognised payment'}[value]||String(value)):String(value);
  const items=Object.entries(fields).filter(([key,f])=>f.value!==null&&f.value!==undefined&&f.value!==''&&f.value!=='unknown'&&labels[key]);
  const conflictKeys=new Set((extraction?.conflicts||[]).map(c=>c.field));
  $('#extractedFactsCount').textContent=outcome.filled?`${outcome.filled} filled · ${Math.max(0,items.length-outcome.filled)} to review`:items.length?`${items.length} suggestions to review`:'No details picked up yet';
  const cards=items.map(([key,field])=>{
    const isConflict=conflictKeys.has(key)||outcome.conflicts.some(c=>c.key===key);
    const current=outcome.conflicts.find(c=>c.key===key)?.current;
    const state=field.needs_confirmation?'Check date':isConflict?'Confirm values':(field.confidence==='high'?'Found in speech':'Suggested');
    const currentNote=current!==undefined?`<small class="extracted-fact-current">Your existing answer: ${escapeHtml(showValue(key,current))}</small>`:'';
    return `<article class="extracted-fact-chip ${field.needs_confirmation||isConflict?'needs-review':''}"><div><span>${escapeHtml(labels[key])}</span><b>${escapeHtml(showValue(key,field.value))}</b>${currentNote}<small>${escapeHtml(state)}${field.evidence?` · “${escapeHtml(field.evidence)}”`:''}</small></div>${!outcome.items.find(item=>item.key===key)?.applied&&outcome.items.find(item=>item.key===key)?`<button type="button" data-apply-extracted="${escapeHtml(key)}" aria-label="Apply suggested ${escapeHtml(labels[key])}">Use</button>`:''}</article>`;
  }).join('');
  const conflicts=(extraction?.conflicts||[]).map(c=>`<p><strong>Check ${escapeHtml(labels[c.field]||c.field)}:</strong> ${escapeHtml(c.message||'More than one possible value was mentioned.')}</p>`).join('');
  const questions=(extraction?.clarifying_questions||[]).map(q=>`<p>${escapeHtml(q)}</p>`).join('');
  $('#extractedFactsList').innerHTML=cards||'<p class="extracted-facts-empty">No details could be safely extracted yet. You can still fill the fields yourself.</p>';
  const qbox=$('#extractedFactsQuestions');qbox.innerHTML=conflicts+questions;qbox.hidden=!(conflicts||questions);
  panel.hidden=false;
  panel.dataset.extraction=JSON.stringify(extraction||{});
  panel.dataset.hasUsefulFacts=items.length?'1':'0';
}
$('#extractedFactsList')?.addEventListener('click',e=>{
  const button=e.target.closest('[data-apply-extracted]');if(!button)return;
  try{
    const extraction=JSON.parse($('#extractedFactsPanel').dataset.extraction||'{}');
    const key=button.dataset.applyExtracted,field=extraction.fields?.[key];
    const selector={issue_type:'#issueType',merchant:'#merchant',amount:'#amount',payment_date:'#paymentDate',payment_status:'#paymentStatus',contacted_support:'#contactedSupport'}[key];
    const el=selector&&$(selector);if(!el||!field)return;
    const value=key==='contacted_support'?(field.value===true?'yes':field.value===false?'no':''):String(field.value??'');
    if(key==='amount'&&field.value!==null)el.value=String(field.value);
    else if(value!==''&&[...el.options||[]].some(option=>option.value===value))el.value=value;
    else if(value!==''&&el.tagName!=='SELECT')el.value=value;
    else if(value!==''&&el.tagName==='SELECT'){showToast('This suggestion is not an available option. Please choose manually.','error');return;}
    button.textContent='Added';button.disabled=true;button.closest('.extracted-fact-chip')?.classList.remove('needs-review');
    showToast(`${button.getAttribute('aria-label')?.replace('Apply suggested ','')||'Suggestion'} added. Please review it.`);
  }catch(_){showToast('Could not apply that suggestion. Please enter it manually.','error');}
});
$('#recordButton')?.addEventListener('click',()=>recording?stopRecording():startRecording());
let extractionTimer=null,extractionRequestSequence=0,lastExtractionText='';
$('#description')?.addEventListener('input',()=>{updateCharCount();syncSprintPreviewAvailability();scheduleTextExtraction();markPreviewStale();});
function syncSprintPreviewAvailability(){const button=$('#previewResolutionButton');if(button&&!button.dataset.loading)button.disabled=($('#description')?.value?.trim()||'').length<8;}
function markPreviewStale(){resolutionPreviewSequence++;const button=$('#previewResolutionButton');if(button?.dataset.loading){delete button.dataset.loading;button.disabled=($('#description')?.value?.trim()||'').length<8;button.innerHTML='<span>Get my next step</span><span aria-hidden="true">↗</span>';}const panel=$('#resolutionPreview');if(panel&&!panel.hidden){panel.hidden=true;panel.innerHTML='';}}
['issueType','merchant','amount','paymentDate','paymentStatus','contactedSupport'].forEach(id=>{const el=$('#'+id);el?.addEventListener('change',markPreviewStale);el?.addEventListener('input',markPreviewStale);});
syncSprintPreviewAvailability();
function updateCharCount(){$('#charCount').textContent=`${$('#description').value.length} / 5000`;}
function scheduleTextExtraction(){
  clearTimeout(extractionTimer);
  const text=$('#description')?.value?.trim()||'';
  if(text.length<8){extractionRequestSequence++;return;}
  extractionTimer=setTimeout(()=>runTextExtraction(text),550);
}
async function runTextExtraction(text){
  const sequence=++extractionRequestSequence;
  if(text===lastExtractionText && $('#extractedFactsPanel')?.dataset.hasUsefulFacts==='1')return;
  try{
    const response=await api('/api/extraction/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({description:text})});
    if(sequence!==extractionRequestSequence||($('#description')?.value?.trim()||'')!==text)return;
    lastExtractionText=text;
    const extraction=response.extracted_facts||{};
    const outcome=applyExtractedFacts(extraction);
    renderExtractedFacts(extraction,outcome);
    if(outcome.filled>0)setVoiceFeedback(`We picked up ${outcome.filled} detail${outcome.filled===1?'':'s'} from your story. Check them before saving.`);
  }catch(_){
    // Typing must never be blocked if the extraction service is unavailable.
  }
}
const evidenceInput=$('#evidenceFile');
evidenceInput?.addEventListener('change',()=>{const incoming=[...evidenceInput.files],extensions=new Set(['.png','.jpg','.jpeg','.webp','.pdf']);for(const file of incoming){const dot=file.name.lastIndexOf('.'),ext=dot>=0?file.name.slice(dot).toLowerCase():'';if(!extensions.has(ext)){showToast(`${file.name}: use PNG, JPG, WEBP or PDF.`,'error');continue;}if(file.size>8*1024*1024){showToast(`${file.name}: files must be 8 MB or smaller.`,'error');continue;}if(!selectedEvidenceFiles.some(f=>f.name===file.name&&f.size===file.size))selectedEvidenceFiles.push(file);}evidenceInput.value='';renderSelectedFiles();});
function renderSelectedFiles(){const list=$('#selectedFiles');$('#fileCount').textContent=`${selectedEvidenceFiles.length} file${selectedEvidenceFiles.length===1?'':'s'}`;list.innerHTML=selectedEvidenceFiles.map((f,i)=>`<div class="selected-file"><span>▧</span><span>${escapeHtml(f.name)} <small>(${(f.size/1024).toFixed(0)} KB)</small></span><button type="button" data-remove-file="${i}" aria-label="Remove ${escapeHtml(f.name)}">×</button></div>`).join('');}
$('#selectedFiles')?.addEventListener('click',e=>{const b=e.target.closest('[data-remove-file]');if(!b)return;selectedEvidenceFiles.splice(Number(b.dataset.removeFile),1);renderSelectedFiles();});
$('#createCaseButton')?.addEventListener('click',createCase);
async function createCase(){
  const payload=getResolutionPayload(),errorBox=$('#formError');errorBox.hidden=true;
  if(payload.description.length<8){errorBox.textContent='Please describe what happened in at least 8 characters. Type it or use voice input.';errorBox.hidden=false;$('#description').focus();return;}
  if(!$('#safeDataCheck').checked){errorBox.textContent='Please confirm that you have not included passwords, OTPs or payment PINs, and that you have permission to share the files.';errorBox.hidden=false;return;}
  if($('#amount').value.trim()&&payload.amount===null){errorBox.textContent='Enter a valid amount, or leave the field empty.';errorBox.hidden=false;return;}
  if(authRequired&&!signedInUser){pendingAuthAction='create-case';showAuthGate('Sign in or create a private account to save this Resolution Passport. Your story and first-pass suggestion will stay on this screen.');return;}
  const button=$('#createCaseButton');button.disabled=true;button.innerHTML='<span class="button-spinner"></span> Saving your case…';
  try{
    const item=await api('/api/cases',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});currentCaseId=item.case_id;const uploadErrors=[];
    for(const file of selectedEvidenceFiles){const form=new FormData();form.append('file',file);try{await api(`/api/cases/${encodeURIComponent(currentCaseId)}/evidence`,{method:'POST',body:form});}catch(err){uploadErrors.push(`${file.name}: ${err.message}`);}}
    if(pendingSharedIntakeToken){try{await attachSharedIntakeToCase(currentCaseId,false);}catch(err){pendingSharedIntakeAttachCaseId=currentCaseId;uploadErrors.push(`Shared item still needs adding: ${err.message}`);}}
    activeCaseTab='overview';selectedEvidenceFiles=[];renderSelectedFiles();$('#description').value='';$('#issueType').value='Other payment issue';syncIssueChoiceFromSelect();$('#merchant').value='';$('#amount').value='';$('#paymentDate').value='';$('#paymentStatus').value='unknown';$('#contactedSupport').value='';$('#safeDataCheck').checked=false;$('#resolutionPreview').hidden=true;$('#intakeEvidencePanel').hidden=true;$('#intakeEvidenceToggle').setAttribute('aria-expanded','false');$('#formError').hidden=true;updateCharCount();syncSprintPreviewAvailability();markPreviewStale();setIntakeStep(1,{scroll:false});showView('detail');
    if(uploadErrors.length)showToast(`Case saved. Some evidence could not be uploaded: ${uploadErrors.join(' ')}`,'error');else if(item.redaction_types?.length)showToast(`Case ${currentCaseId} saved. Sensitive-looking ${item.redaction_types.join(', ')} values were redacted; review the saved story.`,'error');else showToast(`Case ${currentCaseId} created with guided next steps.`);
  }catch(err){errorBox.textContent=err.message;errorBox.hidden=false;}finally{button.disabled=false;button.innerHTML='Save my case <span>↗</span>'; }
}

let casesFilter='all',casesSearch='';
function renderCasesList(){
  const list=$('#casesList');if(!list)return;
  const query=casesSearch.trim().toLocaleLowerCase();
  const filtered=cachedCases.filter(item=>{
    const stage=String(item.case_stage||'Needs next step');
    const resolved=stage==='Resolved (user-reported)';
    const waiting=stage==='Awaiting response';
    if(casesFilter==='active'&&(resolved||waiting))return false;
    if(casesFilter==='waiting'&&!waiting)return false;
    if(casesFilter==='resolved'&&!resolved)return false;
    const searchable=[item.case_id,item.issue_type,item.merchant,item.case_stage,item.next_action].join(' ').toLocaleLowerCase();
    return !query||searchable.includes(query);
  });
  if(!filtered.length){list.innerHTML=`<div class="empty-state"><div class="empty-symbol">⌕</div><h3>${cachedCases.length?'No matching cases.':'Your story starts here.'}</h3><p>${cachedCases.length?'Try another search or choose a different case filter.':'Create your first case. We’ll keep the details, files and next steps together.'}</p>${cachedCases.length?'':'<button class="button button-mint" data-view="new">Create a case <span>↗</span></button>'}</div>`;list.querySelector('[data-view="new"]')?.addEventListener('click',()=>showView('new'));return;}
  list.innerHTML=filtered.map(c=>`<article class="case-list-item" role="button" tabindex="0" data-open-case="${escapeHtml(c.case_id)}" aria-label="Open case ${escapeHtml(c.case_id)}"><div class="case-monogram">${escapeHtml((c.issue_type||'P').slice(0,1).toUpperCase())}</div><div class="case-list-main"><span class="case-id">${escapeHtml(c.case_id)}</span><h3>${escapeHtml(c.issue_type)}</h3><p>${escapeHtml(c.merchant||'Merchant not provided')} · Updated ${escapeHtml(prettyDate(c.updated_at))} · ${Number(c.evidence_count||0)} evidence file(s)</p><small class="case-next-action"><b>Next:</b> ${escapeHtml(c.next_action||'Review case details')}</small></div><div class="case-list-amount">${escapeHtml(money(c.amount))}</div><div class="case-list-side"><span class="status-pill">${escapeHtml(c.case_stage||'Needs next step')}</span><span class="case-list-date">${c.follow_up_due?`Follow-up · ${escapeHtml(c.follow_up_due)}`:escapeHtml(prettyDate(c.created_at))}</span></div></article>`).join('');
}
async function refreshCases(){const list=$('#casesList');if(!list)return;list.innerHTML='<div class="empty-state"><div class="empty-symbol">◌</div><h3>Opening your cases…</h3><p>Gathering your case details.</p></div>';try{cachedCases=await api('/api/cases');$('#navCaseCount').textContent=cachedCases.length;$('#totalCaseCount').textContent=cachedCases.length;$('#openCaseCount').textContent=cachedCases.filter(c=>(c.case_stage||'Needs next step')!=='Resolved (user-reported)').length;$('#evidenceCaseCount').textContent=cachedCases.reduce((n,c)=>n+Number(c.evidence_count||0),0);renderCasesList();}catch(err){list.innerHTML=`<div class="empty-state"><div class="empty-symbol">!</div><h3>We couldn’t load your cases.</h3><p>Please try again in a moment.</p></div>`;}}
$('#casesSearch')?.addEventListener('input',event=>{casesSearch=event.currentTarget.value||'';renderCasesList();});
$$('[data-case-filter]').forEach(button=>button.addEventListener('click',()=>{casesFilter=button.dataset.caseFilter||'all';$$('[data-case-filter]').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));renderCasesList();}));
$('#casesList')?.addEventListener('click',e=>{const row=e.target.closest('[data-open-case]');if(row){activeCaseTab='overview';currentCaseId=row.dataset.openCase;showView('detail');}});
$('#casesList')?.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.matches('[data-open-case]')){e.preventDefault();activeCaseTab='overview';currentCaseId=e.target.dataset.openCase;showView('detail');}});
async function loadCase(id){const panel=$('#caseDetailContent');panel.innerHTML='<div class="empty-state"><div class="empty-symbol">◌</div><h3>Loading case…</h3></div>';try{renderCaseDetail(await api(`/api/cases/${encodeURIComponent(id)}`));}catch(err){panel.innerHTML=`<div class="empty-state"><h3>We couldn’t open this case.</h3><p>Please return to your cases and try again.</p><button class="button button-mint" data-view="cases">Back to cases</button></div>`;panel.querySelector('[data-view="cases"]')?.addEventListener('click',()=>showView('cases'));}}
function timelineLabel(type){return({live_room_session_started:'Live resolution session started',live_room_session_ended:'Live resolution session ended',live_room_user_turn:'Live conversation detail',live_room_agent_guidance:'Live resolution guidance',created:'Case created',notice:'Guidance prepared',outcome_updated:'Outcome recorded',evidence:'Evidence added',draft:'Support request prepared',user_note:'Personal note',privacy:'Privacy protection',progress:'Case progress updated',details_updated:'Case details updated',guidance_refreshed:'Guidance refreshed',draft_edited:'Support draft edited',followup:'Follow-up reminder updated',followup_updated:'Follow-up updated',contacted_support:'Contacted support',still_waiting:'Still waiting',submission_reported:'Submission reported',response_received:'Response received',resolved:'Marked resolved',not_resolved:'Issue still open',official_channel_opened:'Official channel opened',whatsapp_linked:'WhatsApp connected',whatsapp_update:'WhatsApp update',followup_scheduled:'Follow-up scheduled',reminder_sent:'Reminder accepted for delivery',whatsapp_sent:'WhatsApp message sent',whatsapp_delivered:'WhatsApp message delivered',whatsapp_read:'WhatsApp message read',whatsapp_delivery_failed:'WhatsApp delivery failed',evidence_facts_reviewed:'Evidence details reviewed',inbound_email_received:'Forwarded reply received',case_inbox_created:'Case inbox created',case_inbox_rotated:'Case inbox rotated',inbound_email_discarded:'Forwarded reply discarded',shared_item_added:'Shared item added to case'})[type]||'Timeline update';}
function savedCaseFastPathQuestionMarkup(resolution){
  const question=resolution?.next_question;
  if(question?.prompt&&Array.isArray(question.options)&&question.options.length){
    const options=question.options.filter(option=>option.value!=='unknown').map(option=>`<button type="button" class="fastest-path-option" data-action="answer-case-fastpath" data-field="${escapeHtml(question.field||'')}" data-value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</button>`).join('');
    return `<div class="case-guided-question fastest-path-question case-fastpath-saved" aria-live="polite"><div class="fastest-path-question-heading"><span>ONE DETAIL THAT CAN CHANGE THE NEXT STEP</span><p>${escapeHtml(question.prompt)}</p></div>${question.why_it_matters?`<small class="fastest-path-why">${escapeHtml(question.why_it_matters)}</small>`:''}${options?`<div class="fastest-path-options" role="group" aria-label="Answer this case clarification">${options}</div>`:''}<small class="case-fastpath-boundary">This updates your guidance from your answer. It does not check bank or merchant records.</small></div>`;
  }
  if(resolution?.clarifying_question){
    return `<div class="case-guided-question"><b>One detail could make this advice more specific</b><p>${escapeHtml(resolution.clarifying_question)}</p><button type="button" class="case-subtle-button" data-action="open-edit-details">Review case details ↗</button></div>`;
  }
  return '';
}
function commitmentRelationLabel(relation){return ({supports:'Supports the statement',contradicts:'Conflicts with the statement',qualifies:'Qualifies or narrows it',triggers:'Condition occurred',fulfils:'Fulfilment reported',supersedes:'Says the statement was replaced',unrelated:'Not relevant to this commitment',unknown:'Relationship not clear'})[relation]||relation||'Update';}
function commitmentEvidenceOptions(files, selected=''){
  return `<option value="">No file linked</option>${(files||[]).map(f=>`<option value="${escapeHtml(f.evidence_id)}" ${selected===f.evidence_id?'selected':''}>${escapeHtml(f.original_name)}</option>`).join('')}`;
}
function renderCommitmentCard(item, files=[]){
  const evaluation=item.evaluation||{}, events=item.events||[];
  const duration=item.duration_value==null?'Timeframe not captured':`${item.duration_value}${item.duration_max_value!=null&&item.duration_max_value!==item.duration_value?`–${item.duration_max_value}`:''} ${item.day_type==='business_day'?'business ':item.day_type==='calendar_day'?'calendar ':''}${item.duration_unit}${item.duration_value===1?'':'s'}`;
  const amount=item.amount_minor_units==null?'':` · ₹${(Number(item.amount_minor_units)/100).toLocaleString('en-IN',{maximumFractionDigits:2})}`;
  const due=evaluation.estimated_due_date?`${evaluation.estimated_due_date.earliest}${evaluation.estimated_due_date.latest!==evaluation.estimated_due_date.earliest?` – ${evaluation.estimated_due_date.latest}`:''}`:'';
  const history=events.length?events.map(e=>`<article class="commitment-history-row"><div><b>${escapeHtml(commitmentRelationLabel(e.relation))}</b><small>${escapeHtml(prettyDate(e.created_at))} · ${escapeHtml(e.evidence_status||'user-reported')}</small></div>${e.source_excerpt_redacted?`<p>${escapeHtml(e.source_excerpt_redacted)}</p>`:''}${e.event_date_confirmed?`<small>Occurrence date recorded as ${escapeHtml(e.event_date_confirmed)} (user-confirmed, not independently checked).</small>`:''}${e.evidence_id?`<small>Linked to a case file; authenticity has not been independently verified.</small>`:''}</article>`).join(''):'<p class="muted-note">No later updates have been linked yet.</p>';
  return `<article class="commitment-card" data-commitment-card="${escapeHtml(item.commitment_id)}">
    <div class="commitment-card-top"><div><span class="case-mini-kicker">${escapeHtml(item.commitment_id)} · ${escapeHtml(item.speech_act.replaceAll('_',' '))}</span><h3>${escapeHtml(item.action_text)}${escapeHtml(amount)}</h3></div><span class="commitment-state-chip" data-state="${escapeHtml(evaluation.status||'unknown')}">${escapeHtml(evaluation.status_label||'Needs review')}</span></div>
    <div class="commitment-facts-grid"><div><small>CONDITION / TRIGGER</small><b>${escapeHtml(item.condition_text||'No condition detected')}</b><p>${escapeHtml(item.condition_text?(evaluation.trigger_date?`Recorded trigger date: ${evaluation.trigger_date}`:'Clock does not start until the trigger and date are established.'):(item.trigger_type==='statement_date'?'Starts from the recorded statement date.':'Start rule not established.'))}</p></div><div><small>STATED TIMEFRAME</small><b>${escapeHtml(duration)}</b><p>${escapeHtml(evaluation.due_date_note||'No deadline calculated.')}${due?`<br><strong>Estimated date: ${escapeHtml(due)}</strong>`:''}</p></div></div>
    <details class="commitment-source-disclosure"><summary>Review the saved source statement</summary><blockquote>${escapeHtml(item.source_excerpt_redacted||'No excerpt stored')}</blockquote><small>${escapeHtml(item.source_label||item.source_type)} · source authenticity not independently verified</small></details>
    <p class="commitment-next-action"><b>Current interpretation:</b> ${escapeHtml(evaluation.next_action||'Review this commitment and its sources.')}</p>
    <details class="commitment-history-disclosure"><summary>Change history (${events.length})</summary><div class="commitment-history-list">${history}</div></details>
    <details class="commitment-update-disclosure"><summary>Add a later reply or proof</summary><div class="commitment-update-form" data-commitment-update-form="${escapeHtml(item.commitment_id)}">
      <label class="case-field-v2"><span>What does the new source say?</span><textarea data-commitment-event-text rows="3" maxlength="1500" placeholder="Paste only the relevant sentence or enter a short, redacted note." required></textarea></label>
      <label class="case-field-v2"><span>How does it relate to the original statement?</span><select data-commitment-relation><option value="unknown">I'm not sure yet</option><option value="supports">Supports it</option><option value="triggers">The condition happened</option><option value="contradicts">Conflicts with it</option><option value="qualifies">Changes or narrows it</option><option value="fulfils">Says the commitment was fulfilled</option><option value="supersedes">Says it was replaced</option><option value="unrelated">Unrelated</option></select></label>
      <div class="commitment-date-grid"><label class="case-field-v2"><span>Date stated by the source (optional)</span><input type="date" data-commitment-date-claimed></label><label class="case-field-v2"><span>Occurrence date you can confirm (optional)</span><input type="date" data-commitment-date-confirmed></label></div>
      <label class="case-field-v2"><span>Link an existing case file (optional)</span><select data-commitment-evidence>${commitmentEvidenceOptions(files)}</select></label>
      <p class="case-privacy-caption">Choose “condition happened” only when you have reviewed a relevant source. A linked file is not automatically authentic or independently verified.</p>
      <button type="button" class="button button-dark" data-action="reconcile-commitment" data-commitment-id="${escapeHtml(item.commitment_id)}">Record reviewed update</button>
      <button type="button" class="button button-quiet" data-action="delete-commitment" data-commitment-id="${escapeHtml(item.commitment_id)}">Remove this commitment</button>
    </div></details>
  </article>`;
}
function renderCommitmentsPanel(commitments=[], files=[]){
  const cards=(commitments||[]).map(item=>renderCommitmentCard(item,files)).join('');
  return `<details id="caseCommitmentsDisclosure" class="case-secondary-disclosure case-commitments-disclosure">
    <summary><span class="case-secondary-icon" aria-hidden="true">◎</span><span><b>Commitments &amp; conditions</b><small>${commitments.length?`${commitments.length} saved statement${commitments.length===1?'':'s'} · track what has to happen first`:'Record a support promise and its conditions'}</small></span><span class="case-disclosure-chevron" aria-hidden="true">＋</span></summary>
    <div class="case-secondary-disclosure-content"><section class="case-workspace-card case-tab-content-card case-commitments-workspace"><div class="case-card-heading-v2"><div><span class="case-mini-kicker">CONDITION-AWARE COMMITMENT RECONCILIATION</span><h2>What was promised—and what starts the clock?</h2><p>Import a short support-call recording or paste the exact wording from an email/chat. Review the extracted fields, confirm them, and link later evidence without erasing earlier statements.</p></div><span class="case-user-reported-tag">Review required</span></div>
      <div class="commitment-notice"><b>Important:</b> this does not prove who spoke or what a company actually did. Recordings are sent to the configured Gnani speech service only when you choose to transcribe them; BolKeResolve does not save the recording. A short redacted statement excerpt is saved only after you confirm it.</div>
      <div class="commitment-intake-form">
        <label class="case-field-v2"><span>Where did the statement come from?</span><select id="commitmentSourceType"><option value="support_call_transcript">Support-call recording / transcript</option><option value="support_email">Support email</option><option value="chat_message">Chat message</option><option value="user_note">My written note</option><option value="case_evidence">Statement linked to case evidence</option></select></label>
        <label class="case-field-v2"><span>Import a short audio clip (optional)</span><input id="commitmentAudioFile" type="file" accept=".wav,.mp3,.ogg,.flac,.aac,.m4a,audio/*"><small>Up to 12 MB. Use only a recording you have the right to use. The recording is sent for transcription and is not retained by this app.</small></label>
        <button type="button" class="button button-outline" data-action="transcribe-commitment-audio">Transcribe selected recording</button>
        <label class="case-field-v2"><span>Exact statement or transcript</span><textarea id="commitmentSourceText" rows="4" maxlength="4000" placeholder="Example: Once the return is scanned at the warehouse, we will initiate the ₹1,200 refund within five business days."></textarea></label>
        <div class="commitment-intake-actions"><button type="button" class="button button-dark" data-action="preview-commitment">Find a possible commitment</button><small>Preview does not save anything. Check the words and dates yourself.</small></div>
        <div id="commitmentPreviewResult" class="commitment-preview-result" hidden aria-live="polite"></div>
      </div>
      <div class="commitment-saved-section"><div class="case-card-heading-v2"><div><span class="case-mini-kicker">CASE-SPECIFIC RECORD</span><h3>Saved commitments</h3><p>Later evidence can support, qualify or contradict a statement. Nothing overwrites history silently.</p></div><span class="case-count-badge">${commitments.length}</span></div>
      <div id="commitmentList" class="commitment-list">${cards||'<div class="case-empty-inline"><span>◎</span><b>No commitments saved</b><p>Start with one exact sentence from a support call, email or chat. We will not create a promise if the wording is unclear.</p></div>'}</div></div>
    </section></div>
  </details>`;
}

function switchCaseTab(requestedTab){
  const aliases={evidence:'prep',draft:'prep',outcome:'progress',activity:'progress',tracking:'progress'};
  const tab=aliases[requestedTab]||requestedTab;
  const allowed=new Set(['overview','prep','progress']);
  if(!allowed.has(tab))return;
  const previousTab=activeCaseTab;
  activeCaseTab=tab;
  const toolsMenu=$('#caseToolsMenu');
  /* Keep the selector visible whenever a secondary workspace is open; a hidden selector must never leave users stranded in an unlabeled subview. */
  if(toolsMenu)toolsMenu.open=tab!=='overview';
  const primaryAction=$('#casePrimaryAction');
  if(primaryAction)primaryAction.hidden=tab!=='overview';
  const root=$('#caseDetailContent');
  $$('.case-workspace-tabs [data-case-tab]',root).forEach(button=>{
    const selected=button.dataset.caseTab===tab;
    button.classList.toggle('active',selected);
    button.setAttribute('aria-selected',String(selected));
    button.setAttribute('tabindex',selected?'0':'-1');
  });
  $$('[data-tab-panel]',root).forEach(panel=>{panel.hidden=panel.dataset.tabPanel!==tab;});
  const targetId=({evidence:'caseEvidenceDisclosure',draft:'caseMessageDisclosure',outcome:'caseOutcomeSection',activity:'caseActivityDisclosure',tracking:'caseFollowThroughSection'})[requestedTab];
  if(targetId){
    const target=document.getElementById(targetId);
    if(target?.tagName==='DETAILS')target.open=true;
    if(target){
      const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      requestAnimationFrame(()=>target.scrollIntoView({behavior:reduced?'auto':'smooth',block:'start'}));
    }
  }else if(previousTab!==tab&&tab==='overview'){
    const target=$('#casePrimaryAction');
    requestAnimationFrame(()=>target?.scrollIntoView({behavior:'auto',block:'start'}));
  }else if(previousTab!==tab&&(tab==='prep'||tab==='progress')){
    const target=$(`#casePanel${tab==='prep'?'Prep':'Progress'}`);
    requestAnimationFrame(()=>target?.scrollIntoView({behavior:'auto',block:'start'}));
  }
}
function renderCaseDetail(c){
  currentCaseId=c.case_id;
  activeCaseSnapshot=c;
  reviewedReplyDraft=null;
  const events=[...(c.timeline||[])].sort((a,b)=>{const at=Date.parse(a.created_at||'')||0,bt=Date.parse(b.created_at||'')||0;return bt-at;}),files=c.evidence||[],resolution=c.resolution||{};
  const steps=resolution.recommended_steps||[],sources=resolution.official_sources||[],supportDestinations=Array.isArray(resolution.support_destinations)?resolution.support_destinations:[];
  const classification=resolution.classification||{};
  const activeIndex=Math.max(0,['Needs next step','Contacted support','Awaiting response','Follow-up needed','Resolved (user-reported)'].indexOf(c.case_stage||'Needs next step'));
  const activityKind=e=>['evidence','draft','draft_edited','privacy'].includes(e.event_type)?'documents':['user_note'].includes(e.event_type)?'notes':['progress','outcome_updated','contacted_support','still_waiting','submission_reported','response_received','resolved','not_resolved','followup','followup_updated','followup_scheduled','reminder_sent','whatsapp_sent','whatsapp_delivered','whatsapp_read','whatsapp_delivery_failed','guidance_refreshed','details_updated','inbound_email_received','case_inbox_created','case_inbox_rotated','inbound_email_discarded','evidence_facts_reviewed'].includes(e.event_type)?'progress':'case';
  const activityIcon=e=>{const icons={created:'<svg viewBox="0 0 24 24"><path d="M12 7v5l3 2"/><circle cx="12" cy="12" r="9"/></svg>',notice:'<svg viewBox="0 0 24 24"><path d="M5 12.5 9.5 17 19 7"/></svg>',evidence:'<svg viewBox="0 0 24 24"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/></svg>',draft:'<svg viewBox="0 0 24 24"><path d="M4 20h4l11-11a2.1 2.1 0 0 0-4-4L4 16z"/><path d="M13.5 6.5 17.5 10.5"/></svg>',draft_edited:'<svg viewBox="0 0 24 24"><path d="M4 20h4l11-11a2.1 2.1 0 0 0-4-4L4 16z"/></svg>',user_note:'<svg viewBox="0 0 24 24"><path d="M5 5h14v11H9l-4 3z"/><path d="M8 9h8M8 12h5"/></svg>',progress:'<svg viewBox="0 0 24 24"><path d="M4 17 10 11l4 3 6-8"/><path d="M14 6h6v6"/></svg>',response_received:'<svg viewBox="0 0 24 24"><path d="M20 11.5a7.5 7.5 0 0 1-8 7.5 8.5 8.5 0 0 1-4-.9L4 20l1.3-3.6A7 7 0 0 1 4 11.5 7.8 7.8 0 0 1 12 4a7.8 7.8 0 0 1 8 7.5Z"/></svg>',resolved:'<svg viewBox="0 0 24 24"><path d="m5 12 4 4L19 6"/></svg>',whatsapp_sent:'<svg viewBox="0 0 24 24"><path d="M4 12a8 8 0 0 1 14-5M20 12a8 8 0 0 1-14 5"/><path d="M16 4h3v3M8 20H5v-3"/></svg>',whatsapp_delivered:'<svg viewBox="0 0 24 24"><path d="m3 12 4 4L17 6M10 12l4 4 7-8"/></svg>',whatsapp_read:'<svg viewBox="0 0 24 24"><path d="m2 12 4 4L16 6M9 12l4 4 9-10"/></svg>',whatsapp_delivery_failed:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16h.01"/></svg>'};return icons[e.event_type]||icons[activityKind(e)==='progress'?'progress':activityKind(e)==='documents'?'evidence':'created'];};
  const eventsHtml=events.length?events.map(e=>`<article class="case-activity-item" data-activity-item data-activity-kind="${activityKind(e)}"><span class="case-activity-icon" aria-hidden="true">${activityIcon(e)}</span><div class="case-activity-copy"><div class="case-activity-line"><b>${escapeHtml(timelineLabel(e.event_type))}</b><time datetime="${escapeHtml(e.created_at||'')}">${escapeHtml(prettyDate(e.created_at))}</time></div><p>${escapeHtml(e.event_type==='notice'?'Your details have been organised for your next step.':e.message)}</p>${e.channel&&e.channel!=='web'?`<small class="case-activity-source">Recorded via ${escapeHtml(e.channel)}</small>`:''}</div></article>`).join(''):'<div class="case-activity-empty"><span><svg viewBox="0 0 24 24"><path d="M12 7v5l3 2"/><circle cx="12" cy="12" r="9"/></svg></span><b>Your case history starts here</b><p>Updates, saved messages and notes will appear here as you take the next steps.</p></div>';
  const evidenceHtml=files.length?files.map((f,index)=>{
    const mime=String(f.mime_type||'').toLowerCase();
    const rawUrl=`/api/cases/${encodeURIComponent(c.case_id)}/evidence/${encodeURIComponent(f.evidence_id)}`;
    const inlineUrl=`${rawUrl}?inline=true`;
    const type=mime==='application/pdf'?'PDF':mime.startsWith('video/')?'VIDEO':mime.startsWith('audio/')?'AUDIO':mime.startsWith('image/')?'IMAGE':'FILE';
    let preview='';
    if(mime.startsWith('image/'))preview=`<a class="case-evidence-preview case-evidence-image-preview" href="${escapeHtml(inlineUrl)}" target="_blank" rel="noopener noreferrer"><img src="${escapeHtml(inlineUrl)}" loading="lazy" alt="Preview of ${escapeHtml(f.original_name)}"></a>`;
    else if(mime.startsWith('video/'))preview=`<video class="case-evidence-preview case-evidence-video-preview" controls preload="metadata" playsinline src="${escapeHtml(inlineUrl)}">Your browser cannot preview this recording. <a href="${escapeHtml(rawUrl)}">Download it</a>.</video>`;
    else if(mime.startsWith('audio/'))preview=`<audio class="case-evidence-preview case-evidence-audio-preview" controls preload="metadata" src="${escapeHtml(inlineUrl)}">Your browser cannot play this recording.</audio>`;
    else if(mime==='application/pdf')preview=`<a class="case-evidence-pdf-preview" href="${escapeHtml(inlineUrl)}" target="_blank" rel="noopener noreferrer">Preview PDF ↗</a>`;
    const provenance=String(f.capture_source||'user_upload').replaceAll('_',' ');
    return `<article class="case-evidence-row case-evidence-row-rich"><span class="case-file-icon">${type}</span><div class="case-evidence-name"><b>${escapeHtml(f.original_name)}</b><small>${(Number(f.size_bytes)/1024).toFixed(0)} KB · Added ${escapeHtml(prettyDate(f.created_at))} · ${escapeHtml(provenance)} · User-uploaded, not independently verified</small>${preview}<div class="case-evidence-actions"><a class="button button-outline" href="${escapeHtml(inlineUrl)}" target="_blank" rel="noopener noreferrer">Preview ↗</a><a class="button button-quiet" href="${escapeHtml(rawUrl)}" download>Download original ↓</a><button type="button" class="button button-quiet" data-action="review-evidence" data-evidence-id="${escapeHtml(f.evidence_id)}">Check details</button></div></div></article>`;
  }).join(''):'<div class="case-empty-inline"><span>＋</span><b>No evidence added yet</b><p>Receipts, order confirmations and support screenshots can make your request easier to review.</p></div>';
  const overviewEvidenceHtml=files.length?`<section class="case-overview-evidence"><div class="case-overview-evidence-head"><div><span class="case-mini-kicker">YOUR PROOF, SAVED</span><h3>Evidence attached</h3><p>${files.length} original item${files.length===1?'':'s'} stored in this case. Open them again whenever you need.</p></div><button type="button" class="button button-outline" data-action="open-evidence">View all ${files.length} ↗</button></div><div class="case-overview-evidence-items">${files.slice(0,3).map((file,index)=>{const mime=String(file.mime_type||'').toLowerCase(),url=`/api/cases/${encodeURIComponent(c.case_id)}/evidence/${encodeURIComponent(file.evidence_id)}?inline=true`,kind=mime.startsWith('image/')?'Photo':mime.startsWith('video/')?'Video':mime.startsWith('audio/')?'Audio':mime==='application/pdf'?'PDF':'File',glyph=mime.startsWith('image/')?'▧':mime.startsWith('video/')?'▶':mime.startsWith('audio/')?'♪':mime==='application/pdf'?'PDF':'↗';return `<a class="case-overview-evidence-item" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer"><span class="case-overview-evidence-glyph">${glyph}</span><span><b>${escapeHtml(file.original_name||kind)}</b><small>E-${String(index+1).padStart(3,'0')} · ${kind} · ${Math.ceil(Number(file.size_bytes||0)/1024)} KB</small></span><span class="case-overview-evidence-open">Open ↗</span></a>`;}).join('')}</div>${files.length>3?`<small class="case-overview-evidence-more">And ${files.length-3} more saved item${files.length-3===1?'':'s'} in Evidence &amp; receipts.</small>`:''}</section>`:`<section class="case-overview-evidence is-empty"><div class="case-overview-evidence-head"><div><span class="case-mini-kicker">KEEP YOUR PROOF TOGETHER</span><h3>No evidence added yet</h3><p>You can add a payment screenshot, receipt, PDF or support recording whenever you're ready.</p></div><button type="button" class="button button-outline" data-action="open-evidence">Add evidence ↗</button></div></section>`;
  const sourceMap=Object.fromEntries(sources.map(source=>[source.id,source]));
  const planHtml=steps.length?steps.map((item,index)=>{
    const refs=(item.source_ids||[]).map(id=>sourceMap[id]).filter(Boolean).map(source=>`<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.organization)} ↗</a>`).join(' · ');
    return `<details class="case-step-accordion" ${index===0?'open':''}><summary><span class="case-step-index">${String(index+1).padStart(2,'0')}</span><span class="case-step-title"><b>${escapeHtml(item.title)}</b><small>${index===0?'Recommended starting point':item.priority==='urgent'?'Time-sensitive':'Next in your plan'}</small></span><span class="case-step-chevron" aria-hidden="true">⌄</span></summary><div class="case-step-body"><p>${escapeHtml(item.detail)}</p>${item.why?`<small>${escapeHtml(item.why)}</small>`:''}${refs?`<div class="case-step-source">Source: ${refs}</div>`:''}</div></details>`;
  }).join(''):'<p class="muted-note">Rebuild the guidance plan to see the next steps for this case.</p>';
  const sourceHtml=sources.length?sources.map(source=>`<a class="case-source-card" href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer"><span>${escapeHtml(source.organization)}</span><b>${escapeHtml(source.title)} ↗</b><small>Reviewed ${escapeHtml(source.reviewed_on||'date not recorded')}</small></a>`).join(''):'<p class="muted-note">No external guidance source was attached to this plan.</p>';
  const supportRoutesHtml=supportDestinations.length?`<section class="case-workspace-card case-support-routes"><div class="case-card-heading-v2"><div><span class="case-mini-kicker">MATCHED TO YOUR CASE</span><h2>Official support for your situation</h2><p>Start with the channel that matches your merchant or payment route. BolKeResolve has not contacted it for you.</p></div><span class="case-user-reported-tag">Official links</span></div><div class="case-support-route-grid">${supportDestinations.slice(0,2).map(destination=>{const href=safeHttpsUrl(destination.url);return `<article class="case-support-route ${destination.id==='cybercrime_india'?'is-urgent':''}"><span class="case-support-route-label">${escapeHtml(destination.id==='cybercrime_india'?'SAFETY ROUTE':'SUPPORT ROUTE')}</span><h3>${escapeHtml(destination.name||'Official support')}</h3><p>${escapeHtml(destination.action||'Open the official support channel and follow its current instructions.')}</p>${destination.note?`<small>${escapeHtml(destination.note)}</small>`:''}<div class="case-support-route-actions">${href?`<a class="button button-outline" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(destination.label||'Open official support')} ↗</a>`:''}<button type="button" class="button button-quiet" data-case-tab="draft">Prepare message</button></div></article>`;}).join('')}</div></section>${c.merchant?nchDirectoryMarkup(resolution.nch_directory_match):''}`:'';
  const missing=resolution.missing_information||[];
  const missingHtml=missing.length?`<div class="case-missing-list">${missing.slice(0,4).map(value=>`<span>＋ ${escapeHtml(value)}</span>`).join('')}</div>`:'<p class="case-quiet-copy">You’ve shared the key details currently needed for this first plan.</p>';
  const provenanceFacts=c.fact_provenance||[];
  const provenanceRows=provenanceFacts.map(f=>{
    const value=f.field==='amount'&&f.value!=='Not provided'?money(f.value):f.value;
    return `<div class="case-provenance-row"><div><b>${escapeHtml(f.label||f.field)}</b><small>${escapeHtml(value||'Not provided')}</small></div><div><span class="case-provenance-origin">${escapeHtml(f.origin||'Source not recorded')}</span><small>${escapeHtml(f.status||'User-reported')}</small></div></div>`;
  }).join('');
  const confirmedEvidenceFacts=c.evidence_fact_sources||[];
  const confirmedEvidenceFactsHtml=confirmedEvidenceFacts.length?`<div class="case-confirmed-source-facts"><b>Details confirmed from uploaded files</b>${confirmedEvidenceFacts.map(item=>`<div class="case-confirmed-source-fact"><span>${escapeHtml(({merchant:'Merchant / app',amount:'Amount',payment_date:'Date found',payment_status:'Status wording'})[item.field_key]||item.field_key)}</span><strong>${escapeHtml(item.field_key==='amount'?money(item.value):String(item.value??''))}</strong><small>${escapeHtml(item.original_name||'Uploaded evidence')} · ${item.applied_to_case?'Applied to saved case':'Recorded as document detail'} · not independently verified</small></div>`).join('')}</div>`:'';
  const provenanceDisclosure=`<details class="case-provenance-disclosure" id="caseProvenanceDisclosure"><summary><span class="case-provenance-icon" aria-hidden="true">ⓘ</span><span><b>Where these details came from</b><small>${provenanceFacts.length} facts · evidence is not independently verified</small></span><span class="case-disclosure-chevron" aria-hidden="true">＋</span></summary><div class="case-provenance-content"><p>Source labels explain how information entered this case; they do not prove the underlying payment or claim is true.</p><div class="case-provenance-grid">${provenanceRows||'<p>No source labels are available for this older case.</p>'}</div>${confirmedEvidenceFactsHtml}<div class="case-provenance-evidence-note">${files.length?`${files.length} uploaded file${files.length===1?'':'s'} · Uploaded by you · File contents and authenticity are not independently verified.`:'No evidence files uploaded yet.'}</div></div></details>`;
  const progressOptions=['Needs next step','Contacted support','Awaiting response','Follow-up needed','Resolved (user-reported)'].map(v=>`<option value="${escapeHtml(v)}" ${(c.case_stage||'Needs next step')===v?'selected':''}>${escapeHtml(v)}</option>`).join('');
  const issueOptions=['Refund not received','Failed UPI payment','UPI payment pending / recipient not credited','Duplicate charge','Incorrect amount','Order paid but not received','Suspected fraud or unauthorised transaction','Other payment issue'].map(v=>`<option value="${escapeHtml(v)}" ${c.issue_type===v?'selected':''}>${escapeHtml(v)}</option>`).join('');
  const languageOptions=Object.entries(languageNames).filter(([key])=>key!=='auto').map(([key,label])=>`<option value="${escapeHtml(key)}" ${c.language_code===key?'selected':''}>${escapeHtml(label)}</option>`).join('');
  const draftHtml=c.support_draft?`<div class="case-draft-preview"><div class="case-draft-preview-top"><div><span class="case-mini-kicker">READY TO REVIEW</span><h3>Message to ${escapeHtml(c.merchant||'support')} support</h3><p>Built from the details saved in this case. Correct anything that is wrong or missing.</p></div><span class="case-draft-state">Not sent</span></div><div class="draft-context-strip"><span><small>ISSUE</small><b>${escapeHtml(c.issue_type||'Payment issue')}</b></span><span><small>AMOUNT</small><b>${escapeHtml(money(c.amount))}</b></span><span><small>APP CASE ID</small><b>${escapeHtml(c.case_id)}</b></span></div><label class="draft-message-label" for="draftOutput">Message text <span>Editable copy · nothing sent automatically</span></label><textarea id="draftOutput" rows="14" class="draft-output draft-output-editor" aria-label="Edit your support message" maxlength="8000" spellcheck="true">${escapeHtml(c.support_draft)}</textarea><div class="draft-actions"><button class="button button-dark" data-action="save-draft">Save edits</button><button class="button button-outline" data-action="copy-draft">Copy message</button><button class="button button-outline" data-action="share-whatsapp-draft">Open WhatsApp draft ↗</button><button class="button button-outline" data-action="share-email-draft">Open email draft ↗</button><button class="button button-outline" data-action="speak-draft">Read aloud</button></div></div>`:'<div class="case-draft-empty"><span class="case-draft-icon">✎</span><h3>Prepare a message with your actual case details</h3><p>We’ll include only facts recorded in this case, make a specific request for this issue, and leave unknown details out. You can review and edit the wording before sharing it.</p></div>';
  const pack=c.action_pack||{}, checklist=pack.evidence_checklist||[], readiness=pack.readiness||{completed_required:0,required_total:0,percent:0};
  const checklistHtml=checklist.map(task=>`<label class="action-check-item"><input type="checkbox" data-checklist-key="${escapeHtml(task.key)}" ${task.checked?'checked':''}><span class="action-check-copy"><b>${escapeHtml(task.title)}</b><small>${escapeHtml(task.detail)}</small></span><em>${task.required?'Needed':'Helpful'}</em></label>`).join('');
  const follow=c.follow_up||pack.follow_up||{}, followStatus=({overdue:'Past due',due_today:'Due today',upcoming:'Scheduled',completed:'Marked complete',not_set:'No date set'})[pack.follow_up?.status||'not_set']||'No date set';
  const sourceMini=(pack.official_sources||[]).map(source=>`<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer"><b>${escapeHtml(source.organization)}</b><small>${escapeHtml(source.title)} ↗</small></a>`).join('');
  const currentOutcome=c.outcome||{};
  const outcomeLabels={still_pending:'Still pending',no_response:'No response',partially_resolved:'Partially resolved',resolved:'Resolved (user-reported)',stopped:'Stopped pursuing for now'};
  const outcomeSummary=currentOutcome.outcome_code?`<div class="passport-outcome-saved"><span class="case-mini-kicker">LATEST OUTCOME · USER-REPORTED</span><b>${escapeHtml(outcomeLabels[currentOutcome.outcome_code]||currentOutcome.outcome_code)}</b>${currentOutcome.details?`<p>${escapeHtml(currentOutcome.details)}</p>`:''}${currentOutcome.reference?`<small>Reference recorded: ${escapeHtml(currentOutcome.reference)}</small>`:''}<small>Last updated ${escapeHtml(prettyDate(currentOutcome.updated_at||currentOutcome.created_at))}</small></div>`:'<div class="passport-outcome-empty"><b>No outcome recorded yet</b><p>When something changes, record what happened. This helps keep your own history clear; it does not verify a merchant or bank action.</p></div>';
  const outcomeHtml=`<section class="case-workspace-card case-tab-content-card passport-outcome-card"><div class="case-card-heading-v2"><div><span class="case-mini-kicker">CLOSE THE LOOP</span><h2>What happened next?</h2><p>Record what you experienced after taking the suggested steps. Your outcome stays part of this private case record.</p></div><span class="case-user-reported-tag">Self-reported</span></div><div class="passport-outcome-layout"><div>${outcomeSummary}<div class="case-honesty-note"><span>i</span><p><b>Reported does not mean verified.</b><br>BolKeResolve does not automatically check whether a refund arrived or a complaint was accepted. Do not share private reference numbers with other people unless needed.</p></div></div><form id="caseOutcomeForm" class="passport-outcome-form"><label class="case-field-v2"><span>Current outcome</span><select id="caseOutcomeCode" required><option value="still_pending" ${currentOutcome.outcome_code==='still_pending'?'selected':''}>Still pending</option><option value="no_response" ${currentOutcome.outcome_code==='no_response'?'selected':''}>No response from the organisation</option><option value="partially_resolved" ${currentOutcome.outcome_code==='partially_resolved'?'selected':''}>Partially resolved</option><option value="resolved" ${currentOutcome.outcome_code==='resolved'?'selected':''}>Resolved</option><option value="stopped" ${currentOutcome.outcome_code==='stopped'?'selected':''}>I stopped pursuing this for now</option></select></label><label class="case-field-v2"><span>What happened? <small>(optional)</small></span><textarea id="caseOutcomeDetails" rows="4" maxlength="1000" placeholder="e.g. Support replied and asked me to wait two more days">${escapeHtml(currentOutcome.details||'')}</textarea></label><label class="case-field-v2"><span>Reference / ticket number <small>(optional)</small></span><input id="caseOutcomeReference" type="text" maxlength="120" value="${escapeHtml(currentOutcome.reference||'')}" placeholder="Enter only if useful for your own record"></label><p class="case-privacy-caption">The outcome and any reference are included in your private passport export. Review exports before sharing them.</p><button class="button button-dark" type="submit">Save reported outcome ↗</button></form></div></section>`;
  const packHtml=`<section class="case-workspace-card case-tab-content-card action-pack-card">
    <div class="case-card-heading-v2 action-pack-header"><div><span class="case-mini-kicker">YOUR RESOLUTION KIT</span><h2>Prepare once. Act with clarity.</h2><p>Only the essentials: what to do first, what to gather, and when to follow up.</p></div><span class="case-draft-state">Not submitted</span></div>
    <div class="action-pack-overview-grid"><div class="action-pack-first-action"><div class="action-pack-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 12.5 9.5 17 19 7"/></svg></div><span class="case-mini-kicker">YOUR NEXT BEST ACTION</span><p>${escapeHtml(pack.first_action||'Review your saved details and choose the next appropriate step.')}</p><button type="button" class="action-pack-inline-link" data-case-tab="draft">Prepare a support message <span aria-hidden="true">↗</span></button></div>
      <div class="action-pack-readiness"><div class="action-pack-readiness-top"><div><span>Preparation progress</span><b id="actionPackReadinessCount">${readiness.completed_required||0} of ${readiness.required_total||0} required items</b></div><strong id="actionPackReadinessPercent">${readiness.percent||0}%</strong></div><div class="action-pack-progress-track" role="progressbar" aria-label="Evidence preparation progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${readiness.percent||0}"><span id="actionPackReadinessBar" style="width:${readiness.percent||0}%"></span></div><small>Mark an item ready once you have it. We don't inspect files to verify these checks.</small><div class="action-pack-readiness-footer"><span class="action-pack-mini-mark">✓</span><span>Progress saves to this case</span></div></div></div>
    <section class="action-pack-checklist-section"><div class="action-pack-section-top"><div><span class="case-mini-kicker">GET YOUR RECORDS TOGETHER</span><h3>What to prepare</h3><p>Check items as you find them. Required items count toward the progress above.</p></div><span class="action-pack-task-total">${readiness.required_total||0} required</span></div><div class="action-pack-checklist">${checklistHtml||'<p class="muted-note">No checklist items are attached to this issue yet.</p>'}</div></section>
    <div class="action-pack-lower-grid"><section class="action-pack-followup"><div class="action-pack-section-heading"><div><span class="case-mini-kicker">DON’T LOSE THE THREAD</span><h3>Choose a follow-up date</h3><p>Save a reminder in the case. No notification will be sent unless a reminder channel is connected.</p></div><span class="followup-status-chip status-${escapeHtml(pack.follow_up?.status||'not_set')}">${escapeHtml(followStatus)}</span></div>
      <form id="caseFollowupForm" class="action-pack-followup-form"><label><span>Follow-up date</span><input type="date" id="caseFollowupDate" value="${escapeHtml(follow.due_date||'')}"></label><label><span>Private note <small>(optional)</small></span><input type="text" id="caseFollowupNote" maxlength="300" value="${escapeHtml(follow.note||'')}" placeholder="e.g. Follow up if no response"></label><label class="action-pack-done-toggle"><input type="checkbox" id="caseFollowupCompleted" ${follow.completed?'checked':''}><span>Mark this follow-up complete</span></label><div class="action-pack-buttons"><button class="button button-dark" type="submit">Save reminder</button><button class="button button-outline" type="button" data-action="download-pack">Download text pack ↗</button><button class="button button-outline" type="button" data-action="download-passport-json">Download passport JSON</button><button class="button button-outline" type="button" data-action="print-passport">Print / Save PDF ↗</button><button class="button button-outline" type="button" data-action="copy-pack">Copy pack</button></div></form>
    </section><section class="action-pack-sources"><div class="action-pack-section-top"><div><span class="case-mini-kicker">CHECK THE ORIGINAL SOURCE</span><h3>Official guidance</h3><p>Open the source before relying on a deadline or escalation route.</p></div><span class="action-pack-source-mark" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M14 4h6v6M20 4l-9 9"/><path d="M18 13v6H5V6h6"/></svg></span></div><div class="action-pack-sources-grid">${sourceMini||'<p class="muted-note">No official source is attached to this plan. Refresh guidance after reviewing case details.</p>'}</div></section></div>
    <p class="case-privacy-caption">This pack uses your saved description and public guidance. Nothing is submitted or sent automatically. Never share OTPs, UPI PINs, passwords or full payment credentials.</p></section>`;
  const currentStep=steps[0]||null;
  const completion=c.completion_loop||{};
  const completionAction=completion.action||{};
  const focusTitle=completionAction.title||currentStep?.title||'Make your next step clear';
  const focusDetail=completionAction.detail||currentStep?.detail||'Refresh the guidance to match the details currently saved in your case.';
  const completionTarget=['draft','prep','progress','evidence'].includes(completionAction.target)?completionAction.target:'draft';
  const completionLoopMarkup=`<div class="completion-loop-strip" data-completion-state="${escapeHtml(completion.state||'initial')}"><div class="completion-loop-state"><span class="completion-loop-pulse" aria-hidden="true"></span><span><b>${escapeHtml(completion.state_label||'Next step')}</b><small>${escapeHtml(completion.next_milestone||'Choose the next useful action')}</small></span></div>${completion.last_recorded_update?`<p class="completion-loop-last-update">Last recorded: ${escapeHtml(prettyDate(completion.last_recorded_update.at))}</p>`:''}</div>${completion.reply_context?`<p class="completion-loop-reply-context">Next step updated using your reviewed support reply: <b>${escapeHtml(completion.reply_context.label)}</b>. Original text is not retained by reply review; the sender's claims are not independently verified.</p>`:''}`;
  const safeStage=escapeHtml(c.case_stage||'Needs next step');
  const shareRetryMarkup=pendingSharedIntakeToken&&pendingSharedIntakeAttachCaseId===c.case_id?`<div class="shared-intake-retry"><div><b>One shared item still needs adding</b><p>The case was saved, but the shared file or note could not be attached yet.</p></div><button type="button" class="button button-dark" data-action="retry-shared-intake">Finish adding item ↗</button></div>`:'';
  const primaryActionCard = `
          <article id="casePrimaryAction" class="case-focus-card case-guided-focus case-primary-next-action ${resolution.urgency?.level==='urgent'?'is-urgent':''}">
            <div class="case-focus-meta"><span class="case-focus-badge">${resolution.urgency?.level==='urgent'?'SAFETY FIRST':'YOUR NEXT STEP'}</span><span class="case-confidence ${classification.confidence==='high'?'confidence-high':classification.confidence==='medium'?'confidence-medium':'confidence-low'}">${escapeHtml(classification.confidence||'unrated')} confidence</span></div>
            <p class="case-guided-eyebrow">ONE THING TO DO NOW</p>
            ${completionLoopMarkup}
            <h2>${escapeHtml(focusTitle)}</h2>
            <p class="case-guided-explanation">${escapeHtml(focusDetail)}</p>
            ${completion.why?`<p class="completion-loop-why">${escapeHtml(completion.why)}</p>`:''}
            ${savedCaseFastPathQuestionMarkup(resolution)}
            <div class="case-guided-primary-row"><button type="button" class="button button-dark case-guided-primary" data-case-tab="${completionTarget}">${escapeHtml(completionAction.button|| (c.support_draft?'Review support message':'Prepare support message'))} <span aria-hidden="true">↗</span></button><span class="case-trust-note"><span>✓</span> Based on what you shared, not bank verification</span></div>
            <div class="case-guided-safety"><span aria-hidden="true">!</span><p>Never share an OTP, UPI PIN, password or full card number. Nothing is sent without your review.</p></div>
            ${rulebookMarkup(resolution.rulebook,'case-rulebook')}
          </article>
  `;
  $('#caseDetailContent').innerHTML=`
    <div class="case-detail-v2">
      ${shareRetryMarkup}
      <header class="case-detail-header-v2">
        <div class="case-detail-title-block">
          <div class="case-id-line"><span class="case-id-mark"></span><span>RESOLUTION PASSPORT · CASE ${escapeHtml(c.case_id)}</span><span class="case-id-separator">·</span><span>Updated ${escapeHtml(prettyDate(c.updated_at||c.created_at))}</span></div>
          <h1>${escapeHtml(c.issue_type||classification.issue_type||'Payment issue')}</h1>
          <p>${escapeHtml(c.merchant||'Organisation not provided')} <span>·</span> Created ${escapeHtml(prettyDate(c.created_at))}</p>
        </div>
        <div class="case-header-actions"><span class="case-status-pill">${safeStage}</span><button type="button" class="button button-mint" data-action="resume-live">Continue live ↗</button><button type="button" class="button button-danger" data-action="delete-case">Delete case</button></div>
      </header>
      ${primaryActionCard}
      <section class="case-snapshot-strip" aria-label="Case summary">
        <div class="case-snapshot-amount"><span>AMOUNT AT ISSUE</span><strong>${escapeHtml(money(c.amount))}</strong><small>As you reported it</small></div>
        <div class="case-snapshot-cell"><span>MERCHANT / APP</span><b>${escapeHtml(c.merchant||'Not added yet')}</b></div>
        <div class="case-snapshot-cell"><span>PAYMENT DATE</span><b>${escapeHtml(c.payment_date||'Not added yet')}</b></div>
        <div class="case-snapshot-cell"><span>EVIDENCE</span><b>${files.length} ${files.length===1?'file':'files'}</b></div>
      </section>
      ${provenanceDisclosure}
      <details class="case-tools-menu" id="caseToolsMenu">
        <summary><span class="case-tools-summary-icon" aria-hidden="true">＋</span><span class="case-tools-summary-copy"><b>More case tools</b><small>Messages, evidence and progress — only when you need them</small></span><span class="case-tools-summary-chevron" aria-hidden="true">⌄</span></summary>
        <nav class="case-workspace-tabs" role="tablist" aria-label="Case tools">
          <button type="button" id="caseTabOverview" class="case-workspace-tab" role="tab" data-case-tab="overview" aria-controls="casePanelOverview" aria-selected="true"><span>01</span><b>Plan &amp; details</b><small>Full plan and case facts</small></button>
          <button type="button" id="caseTabPrep" class="case-workspace-tab" role="tab" data-case-tab="prep" aria-controls="casePanelPrep" aria-selected="false"><span>02</span><b>Prepare &amp; contact</b><small>${files.length} files · ${c.support_draft?'Message ready':'Message optional'}</small></button>
          <button type="button" id="caseTabProgress" class="case-workspace-tab" role="tab" data-case-tab="progress" aria-controls="casePanelProgress" aria-selected="false"><span>03</span><b>Progress</b><small>${escapeHtml(c.case_stage||'Needs next step')}</small></button>
        </nav>
      </details>
      <section id="casePanelOverview" class="case-tab-panel" data-tab-panel="overview" role="tabpanel" aria-labelledby="caseTabOverview" tabindex="0">
        <div class="case-guided-overview">
          <p class="case-secondary-panel-intro">Your recommended action stays above. Open the full plan or case details below when you need them.</p>
          ${overviewEvidenceHtml}
          <details class="case-secondary-disclosure case-guided-disclosure" id="caseFullPlanDisclosure">
            <summary><span class="case-secondary-icon" aria-hidden="true">↗</span><span><b>See the full resolution plan</b><small>${steps.length} recommended step${steps.length===1?'':'s'} · official guidance</small></span><span class="case-disclosure-chevron" aria-hidden="true">＋</span></summary>
            <div class="case-secondary-disclosure-content">
              <section class="case-workspace-card case-plan-card">
                <div class="case-card-heading-v2"><div><span class="case-mini-kicker">YOUR RESOLUTION PLAN</span><h2>Steps to follow</h2><p>Start with the first step. Open another only when you need it.</p></div><button type="button" class="case-text-action" data-action="refresh-guidance">Refresh plan ↻</button></div>
                <div class="case-step-accordion-list">${planHtml}</div>
                <details class="case-sources-disclosure"><summary>Official guidance and sources <span>${sources.length}</span></summary><div class="case-source-grid-v2">${sourceHtml}</div><p class="case-source-footnote">Sources were last reviewed ${escapeHtml(resolution.generated_at||'when the plan was created')}. Open the official page before acting.</p></details>
              </section>
            </div>
          </details>

          <details class="case-secondary-disclosure case-guided-disclosure" id="caseOverviewDetailsDisclosure">
            <summary><span class="case-secondary-icon" aria-hidden="true">≡</span><span><b>Case details</b><small>${missing.length?`${missing.length} detail${missing.length===1?'':'s'} could make the guidance more specific`:'Review or correct the information you shared'}</small></span><span class="case-disclosure-chevron" aria-hidden="true">＋</span></summary>
            <div class="case-secondary-disclosure-content">
              <section class="case-workspace-card case-precision-card case-guided-missing"><div class="case-card-heading-v2"><div><span class="case-mini-kicker">OPTIONAL DETAILS</span><h2>Make the advice more specific</h2></div><span class="case-count-badge">${missing.length}</span></div>${missingHtml}<button type="button" class="case-subtle-button" data-action="open-edit-details">Review or edit details <span>↗</span></button></section>
              <section class="case-workspace-card case-story-card-v2">
                <div class="case-card-heading-v2"><div><span class="case-mini-kicker">YOUR WORDS</span><h2>What you told us</h2></div><span class="case-user-reported-tag">User-reported</span></div>
                <details class="case-story-disclosure"><summary>Read the full story you shared</summary><p>${escapeHtml(c.description||'No description saved.')}</p></details>
                <details class="case-edit-disclosure"><summary>Correct details or add missing information</summary>
                  <form id="caseEditForm" class="case-edit-form">
                    <label><span>Issue type</span><select name="issue_type">${issueOptions}</select></label>
                    <label><span>Merchant or app</span><input name="merchant" maxlength="100" value="${escapeHtml(c.merchant||'')}" placeholder="e.g. Zomato"></label>
                    <label><span>Amount (₹)</span><input name="amount" type="number" min="0" max="100000000" step="0.01" value="${c.amount===null||c.amount===undefined?'':escapeHtml(c.amount)}" placeholder="850"></label>
                    <label><span>Payment date</span><input name="payment_date" type="date" value="${escapeHtml(c.payment_date||'')}"></label>
                    <label><span>Status shown in the app</span><select name="payment_status"><option value="unknown" ${c.payment_status==='unknown'?'selected':''}>Not sure yet</option><option value="failed" ${c.payment_status==='failed'?'selected':''}>Failed</option><option value="pending" ${c.payment_status==='pending'?'selected':''}>Pending</option><option value="successful" ${c.payment_status==='successful'?'selected':''}>Successful</option><option value="refund_pending" ${c.payment_status==='refund_pending'?'selected':''}>Refund pending</option><option value="unauthorized" ${c.payment_status==='unauthorized'?'selected':''}>I don’t recognise this payment</option></select></label>
                    <label><span>Have you contacted support?</span><select name="contacted_support"><option value="" ${c.contacted_support===null||c.contacted_support===undefined?'selected':''}>Not answered</option><option value="yes" ${c.contacted_support===true?'selected':''}>Yes</option><option value="no" ${c.contacted_support===false?'selected':''}>Not yet</option></select></label>
                    <label class="case-edit-wide"><span>Your description</span><textarea name="description" minlength="8" maxlength="5000" rows="4" required>${escapeHtml(c.description||'')}</textarea></label>
                    <label><span>Case language</span><select name="language_code">${languageOptions}</select></label>
                    <div class="case-edit-submit"><button type="submit" class="button button-dark">Save and update plan ↗</button><span>Your saved facts and next steps will be updated.</span></div>
                  </form>
                </details>
              </section>
            </div>
          </details>
        </div>
      </section>
      <section id="casePanelPrep" class="case-tab-panel" data-tab-panel="prep" role="tabpanel" aria-labelledby="caseTabPrep" tabindex="0" hidden>
        <div class="case-combined-panel-intro"><span class="case-mini-kicker">PREPARE &amp; CONTACT</span><h2>Get ready, then reach out</h2><p>Gather useful records, review your message, and decide when you want to share it. Nothing is sent automatically.</p></div>
        <button type="button" class="case-back-link" data-case-tab="overview">← Back to your next step</button>
        ${supportRoutesHtml}
        <details id="caseMessageDisclosure" class="case-secondary-disclosure">
          <summary><span class="case-secondary-icon" aria-hidden="true">✎</span><span><b>Support message</b><small>${c.support_draft?'Your draft is ready to review':'Prepare a message in your preferred language'}</small></span><span class="case-disclosure-chevron">＋</span></summary>
          <div class="case-secondary-disclosure-content"><section id="caseMessageSection" class="case-workspace-card case-tab-content-card case-message-workspace"><div class="case-card-heading-v2"><div><span class="case-mini-kicker">YOU STAY IN CONTROL</span><h2>Review before sharing</h2><p>Choose a language, review the wording, and copy it into the organisation’s official channel.</p></div><span class="case-draft-state">Not sent</span></div>
            ${draftHtml}
            <div class="message-language-heading"><b>Prepare in another language</b><span>Changing language replaces the draft. Save your edits first.</span></div><div class="case-message-options"><button class="button button-dark" data-action="draft-en">English</button><button class="button button-outline" data-action="draft-hi">हिन्दी</button><button class="button button-outline" data-action="draft-hinglish">Hinglish</button></div>
            <p class="case-privacy-caption">BolKeResolve does not email or send this message automatically. Check every detail before sharing.</p>
          </section></div>
        </details>
        <details id="caseEvidenceDisclosure" class="case-secondary-disclosure">
          <summary><span class="case-secondary-icon" aria-hidden="true">＋</span><span><b>Evidence &amp; receipts</b><small>${files.length?`${files.length} file${files.length===1?'':'s'} saved`:'Add receipts, screenshots or confirmations'}</small></span><span class="case-disclosure-chevron">＋</span></summary>
          <div class="case-secondary-disclosure-content"><section id="caseEvidenceSection" class="case-workspace-card case-tab-content-card"><div class="case-card-heading-v2"><div><span class="case-mini-kicker">KEEP THE PROOF TOGETHER</span><h2>Evidence</h2><p>Receipts, screenshots and support references can help when you contact the organisation.</p></div><span class="case-count-badge">${files.length}</span></div>
            <div class="case-evidence-list">${evidenceHtml}</div><div id="caseEvidenceReviewResults" class="case-evidence-review-results" aria-live="polite" hidden></div>
            <form id="detailEvidenceForm" class="case-upload-form"><label class="case-upload-drop" for="detailEvidenceInput"><span class="case-upload-symbol">↑</span><span><b>Add evidence</b><small>Redacted PNG, JPG, WEBP or PDF · up to 8 MB</small></span><span class="case-upload-browse">Browse</span><input type="file" id="detailEvidenceInput" accept=".png,.jpg,.jpeg,.webp,.pdf"></label><button class="button button-dark" type="submit">Upload selected file ↗</button></form>
            <p class="case-privacy-caption">Only upload documents you’re comfortable storing here. Hide OTPs, UPI PINs, full card numbers and unrelated personal details first.</p>
          </section></div>
        </details>

        ${renderCommitmentsPanel(c.commitments||[], files)}
        <details id="caseActionPackDisclosure" class="case-secondary-disclosure case-action-pack-disclosure">
          <summary><span class="case-secondary-icon" aria-hidden="true">☷</span><span><b>Checklist, reminders and exports</b><small>Extra tools for when support asks for more information</small></span><span class="case-disclosure-chevron" aria-hidden="true">＋</span></summary>
          <div class="case-secondary-disclosure-content">${packHtml}</div>
        </details>
        <details id="caseInboxBridgeDisclosure" class="case-secondary-disclosure case-inbox-bridge-disclosure">
          <summary><span class="case-secondary-icon" aria-hidden="true">✉</span><span><b>Forward a support reply into this case</b><small>Optional case-specific email inbox · replies are reviewed before use</small></span><span class="case-disclosure-chevron" aria-hidden="true">＋</span></summary>
          <div class="case-secondary-disclosure-content"><section class="case-workspace-card case-inbox-bridge-card"><div class="case-card-heading-v2"><div><span class="case-mini-kicker">OPTIONAL EMAIL BRIDGE</span><h2>Keep the reply with your case</h2><p>Create a private forwarding address for this case. Forward a support email to it, then review the interpretation before it updates the timeline.</p></div><span class="case-user-reported-tag">Not auto-sent</span></div><p class="case-inbox-privacy-note">Forwarded message text is encrypted temporarily while it awaits review. It is cleared when you confirm or discard it, or after the configured retention period. The sender and claims are not independently verified. Attachments are listed, not imported.</p><div id="caseInboxBridgeContent"><button type="button" class="button button-dark" data-action="open-case-inbox">Set up / open case inbox</button><p class="case-privacy-caption">This optional feature appears only when an authenticated inbound-email provider and encryption key are configured for the site. You can continue using the manual reply review without it.</p></div></section></div>
        </details>
      </section>
      <section id="casePanelProgress" class="case-tab-panel" data-tab-panel="progress" role="tabpanel" aria-labelledby="caseTabProgress" tabindex="0" hidden>
        <div class="case-combined-panel-intro"><span class="case-mini-kicker">YOUR CASE, YOUR RECORD</span><h2>Track what happens next</h2><p>Record your actions and replies here. These updates are yours; they are not live verification from a bank or merchant.</p></div>
        <button type="button" class="case-back-link" data-case-tab="overview">← Back to your next step</button>
        <section id="caseFollowThroughSection" class="case-follow-through-content case-progress-tools">
          <section class="case-workspace-card case-progress-card-v2">
              <div class="case-card-heading-v2"><div><span class="case-mini-kicker">YOUR FOLLOW-THROUGH</span><h2>Track progress</h2></div><span class="case-user-reported-tag">Self-reported</span></div>
              <p class="case-side-description">Update this after you take an action or receive a reply. We don’t receive status updates from banks or merchants.</p>
              <ol class="case-progress-rail">${['Needs next step','Contacted support','Awaiting response','Follow-up needed','Resolved (user-reported)'].map((label,index)=>`<li class="${index<activeIndex?'is-complete':index===activeIndex?'is-active':''}"><span>${index<activeIndex?'✓':index+1}</span><b>${escapeHtml(label)}</b></li>`).join('')}</ol>
              <div class="case-event-capture"><div class="case-event-capture-heading"><b>What changed since your last visit?</b><span>One tap updates your timeline</span></div><div class="case-event-quick-grid"><button type="button" data-case-event="contacted_support">I contacted support</button><button type="button" data-case-event="still_waiting">Still waiting</button><button type="button" data-case-event="response_received">I got a reply</button><button type="button" data-case-event="submission_reported">I submitted a complaint</button><button type="button" data-case-event="resolved" class="case-event-resolved">It’s resolved</button></div><label class="case-field-v2"><span>Optional note or reply summary</span><input id="caseEventDetails" type="text" maxlength="1000" placeholder="e.g. Support asked me to wait 3 more days"></label><label class="case-field-v2"><span>Reference number (optional)</span><input id="caseEventReference" type="text" maxlength="120" placeholder="Complaint or docket reference"></label></div>
              <label class="case-field-v2"><span>Current status</span><select id="caseProgressSelect">${progressOptions}</select></label>
              <label class="case-field-v2"><span>Private note (optional)</span><input id="caseProgressNote" type="text" maxlength="500" placeholder="e.g. Called support today"></label>
              <button type="button" class="button button-mint case-save-progress" data-action="update-progress">Save progress <span>↗</span></button>
            </section>
            <section class="case-workspace-card passport-portability-card"><div class="case-card-heading-v2"><div><span class="case-mini-kicker">YOUR CASE, PORTABLE</span><h2>Take your passport anywhere</h2><p>You can keep working even when no messaging API is connected. Export your record or open a reviewed message in an app you already use.</p></div><span class="case-user-reported-tag">You control sharing</span></div><div class="passport-portability-actions"><button type="button" class="button button-dark" data-action="print-passport">Print / Save as PDF ↗</button><button type="button" class="button button-outline" data-action="download-passport-json">Download portable JSON</button><button type="button" class="button button-outline" data-case-tab="draft">Prepare a message</button></div><p class="case-privacy-caption">Exports can include your story, personal notes and support references. Review the file before sharing it. Nothing is sent automatically.</p></section>
            <div class="case-honesty-note"><span>i</span><p><b>What we know</b><br>These steps use the information you shared. Your bank, payment app and merchant records have not been checked.</p></div>
        </section>
        <details id="caseReplyReviewDisclosure" class="case-secondary-disclosure case-reply-review-disclosure">
          <summary><span class="case-secondary-icon" aria-hidden="true">✉</span><span><b>Understand a support reply</b><small>Review what it may mean before updating your case</small></span><span class="case-disclosure-chevron" aria-hidden="true">＋</span></summary>
          <div class="case-secondary-disclosure-content"><section class="case-workspace-card case-reply-review-card"><div class="case-card-heading-v2"><div><span class="case-mini-kicker">REPLY-AWARE FOLLOW-THROUGH</span><h2>What did support say?</h2><p>Paste the relevant wording to get a cautious first-pass interpretation. Check the original message yourself.</p></div><span class="case-user-reported-tag">Not verified</span></div>
            <form id="caseReplyReviewForm" class="case-reply-review-form"><label class="case-field-v2" for="caseReplyText"><span>Support reply <small>(minimum 8 characters)</small></span><textarea id="caseReplyText" maxlength="8000" minlength="8" required rows="5" placeholder="Example: Your refund has been initiated. Please allow 5–7 business days."></textarea></label><label class="case-field-v2" for="caseReplyReference"><span>Ticket / refund reference <small>(optional)</small></span><input id="caseReplyReference" maxlength="120" placeholder="Add a reference only if you want it saved to your private timeline"></label><p class="case-reply-privacy-note">The preview does not save the pasted reply. Common sensitive patterns are redacted before analysis, but this is not a guarantee. Never include an OTP, UPI PIN, password or full card number.</p><button type="submit" class="button button-dark" id="reviewSupportReplyButton">Review reply <span aria-hidden="true">↗</span></button></form>
            <div id="caseReplyReviewResult" class="case-reply-review-result" hidden aria-live="polite" aria-atomic="true"></div>
          </section></div>
        </details>
        <div id="caseOutcomeSection">${outcomeHtml}</div>
        <details id="caseActivityDisclosure" class="case-secondary-disclosure case-activity-disclosure">
          <summary><span class="case-secondary-icon" aria-hidden="true">↻</span><span><b>Case history</b><small>${events.length} saved ${events.length===1?'update':'updates'} · newest first</small></span><span class="case-disclosure-chevron">＋</span></summary>
          <div class="case-secondary-disclosure-content"><div class="case-activity-layout"><section id="caseActivitySection" class="case-workspace-card case-tab-content-card case-activity-main"><div class="case-card-heading-v2 case-activity-heading"><div><span class="case-mini-kicker">YOUR CASE HISTORY</span><h2>Activity timeline</h2><p>A chronological record of case changes, documents, drafts and your updates.</p></div><span class="case-activity-count">${events.length} ${events.length===1?'update':'updates'}</span></div>
            <div class="case-activity-toolbar"><div class="case-activity-filter-group" role="group" aria-label="Filter activity"><button type="button" class="case-activity-filter active" data-activity-filter="all" aria-pressed="true">All updates</button><button type="button" class="case-activity-filter" data-activity-filter="progress" aria-pressed="false">Progress</button><button type="button" class="case-activity-filter" data-activity-filter="documents" aria-pressed="false">Files &amp; messages</button><button type="button" class="case-activity-filter" data-activity-filter="notes" aria-pressed="false">Notes</button></div><span class="case-activity-order">Newest first ↓</span></div>
            <div class="case-activity-timeline" aria-live="polite">${eventsHtml}<p class="case-activity-filter-empty" hidden>No updates in this category yet.</p></div>
            <form id="timelineNoteForm" class="case-add-note-form"><div class="case-add-note-heading"><span class="case-mini-kicker">ADD CONTEXT</span><b>Add a private note</b><p>Record a promise, reference, or what the organisation told you.</p></div><div><input id="timelineNoteText" type="text" maxlength="1000" placeholder="e.g. Support said to wait until Friday" required><button class="button button-dark" type="submit"><span aria-hidden="true">＋</span> Add note</button></div></form>
          </section><aside class="case-activity-side"><section class="case-activity-summary-card"><span class="case-mini-kicker">CASE SNAPSHOT</span><strong>${events.length}</strong><b>Saved updates</b><p>These events reflect information recorded in BolKeResolve, not a live feed from your bank or merchant.</p><button type="button" class="button button-outline" data-case-tab="prep">Open preparation kit ↗</button></section><div class="case-honesty-note"><span>i</span><p><b>Your record stays honest</b><br>Only your reported actions and app events appear here. External services are not checked automatically.</p></div></aside></div></div>
        </details>
      </section>
    </div>`;
  switchCaseTab(activeCaseTab);
  $('#detailEvidenceForm')?.addEventListener('submit',uploadMoreEvidence);
  $('#timelineNoteForm')?.addEventListener('submit',addTimelineNote);
  $('#caseEditForm')?.addEventListener('submit',saveCaseDetails);
  $('#caseFollowupForm')?.addEventListener('submit',saveCaseFollowup);
  $('#caseOutcomeForm')?.addEventListener('submit',saveCaseOutcome);
  $('#caseReplyReviewForm')?.addEventListener('submit',reviewSupportReply);
  const panel=$('#caseDetailContent');
  if(panel&&!panel.dataset.eventsBound){panel.addEventListener('click',detailActionHandler);panel.dataset.eventsBound='1';}
  if(panel&&!panel.dataset.checklistEventsBound){panel.addEventListener('change',handleCaseChecklistChange);panel.dataset.checklistEventsBound='1';}
}
async function handleCaseChecklistChange(event){
  const input=event.target.closest('[data-checklist-key]');if(!input)return;
  const key=input.dataset.checklistKey;input.disabled=true;
  try{
    const result=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/checklist/${encodeURIComponent(key)}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({checked:input.checked})});
    const pack=result.action_pack||{},ready=pack.readiness||{};
    const percent=Number(ready.percent||0),bar=$('#actionPackReadinessBar'),percentNode=$('#actionPackReadinessPercent'),countNode=$('#actionPackReadinessCount');
    if(bar){bar.style.width=`${percent}%`;bar.parentElement?.setAttribute('aria-valuenow',String(percent));}if(percentNode)percentNode.textContent=`${percent}%`;if(countNode)countNode.textContent=`${ready.completed_required||0} of ${ready.required_total||0} needed items ready`;
    const prepTab=$('.case-workspace-tabs [data-case-tab="prep"]');if(prepTab){const meta=prepTab.querySelector('small');if(meta)meta.textContent=`${percent}% checklist ready · ${meta.textContent.split(' · ').slice(-1)[0]||'Message optional'}`;}
    showToast(input.checked?'Marked as ready.':'Checklist item updated.');
  }catch(error){input.checked=!input.checked;showToast(error.message||'Could not save this checklist item.','error');}
  finally{input.disabled=false;}
}
async function saveCaseFollowup(event){
  event.preventDefault();const button=event.submitter||event.currentTarget.querySelector('button[type="submit"]');if(button){button.disabled=true;button.textContent='Saving…';}
  try{
    await api(`/api/cases/${encodeURIComponent(currentCaseId)}/follow-up`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({due_date:$('#caseFollowupDate')?.value||'',note:$('#caseFollowupNote')?.value?.trim()||'',completed:!!$('#caseFollowupCompleted')?.checked})});
    await loadCase(currentCaseId);switchCaseTab('progress');showToast('Follow-up reminder saved in your case.');
  }catch(error){showToast(error.message||'Could not save the reminder.','error');}
  finally{if(button){button.disabled=false;button.textContent='Save reminder';}}
}
async function saveCaseOutcome(event){
  event.preventDefault();
  const outcome_code=$('#caseOutcomeCode')?.value,details=$('#caseOutcomeDetails')?.value?.trim()||'',reference=$('#caseOutcomeReference')?.value?.trim()||'';
  if(!outcome_code)return;
  const button=$('#caseOutcomeForm button[type="submit"]');
  if(button){button.disabled=true;button.textContent='Saving outcome…';}
  try{
    await api(`/api/cases/${encodeURIComponent(currentCaseId)}/outcome`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({outcome_code,details,reference})});
    await loadCase(currentCaseId);switchCaseTab('outcome');await refreshCaseCountOnly();showToast('Outcome saved to your passport as user-reported.');
  }catch(error){showToast(error.message||'Could not save the outcome.','error');}
  finally{const current=$('#caseOutcomeForm button[type="submit"]');if(current){current.disabled=false;current.textContent='Save reported outcome ↗';}}
}
async function saveCaseDetails(event){
  event.preventDefault();
  const form=event.currentTarget,fd=new FormData(form),amountRaw=String(fd.get('amount')||'').trim(),support=String(fd.get('contacted_support')||'');
  const payload={
    issue_type:String(fd.get('issue_type')||'Other payment issue'),
    merchant:String(fd.get('merchant')||'').trim(),
    amount:amountRaw&&Number.isFinite(Number(amountRaw))?Number(amountRaw):null,
    payment_date:String(fd.get('payment_date')||''),
    language_code:String(fd.get('language_code')||'hi-IN'),
    payment_status:String(fd.get('payment_status')||'unknown'),
    contacted_support:support===''?null:support==='yes',
    description:String(fd.get('description')||'').trim()
  };
  const button=form.querySelector('[type="submit"]');if(button){button.disabled=true;button.textContent='Saving changes…';}
  try{await api(`/api/cases/${encodeURIComponent(currentCaseId)}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});await loadCase(currentCaseId);await refreshCaseCountOnly();showToast('Details saved and your guidance plan updated.');}
  catch(error){showToast(error.message,'error');if(button){button.disabled=false;button.textContent='Save and update plan ↗';}}
}
async function uploadMoreEvidence(event){event.preventDefault();const input=$('#detailEvidenceInput'),file=input.files?.[0];if(!file){showToast('Choose a file first.','error');return;}if(file.size>8*1024*1024){showToast('Evidence files must be 8 MB or smaller.','error');return;}const form=new FormData();form.append('file',file);try{await api(`/api/cases/${encodeURIComponent(currentCaseId)}/evidence`,{method:'POST',body:form});await loadCase(currentCaseId);switchCaseTab('evidence');await refreshCaseCountOnly();showToast('Evidence added to your case. Review the file details before sharing it.');}catch(err){showToast(err.message,'error');}}
async function addTimelineNote(event){event.preventDefault();const input=$('#timelineNoteText'),message=input.value.trim();if(message.length<3)return;try{await api(`/api/cases/${encodeURIComponent(currentCaseId)}/timeline`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});await loadCase(currentCaseId);switchCaseTab('activity');showToast('Personal note added to the local timeline.');}catch(err){showToast(err.message,'error');}}
async function recordCaseEvent(eventType,button){
  if(!currentCaseId)return;
  const details=$('#caseEventDetails')?.value?.trim()||'';
  const reference=$('#caseEventReference')?.value?.trim()||'';
  button.disabled=true;const original=button.textContent;button.textContent='Saving…';
  try{await api(`/api/cases/${encodeURIComponent(currentCaseId)}/events`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event_type:eventType,details,reference})});await loadCase(currentCaseId);await refreshCaseCountOnly();showToast('Update added to your timeline. It is marked as your report, not an organisation verification.');}
  catch(error){showToast(error.message||'Could not save this update.','error');button.disabled=false;button.textContent=original;}
}
async function connectCaseToWhatsApp(button){
  if((!whatsappCloudApiReady||!whatsappBusinessNumber)&&!whatsappTwilioSandboxConfigured){switchCaseTab('activity');showToast('Your case updates are available here. Add a note or record what changed since your last visit.');return;}
  button.disabled=true;const original=button.textContent;button.textContent='Preparing secure link…';
  try{const result=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/whatsapp-link`,{method:'POST'});const host=$('#caseWhatsAppLinkResult');if(host){host.hidden=false;host.innerHTML=`<div class="wa-link-code" data-provider="${escapeHtml(result.provider||'meta')}"><span>ONE-TIME LINK CODE · EXPIRES IN 10 MIN</span><b>${escapeHtml(result.code)}</b><p>${escapeHtml(result.setup_hint||('Send this code only to the official BolKeResolve number. If asked to opt in first, send START, then resend LINK '+result.code+' within 10 minutes.'))}</p><div><button type="button" class="button button-outline" data-action="copy-wa-link-code">Copy code</button><a class="button button-whatsapp" href="${escapeHtml(result.whatsapp_url)}" target="_blank" rel="noopener noreferrer">Open WhatsApp ↗</a></div></div>`;}showToast(result.provider==='twilio'?'Twilio Sandbox test link created. The code expires in 10 minutes.':'A one-time link code was created. The code expires in 10 minutes.');}
  catch(error){showToast(error.message||'Could not create a WhatsApp link.','error');}
  finally{button.disabled=false;button.textContent=original;}
}
function replyReviewMarkup(review,privacy={}){
  const urgent=review?.priority==='urgent';
  const redacted=privacy?.redacted_categories||[];
  return `<div class="case-reply-review-result-inner"><div class="case-reply-review-result-top"><span class="case-mini-kicker">FIRST-PASS INTERPRETATION</span><span class="case-reply-review-pill ${urgent?'is-urgent':''}">${urgent?'Safety concern':escapeHtml(review?.priority==='normal'?'Review needed':'Check carefully')}</span></div><h3>${escapeHtml(review?.label||'Needs your review')}</h3><p>${escapeHtml(review?.interpretation||'Read the original reply and decide what it means.')}</p><div class="case-reply-next-step"><b>A possible next step</b><p>${escapeHtml(review?.next_step||'Review the original and contact the organisation using its official channel.')}</p></div>${redacted.length?`<p class="case-reply-redaction-note">Sensitive patterns were redacted before analysis: ${redacted.map(escapeHtml).join(', ')}. Check your original text separately.</p>`:''}<div class="case-reply-review-limitations"><b>Before you save</b><ul>${(review?.limitations||[]).slice(0,3).map(item=>`<li>${escapeHtml(item)}</li>`).join('')}</ul></div><button type="button" class="button button-dark" data-action="confirm-reply-review">Save interpretation to timeline <span aria-hidden="true">↗</span></button><button type="button" class="button button-quiet" data-action="discard-reply-review">Discard review</button></div>`;
}
async function reviewSupportReply(event){
  event.preventDefault();
  const form=event.currentTarget,button=$('#reviewSupportReplyButton'),replyText=$('#caseReplyText')?.value?.trim()||'';
  if(!currentCaseId||replyText.length<8){showToast('Paste the relevant support wording first.','error');return;}
  if(button){button.disabled=true;button.textContent='Reviewing reply…';}
  const resultPanel=$('#caseReplyReviewResult');if(resultPanel){resultPanel.hidden=false;resultPanel.innerHTML='<div class="case-reply-review-loading"><span class="loading-orbit" aria-hidden="true"></span><p>Checking for common reply patterns. Nothing is saved yet.</p></div>';}
  reviewedReplyDraft=null;
  try{
    const result=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/reply-review/preview`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reply_text:replyText})});
    reviewedReplyDraft={replyText,review:result,reference:$('#caseReplyReference')?.value?.trim()||'',origin:'case-reply-review',referenceSelector:'#caseReplyReference',resultSelector:'#caseReplyReviewResult',textSelector:'#caseReplyText'};
    if(resultPanel)resultPanel.innerHTML=replyReviewMarkup(result,result.privacy||{});
  }catch(error){if(resultPanel){resultPanel.innerHTML=`<div class="case-reply-review-error"><b>Could not review this reply</b><p>${escapeHtml(error.message||'Try again, or record a short manual note instead.')}</p></div>`;}showToast(error.message||'Could not review the reply.','error');}
  finally{if(button){button.disabled=false;button.innerHTML='Review reply <span aria-hidden="true">↗</span>';}}
}
async function reviewManualInboxReply(event){
  event.preventDefault();
  const form=event.currentTarget,button=$('#caseInboxManualReplySubmit'),replyText=$('#caseInboxManualReplyText')?.value?.trim()||'';
  const panel=$('#caseInboxManualReplyResult');
  if(!currentCaseId||replyText.length<8){showToast('Paste at least eight characters from the relevant support reply.','error');return;}
  if(button){button.disabled=true;button.textContent='Reviewing email…';}
  if(panel){panel.hidden=false;panel.innerHTML='<div class="case-reply-review-loading"><span class="loading-orbit" aria-hidden="true"></span><p>Checking common reply patterns. The original text will not be saved by the preview.</p></div>';}
  reviewedReplyDraft=null;
  try{
    const result=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/reply-review/preview`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reply_text:replyText})});
    reviewedReplyDraft={replyText,review:result,reference:$('#caseInboxManualReplyReference')?.value?.trim()||'',origin:'case-inbox-manual',referenceSelector:'#caseInboxManualReplyReference',resultSelector:'#caseInboxManualReplyResult',textSelector:'#caseInboxManualReplyText'};
    if(panel)panel.innerHTML=replyReviewMarkup(result,result.privacy||{});
  }catch(error){if(panel)panel.innerHTML=`<div class="case-reply-review-error"><b>Could not review this email</b><p>${escapeHtml(error.message||'Try pasting the relevant wording instead.')}</p></div>`;showToast(error.message||'Could not review this email.','error');}
  finally{if(button){button.disabled=false;button.textContent='Review email reply ↗';}}
}
async function confirmReplyReview(button){
  if(!currentCaseId||!reviewedReplyDraft){showToast('Review the reply again before saving.','error');return;}
  button.disabled=true;button.textContent='Saving interpretation…';
  try{
    const draft=reviewedReplyDraft;
    const response=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/reply-review/confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reply_text:draft.replyText,reference:$(draft.referenceSelector||'#caseReplyReference')?.value?.trim()||draft.reference||'',confirmed:true})});
    const origin=draft.origin||'case-reply-review';
    reviewedReplyDraft=null;
    if(origin==='case-inbox-manual'){
      const text=$('#caseInboxManualReplyText');if(text)text.value='';
      const reference=$('#caseInboxManualReplyReference');if(reference)reference.value='';
      const panel=$('#caseInboxManualReplyResult');if(panel){panel.hidden=true;panel.innerHTML='';}
    }else{
      const text=$('#caseReplyText');if(text)text.value='';
      const panel=$('#caseReplyReviewResult');if(panel){panel.hidden=true;panel.innerHTML='';}
    }
    await loadCase(currentCaseId);await refreshCaseCountOnly();switchCaseTab('progress');const activity=$('#caseActivityDisclosure');if(activity)activity.open=true;showToast('A user-confirmed interpretation was added to your timeline. The pasted reply text was not retained by this action.');
  }catch(error){button.disabled=false;button.textContent='Save interpretation to timeline ↗';showToast(error.message||'Could not save the review.','error');}
}
async function answerSavedCaseFastPath(button){
  if(!currentCaseId||!activeCaseSnapshot){showToast('Open the case again before updating its guidance.','error');return;}
  const c=activeCaseSnapshot,field=button.dataset.field,value=button.dataset.value;
  const payload={
    issue_type:c.issue_type||'Other payment issue',
    merchant:c.merchant||'',
    amount:c.amount===null||c.amount===undefined||c.amount===''?null:Number(c.amount),
    payment_date:c.payment_date||'',
    language_code:c.language_code||'hi-IN',
    payment_status:c.payment_status||'unknown',
    contacted_support:c.contacted_support===null||c.contacted_support===undefined?null:Boolean(c.contacted_support),
    description:c.description||''
  };
  if(field==='payment_status'&&['failed','pending','successful'].includes(value))payload.payment_status=value;
  else if(field==='contacted_support'&&['yes','no'].includes(value))payload.contacted_support=value==='yes';
  else{showToast('That answer is not supported. Edit the case details instead.','error');return;}
  const original=button.textContent;
  button.disabled=true;button.textContent='Updating guidance…';
  try{
    await api(`/api/cases/${encodeURIComponent(currentCaseId)}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    await loadCase(currentCaseId);await refreshCaseCountOnly();
    showToast('Guidance updated using your answer. No bank, payment app or merchant records were checked.');
  }catch(error){
    showToast(error.message||'Could not update this case.','error');
    const current=$(`#caseDetailContent [data-action="answer-case-fastpath"][data-field="${field}"][data-value="${value}"]`);
    if(current){current.disabled=false;current.textContent=original;}
  }
}
let activeEvidenceReviewId='';
async function reviewEvidenceFile(button){
  const evidenceId=button.dataset.evidenceId||'';
  if(!currentCaseId||!evidenceId)return;
  const panel=$('#caseEvidenceReviewResults');
  if(!panel)return;
  panel.hidden=false;panel.innerHTML='<div class="case-evidence-review-loading">Reading the file locally… Raw document text will not be retained.</div>';
  button.disabled=true;const oldText=button.textContent;button.textContent='Checking…';
  try{
    const data=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/evidence/${encodeURIComponent(evidenceId)}/review`,{method:'POST'});
    activeEvidenceReviewId=data.review_id;
    const fields=Object.entries(data.fields||{});
    const fieldRows=fields.map(([key,item])=>{
      const mismatch=!!item.mismatch;
      const formatted=key==='amount'?money(item.value):String(item.value??'');
      const current=key==='amount'&&item.current_value!==null?money(item.current_value):String(item.current_value??'');
      return `<article class="case-evidence-fact-candidate ${mismatch?'is-mismatch':''}"><div class="case-evidence-fact-main"><span class="case-evidence-fact-label">${escapeHtml(item.label||key)}</span><strong>${escapeHtml(formatted)}</strong><small>${escapeHtml(item.source_excerpt||'Text was detected in this file')} · ${escapeHtml(item.confidence||'candidate')} confidence</small>${mismatch?`<p class="case-evidence-mismatch-note">Possible mismatch with the saved case: ${escapeHtml(current)}. Check the original file carefully.</p>`:''}${item.needs_confirmation?'<small>This candidate needs your confirmation (for example, a date may refer to a different event).</small>':''}</div><div class="case-evidence-fact-actions"><label><input type="checkbox" data-evidence-accept-field="${escapeHtml(key)}"> Record as document fact</label>${mismatch?`<label class="case-evidence-apply-label"><input type="checkbox" data-evidence-apply-field="${escapeHtml(key)}"> Also update the case to ${escapeHtml(formatted)}</label>`:''}</div></article>`;
    }).join('');
    const extractionConflicts=(data.extraction_conflicts||[]).map(c=>`<p class="case-evidence-mismatch-note">${escapeHtml(c.message||'More than one candidate value was found.')} ${escapeHtml((c.values||[]).join(', '))}</p>`).join('');
    panel.innerHTML=`<div class="case-evidence-review-head"><div><span class="case-mini-kicker">LOCAL DOCUMENT REVIEW</span><h3>Check the details we found</h3><p>${escapeHtml(data.evidence_name||'Uploaded file')} · ${escapeHtml(data.method||'document processing')}</p></div><button type="button" class="case-text-action" data-action="discard-evidence-review" data-review-id="${escapeHtml(data.review_id)}">Close</button></div><p class="case-evidence-review-notice">${escapeHtml(data.notice||'These are candidates from the uploaded file, not verified payment facts.')} Only select details you have checked against the original document.</p>${extractionConflicts}${fieldRows}<div class="case-evidence-review-footer"><button type="button" class="button button-dark" data-action="confirm-evidence-review" data-review-id="${escapeHtml(data.review_id)}">Save selected facts ↗</button><span>Case details change only when you also select an explicit “update the case” option.</span></div>`;
  }catch(error){panel.hidden=false;panel.innerHTML=`<div class="case-evidence-review-error"><b>Couldn’t read this file reliably</b><p>${escapeHtml(error.message||'You can still review the file manually.')}</p></div>`;}
  finally{button.disabled=false;button.textContent=oldText;}
}
async function confirmEvidenceReview(button){
  const panel=$('#caseEvidenceReviewResults');if(!panel)return;
  const reviewId=button.dataset.reviewId||activeEvidenceReviewId;
  const accepted=[...panel.querySelectorAll('[data-evidence-accept-field]:checked')].map(el=>el.dataset.evidenceAcceptField);
  const applied=[...panel.querySelectorAll('[data-evidence-apply-field]:checked')].map(el=>el.dataset.evidenceApplyField);
  const acceptedAll=[...new Set([...accepted,...applied])];
  if(!acceptedAll.length){showToast('Select at least one detail you checked against the original file.','error');return;}
  button.disabled=true;button.textContent='Saving reviewed facts…';
  try{
    const result=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/evidence-review/confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({review_id:reviewId,accepted_fields:acceptedAll,apply_fields:applied,confirmed:true})});
    activeEvidenceReviewId='';await loadCase(currentCaseId);switchCaseTab('prep');const disclosure=$('#caseEvidenceDisclosure');if(disclosure)disclosure.open=true;showToast(result.applied_fields?.length?`Saved ${result.accepted_fields.length} document facts and updated ${result.applied_fields.length} case field(s). Review the refreshed plan.`:`Saved ${result.accepted_fields.length} document fact(s). Your existing case details were not changed.`);
  }catch(error){button.disabled=false;button.textContent='Save selected facts ↗';showToast(error.message||'Could not save reviewed facts.','error');}
}
async function discardEvidenceReview(button){
  const reviewId=button.dataset.reviewId||activeEvidenceReviewId;
  if(!reviewId||!currentCaseId)return;
  try{await api(`/api/cases/${encodeURIComponent(currentCaseId)}/evidence-review/${encodeURIComponent(reviewId)}`,{method:'DELETE'});}catch(_){/* preview rows contain bounded structured candidates only */}
  activeEvidenceReviewId='';const panel=$('#caseEvidenceReviewResults');if(panel){panel.hidden=true;panel.innerHTML='';}showToast('Evidence review closed. No case facts were applied.');
}
function renderCaseInbox(data){
  const root=$('#caseInboxBridgeContent');if(!root)return;
  if(!data?.enabled){
    root.innerHTML=`<div class="case-inbox-unavailable"><b>Case Inbox Bridge automatic forwarding isn’t configured on this site yet.</b><p>Forwarding into a private address needs a receiving domain and an authenticated inbound-email provider. You can still use this case tool now: paste the relevant support email below, review the interpretation, and confirm only the short summary you want saved.</p></div>
      <form id="caseInboxManualReplyForm" class="case-inbox-manual-import"><label class="case-field-v2" for="caseInboxManualReplyText"><span>Paste the support email (subject and relevant message)</span><textarea id="caseInboxManualReplyText" minlength="8" maxlength="8000" rows="5" required placeholder="Subject: Refund update\n\nYour refund has been initiated. Please allow 5–7 business days."></textarea></label><label class="case-field-v2" for="caseInboxManualReplyReference"><span>Ticket / refund reference (optional)</span><input id="caseInboxManualReplyReference" maxlength="120" placeholder="Only add a reference you checked"></label><p class="case-inbox-manual-privacy">The text is sent to the server for a first-pass preview, but the raw reply is not saved to the case database. Common sensitive patterns are redacted; this is not a guarantee. Never include an OTP, PIN, password or full card number. The sender and statements are not independently verified.</p><button type="submit" class="button button-dark" id="caseInboxManualReplySubmit">Review email reply ↗</button></form><div id="caseInboxManualReplyResult" class="case-reply-review-result case-inbox-manual-result" hidden aria-live="polite" aria-atomic="true"></div>`;
    $('#caseInboxManualReplyForm')?.addEventListener('submit',reviewManualInboxReply);
    return;
  }
  const address=data.address||'';
  const messageHtml=(data.messages||[]).map(item=>`<article class="case-inbound-message" data-inbound-card="${escapeHtml(item.inbound_id)}"><div class="case-inbound-message-head"><div><span class="case-mini-kicker">FORWARDED EMAIL · REVIEW REQUIRED</span><h3>${escapeHtml(item.subject||'(No subject)')}</h3><p>Sender domain: ${escapeHtml(item.sender_domain||'not available')} · ${escapeHtml(prettyDate(item.received_at))}</p></div><span class="case-user-reported-tag">Not verified</span></div><p class="case-inbound-warning">${escapeHtml(item.notice||'Review before using this email.')} Do not follow links or instructions requesting OTPs, PINs, passwords, fees or remote-access apps.</p><pre class="case-inbound-email-body">${escapeHtml(item.body||'No readable text body. Check the original email.')}</pre>${(item.attachments||[]).length?`<div class="case-inbound-attachments"><b>Attachments (not imported)</b><ul>${item.attachments.map(a=>`<li>${escapeHtml(a.name)} · ${escapeHtml(a.content_type)} · ${escapeHtml(String(a.size_bytes||0))} bytes</li>`).join('')}</ul><small>Download an attachment from your email and upload it to this case after checking it.</small></div>`:''}<div class="case-inbound-message-actions"><button type="button" class="button button-dark" data-action="review-inbound-email" data-inbound-id="${escapeHtml(item.inbound_id)}">Interpret reply</button><button type="button" class="button button-quiet" data-action="discard-inbound-email" data-inbound-id="${escapeHtml(item.inbound_id)}">Discard</button></div><div class="case-inbound-review-result" data-inbound-review-result hidden></div></article>`).join('');
  root.innerHTML=`${address?`<div class="case-inbox-address-card"><div><span class="case-mini-kicker">THIS CASE’S PRIVATE FORWARDING ADDRESS</span><code>${escapeHtml(address)}</code><small>Forward only replies that relate to this case. Treat this address like a private link.</small></div><div class="case-inbox-address-actions"><button type="button" class="button button-dark" data-action="copy-case-inbox" data-inbox-address="${escapeHtml(address)}">Copy address</button><button type="button" class="button button-outline" data-action="rotate-case-inbox">Rotate address</button></div></div>`:`<p class="case-inbox-not-ready">The optional bridge is available. Create an address for this case to start forwarding relevant replies.</p><button type="button" class="button button-dark" data-action="create-case-inbox">Create case inbox</button>`}<div class="case-inbox-message-list"><div class="case-inbox-list-heading"><b>Replies waiting for review</b><span>${Number(data.pending_count||0)}</span><button type="button" class="case-text-action" data-action="refresh-case-inbox">Refresh</button></div>${messageHtml||'<div class="case-empty-inline"><b>No forwarded replies yet</b><p>Forward a support response to this case address. BolKeResolve won’t send messages on your behalf.</p></div>'}</div><p class="case-inbox-retention-note">Pending email text is encrypted at rest and retained for up to ${Number(data.retention_days||14)} days. Confirming or discarding clears the encrypted subject/body; provider copies and your own mailbox are unaffected.</p>`;
}
async function loadCaseInbox(createIfNeeded=false){
  const root=$('#caseInboxBridgeContent');if(!root||!currentCaseId)return;
  root.innerHTML='<p class="case-inbox-loading">Checking the optional inbox setup…</p>';
  try{
    let data=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/inbox`);
    if(data.enabled&&createIfNeeded&&!data.address){await api(`/api/cases/${encodeURIComponent(currentCaseId)}/inbox`,{method:'POST'});data=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/inbox`);}
    renderCaseInbox(data);
  }catch(error){root.innerHTML=`<div class="case-inbox-unavailable"><b>Couldn’t open this case inbox</b><p>${escapeHtml(error.message||'Try again later.')}</p><button type="button" class="button button-outline" data-action="open-case-inbox">Try again</button></div>`;}
}
async function previewInboundEmail(button){
  const inboundId=button.dataset.inboundId||'',card=button.closest('[data-inbound-card]');if(!currentCaseId||!inboundId||!card)return;
  button.disabled=true;button.textContent='Reviewing…';
  try{
    const data=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/inbox/messages/${encodeURIComponent(inboundId)}/preview`,{method:'POST'});
    const r=data.review||{},panel=card.querySelector('[data-inbound-review-result]');if(!panel)return;
    panel.hidden=false;panel.innerHTML=`<div class="case-inbound-interpretation"><span class="case-mini-kicker">FIRST-PASS INTERPRETATION</span><h4>${escapeHtml(r.label||'Needs manual review')}</h4><p>${escapeHtml(r.interpretation||'Please review this reply manually.')}</p><p><b>Possible next action:</b> ${escapeHtml(r.next_step||'Check the original message and decide what to do next.')}</p><small>${escapeHtml(data.notice||'Not independently verified.')}</small><label class="case-field-v2"><span>Ticket / refund reference (optional)</span><input type="text" maxlength="120" data-inbound-reference placeholder="Only save a reference you checked"></label><div class="case-inbound-review-buttons"><button type="button" class="button button-dark" data-action="confirm-inbound-email" data-inbound-id="${escapeHtml(inboundId)}">Confirm interpretation and clear email copy</button><button type="button" class="button button-quiet" data-action="discard-inbound-email" data-inbound-id="${escapeHtml(inboundId)}">Discard email</button></div></div>`;
  }catch(error){showToast(error.message||'Could not interpret this message.','error');}
  finally{button.disabled=false;button.textContent='Interpret reply';}
}
async function confirmInboundEmail(button){
  const inboundId=button.dataset.inboundId||'',card=button.closest('[data-inbound-card]');if(!currentCaseId||!inboundId||!card)return;
  button.disabled=true;button.textContent='Saving review…';
  try{
    await api(`/api/cases/${encodeURIComponent(currentCaseId)}/inbox/messages/${encodeURIComponent(inboundId)}/confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirmed:true,reference:card.querySelector('[data-inbound-reference]')?.value?.trim()||''})});
    await loadCase(currentCaseId);switchCaseTab('prep');const disclosure=$('#caseInboxBridgeDisclosure');if(disclosure)disclosure.open=true;await loadCaseInbox(false);showToast('Reply interpretation saved to the timeline. The encrypted email copy was cleared; the sender and claim remain unverified.');
  }catch(error){button.disabled=false;button.textContent='Confirm interpretation and clear email copy';showToast(error.message||'Could not save the interpretation.','error');}
}
async function discardInboundEmail(button){
  const inboundId=button.dataset.inboundId||'';if(!currentCaseId||!inboundId)return;
  if(!window.confirm('Discard this forwarded message and clear its encrypted contents? No case fact will change.'))return;
  button.disabled=true;try{await api(`/api/cases/${encodeURIComponent(currentCaseId)}/inbox/messages/${encodeURIComponent(inboundId)}`,{method:'DELETE'});await loadCaseInbox(false);showToast('Forwarded message discarded; its encrypted contents were cleared.');}catch(error){button.disabled=false;showToast(error.message||'Could not discard the message.','error');}
}
function renderCommitmentPreviewResult(data){
  const root=$('#commitmentPreviewResult');if(!root)return;
  root.hidden=false;
  if(!data?.candidate){
    root.innerHTML=`<div class="commitment-preview-warning"><b>We couldn't identify a commitment confidently.</b><p>${escapeHtml(data?.notice||'Please review the exact wording. We will not guess a promise.')}</p>${(data?.warnings||[]).map(w=>`<p>${escapeHtml(w)}</p>`).join('')}</div>`;
    return;
  }
  const c=data.candidate;
  const numericAmount=c.amount_minor_units==null?'':String(Number(c.amount_minor_units)/100);
  const warningHtml=(data.warnings||[]).map(w=>`<li>${escapeHtml(w)}</li>`).join('');
  const files=activeCaseSnapshot?.evidence||[];
  root.innerHTML=`<div class="commitment-preview-card"><div class="commitment-preview-heading"><div><span class="case-mini-kicker">REVIEW THE CANDIDATE</span><h3>Check every field before saving</h3></div><span class="case-user-reported-tag">Not verified</span></div>
    <label class="case-field-v2"><span>Source statement excerpt (redacted; editable)</span><textarea id="commitmentPreviewStatement" rows="4" maxlength="1200">${escapeHtml(c.statement_excerpt||'')}</textarea></label>
    <div class="commitment-date-grid"><label class="case-field-v2"><span>Statement type</span><select id="commitmentPreviewSpeechAct"><option value="conditional_process_commitment" ${c.speech_act==='conditional_process_commitment'?'selected':''}>Conditional commitment</option><option value="process_commitment" ${c.speech_act==='process_commitment'?'selected':''}>Process commitment</option><option value="estimated_timeline" ${c.speech_act==='estimated_timeline'?'selected':''}>Estimate / expected time</option><option value="request_or_process_step" ${c.speech_act==='request_or_process_step'?'selected':''}>Request / process step</option><option value="unclassified_statement" ${c.speech_act==='unclassified_statement'?'selected':''}>Unclassified (use caution)</option></select></label>
    <label class="case-field-v2"><span>Source label</span><input id="commitmentPreviewSourceLabel" maxlength="120" value="${escapeHtml(({support_call_transcript:'User-reviewed support-call transcript',support_email:'User-reviewed support email excerpt',chat_message:'User-reviewed chat message excerpt',user_note:'User-entered statement note',case_evidence:'Statement linked to case evidence'})[$('#commitmentSourceType')?.value||'support_call_transcript'])}" /></label></div>
    <label class="case-field-v2"><span>What action did they say they would take?</span><input id="commitmentPreviewAction" data-action-code="${escapeHtml(c.action_code||'user_reviewed_action')}" maxlength="200" value="${escapeHtml(c.action_text||'')}" /></label>
    <div class="commitment-date-grid"><label class="case-field-v2"><span>Amount (₹, optional)</span><input id="commitmentPreviewAmount" type="number" min="0" step="0.01" value="${escapeHtml(numericAmount)}" placeholder="Not stated" /></label><label class="case-field-v2"><span>Statement date (required if its date starts the clock)</span><input id="commitmentPreviewStatementDate" type="date" value="${escapeHtml(c.statement_date||'')}" /></label></div>
    <label class="case-field-v2"><span>What must happen first? (leave blank if none / unknown)</span><textarea id="commitmentPreviewCondition" rows="2" maxlength="300" placeholder="e.g. return is scanned at the warehouse">${escapeHtml(c.condition_text||'')}</textarea></label>
    <div class="commitment-date-grid"><label class="case-field-v2"><span>What starts the clock?</span><select id="commitmentPreviewTrigger"><option value="condition_met" ${c.trigger_type==='condition_met'?'selected':''}>When the condition occurs</option><option value="statement_date" ${c.trigger_type==='statement_date'?'selected':''}>From the statement date</option><option value="unspecified" ${c.trigger_type==='unspecified'?'selected':''}>Not clear yet</option></select></label><label class="case-field-v2"><span>Qualifier / uncertainty</span><input id="commitmentPreviewQualifier" maxlength="50" value="${escapeHtml(c.qualifier||'stated_by_speaker')}" placeholder="e.g. may, usually, within" /></label></div>
    <div class="commitment-date-grid"><label class="case-field-v2"><span>Duration minimum</span><input id="commitmentPreviewDuration" type="number" min="0" max="3650" step="1" value="${c.duration_value==null?'':escapeHtml(c.duration_value)}" placeholder="Not stated" /></label><label class="case-field-v2"><span>Duration maximum (optional)</span><input id="commitmentPreviewDurationMax" type="number" min="0" max="3650" step="1" value="${c.duration_max_value==null?'':escapeHtml(c.duration_max_value)}" placeholder="Same as minimum" /></label></div>
    <div class="commitment-date-grid"><label class="case-field-v2"><span>Duration unit</span><select id="commitmentPreviewUnit"><option value="" ${!c.duration_unit?'selected':''}>Not stated</option><option value="day" ${c.duration_unit==='day'?'selected':''}>Days</option><option value="week" ${c.duration_unit==='week'?'selected':''}>Weeks</option><option value="hour" ${c.duration_unit==='hour'?'selected':''}>Hours</option></select></label><label class="case-field-v2"><span>Day type</span><select id="commitmentPreviewDayType"><option value="unspecified" ${c.day_type==='unspecified'?'selected':''}>Not stated</option><option value="business_day" ${c.day_type==='business_day'?'selected':''}>Business / working days</option><option value="calendar_day" ${c.day_type==='calendar_day'?'selected':''}>Calendar days</option></select></label></div>
    <label class="case-field-v2"><span>Link an existing case file (optional)</span><select id="commitmentPreviewEvidence">${commitmentEvidenceOptions(files)}</select></label>
    ${warningHtml?`<div class="commitment-preview-warning"><b>Check these limitations</b><ul>${warningHtml}</ul></div>`:''}
    <label class="commitment-confirm-check"><input id="commitmentConfirmChecked" type="checkbox"><span>I checked the statement and fields above. Save this as a user-confirmed interpretation, not verified company status.</span></label>
    <button type="button" class="button button-dark" data-action="confirm-commitment">Save reviewed commitment</button>
    <p class="case-privacy-caption">No recording is saved. Only the short excerpt above and fields you confirm are retained. You can remove this commitment later.</p>
  </div>`;
}
async function previewCommitment(button){
  const text=$('#commitmentSourceText')?.value?.trim()||'';
  if(text.length<8){showToast('Paste or transcribe the exact support statement first.','error');$('#commitmentSourceText')?.focus();return;}
  button.disabled=true;button.textContent='Checking statement…';
  const root=$('#commitmentPreviewResult');if(root){root.hidden=false;root.innerHTML='<p>Checking for a possible commitment…</p>';}
  try{
    const sourceType=$('#commitmentSourceType')?.value||'support_call_transcript';
    const result=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/commitments/preview`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,source_type:sourceType})});
    renderCommitmentPreviewResult(result);
  }catch(error){if(root){root.hidden=false;root.innerHTML=`<div class="commitment-preview-warning">${escapeHtml(error.message||'Could not preview this statement.')}</div>`;}}
  finally{button.disabled=false;button.textContent='Find a possible commitment';}
}
async function transcribeCommitmentAudio(button){
  const file=$('#commitmentAudioFile')?.files?.[0];
  if(!file){showToast('Choose an audio clip first.','error');return;}
  const suffix=(file.name.split('.').pop()||'').toLowerCase();
  if(!['wav','mp3','ogg','flac','aac','m4a'].includes(suffix)){showToast('Use WAV, MP3, OGG, FLAC, AAC or M4A audio.','error');return;}
  if(file.size>12*1024*1024){showToast('Audio must be 12 MB or smaller.','error');return;}
  if(!window.confirm('This audio will be sent to the configured Gnani speech service for transcription. BolKeResolve will not save the audio file. Do you have permission to use this recording?'))return;
  button.disabled=true;button.textContent='Sending for transcription…';
  try{
    const form=new FormData();form.append('audio_file',file);form.append('language_code','auto');
    const result=await api('/api/voice/transcribe',{method:'POST',body:form});
    $('#commitmentSourceText').value=result.transcript||'';
    $('#commitmentSourceType').value='support_call_transcript';
    $('#commitmentPreviewResult').hidden=true;$('#commitmentPreviewResult').innerHTML='';
    showToast('Transcript loaded. Review and correct the wording, then find a possible commitment.');
  }catch(error){showToast(error.message||'Could not transcribe this recording.','error');}
  finally{button.disabled=false;button.textContent='Transcribe selected recording';}
}
async function confirmCommitment(button){
  if(!currentCaseId)return;
  if(!$('#commitmentConfirmChecked')?.checked){showToast('Confirm that you reviewed the statement and extracted fields.','error');return;}
  const rawAmount=$('#commitmentPreviewAmount')?.value?.trim()||'';
  const amountMinor=rawAmount===''?null:Math.round(Number(rawAmount)*100);
  if(rawAmount!==''&&(!Number.isFinite(Number(rawAmount))||Number(rawAmount)<0)){showToast('Enter a valid non-negative amount, or leave it blank.','error');return;}
  const maybeNumber=id=>{const v=$(id)?.value?.trim()||'';return v===''?null:Number(v);};
  const payload={confirmed:true,source_type:$('#commitmentSourceType')?.value||'support_call_transcript',source_label:$('#commitmentPreviewSourceLabel')?.value?.trim()||'',source_excerpt:$('#commitmentPreviewStatement')?.value?.trim()||'',source_evidence_id:$('#commitmentPreviewEvidence')?.value||'',speech_act:$('#commitmentPreviewSpeechAct')?.value||'unclassified_statement',action_code:$('#commitmentPreviewAction')?.dataset.actionCode||'user_reviewed_action',action_text:$('#commitmentPreviewAction')?.value?.trim()||'',amount_minor_units:amountMinor,currency:'INR',condition_text:$('#commitmentPreviewCondition')?.value?.trim()||'',trigger_type:$('#commitmentPreviewTrigger')?.value||'unspecified',duration_value:maybeNumber('#commitmentPreviewDuration'),duration_max_value:maybeNumber('#commitmentPreviewDurationMax'),duration_unit:$('#commitmentPreviewUnit')?.value||'',day_type:$('#commitmentPreviewDayType')?.value||'unspecified',qualifier:$('#commitmentPreviewQualifier')?.value?.trim()||'stated_by_speaker',statement_date:$('#commitmentPreviewStatementDate')?.value||''};
  button.disabled=true;button.textContent='Saving reviewed record…';
  try{
    await api(`/api/cases/${encodeURIComponent(currentCaseId)}/commitments/confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    await loadCase(currentCaseId);switchCaseTab('prep');const disclosure=$('#caseCommitmentsDisclosure');if(disclosure)disclosure.open=true;
    showToast('Reviewed commitment saved. Its source and claims are still marked unverified.');
  }catch(error){button.disabled=false;button.textContent='Save reviewed commitment';showToast(error.message||'Could not save this commitment.','error');}
}
async function reconcileCommitment(button){
  const id=button.dataset.commitmentId||'';const form=button.closest('[data-commitment-update-form]');if(!id||!form)return;
  const text=form.querySelector('[data-commitment-event-text]')?.value?.trim()||'';
  if(text.length<3){showToast('Add the relevant new statement or a short note.','error');return;}
  const payload={event_text:text,relation:form.querySelector('[data-commitment-relation]')?.value||'unknown',evidence_status:'user_confirmed',evidence_id:form.querySelector('[data-commitment-evidence]')?.value||'',event_date_claimed:form.querySelector('[data-commitment-date-claimed]')?.value||'',event_date_confirmed:form.querySelector('[data-commitment-date-confirmed]')?.value||'',details:''};
  if(payload.relation==='triggers'&&!payload.event_date_confirmed&&!window.confirm('You have not entered an occurrence date. The condition can be recorded as reported, but the deadline clock will remain unstarted. Continue?'))return;
  button.disabled=true;button.textContent='Recording update…';
  try{
    await api(`/api/cases/${encodeURIComponent(currentCaseId)}/commitments/${encodeURIComponent(id)}/reconcile`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    await loadCase(currentCaseId);switchCaseTab('prep');const disclosure=$('#caseCommitmentsDisclosure');if(disclosure)disclosure.open=true;showToast('Update added to the commitment history. Earlier statements were preserved.');
  }catch(error){button.disabled=false;button.textContent='Record reviewed update';showToast(error.message||'Could not record this update.','error');}
}
async function deleteCommitment(button){
  const id=button.dataset.commitmentId||'';if(!id||!currentCaseId)return;
  if(!window.confirm('Remove this commitment and its linked update history from the active case record? This will not delete the underlying uploaded evidence file.'))return;
  button.disabled=true;try{await api(`/api/cases/${encodeURIComponent(currentCaseId)}/commitments/${encodeURIComponent(id)}`,{method:'DELETE'});await loadCase(currentCaseId);switchCaseTab('prep');const disclosure=$('#caseCommitmentsDisclosure');if(disclosure)disclosure.open=true;showToast('Commitment and its linked history were removed from the active case record.');}catch(error){button.disabled=false;showToast(error.message||'Could not remove the commitment.','error');}
}

async function detailActionHandler(event){const retryShared=event.target.closest('[data-action="retry-shared-intake"]');if(retryShared){await retryPendingSharedIntake(retryShared);return;}const fastPathAnswer=event.target.closest('[data-action="answer-case-fastpath"]');if(fastPathAnswer){await answerSavedCaseFastPath(fastPathAnswer);return;}const confirmReply=event.target.closest('[data-action="confirm-reply-review"]');if(confirmReply){await confirmReplyReview(confirmReply);return;}const discardReply=event.target.closest('[data-action="discard-reply-review"]');if(discardReply){const origin=reviewedReplyDraft?.origin||'case-reply-review';reviewedReplyDraft=null;const result=origin==='case-inbox-manual'?$('#caseInboxManualReplyResult'):$('#caseReplyReviewResult');if(result){result.hidden=true;result.innerHTML='';}const text=origin==='case-inbox-manual'?$('#caseInboxManualReplyText'):$('#caseReplyText');if(text)text.value='';if(origin==='case-inbox-manual'){const reference=$('#caseInboxManualReplyReference');if(reference)reference.value='';}showToast('Reply review discarded. No interpretation was saved.');return;}const activityFilter=event.target.closest('[data-activity-filter]');if(activityFilter){const root=$('#caseDetailContent');const kind=activityFilter.dataset.activityFilter;root?.querySelectorAll('[data-activity-filter]').forEach(button=>{const selected=button===activityFilter;button.classList.toggle('active',selected);button.setAttribute('aria-pressed',String(selected));});root?.querySelectorAll('[data-activity-item]').forEach(item=>{item.hidden=kind!=='all'&&item.dataset.activityKind!==kind;});const empty=root?.querySelector('.case-activity-filter-empty');const items=[...(root?.querySelectorAll('[data-activity-item]')||[])];const shown=items.some(item=>!item.hidden);if(empty)empty.hidden=kind==='all'||shown||items.length===0;return;}const copyWaCode=event.target.closest('[data-action="copy-wa-link-code"]');if(copyWaCode){const code=$('.wa-link-code b')?.textContent||'';if(code){await navigator.clipboard.writeText(`LINK ${code}`);const provider=$('.wa-link-code')?.dataset.provider;showToast(provider==='twilio'?'Link command copied. Send it to the Twilio Sandbox only after your phone has joined that Sandbox.':'Link command copied. Send it only to the official BolKeResolve WhatsApp account.');}return;}const tabButton=event.target.closest('[data-case-tab]');if(tabButton){switchCaseTab(tabButton.dataset.caseTab);return;}const eventButton=event.target.closest('[data-case-event]');if(eventButton){await recordCaseEvent(eventButton.dataset.caseEvent,eventButton);return;}const button=event.target.closest('[data-action]');if(!button)return;const action=button.dataset.action;try{if(action==='preview-commitment'){await previewCommitment(button);return;}else if(action==='transcribe-commitment-audio'){await transcribeCommitmentAudio(button);return;}else if(action==='confirm-commitment'){await confirmCommitment(button);return;}else if(action==='reconcile-commitment'){await reconcileCommitment(button);return;}else if(action==='delete-commitment'){await deleteCommitment(button);return;}else if(action==='review-evidence'){await reviewEvidenceFile(button);return;}else if(action==='confirm-evidence-review'){await confirmEvidenceReview(button);return;}else if(action==='discard-evidence-review'){await discardEvidenceReview(button);return;}else if(action==='open-case-inbox'){await loadCaseInbox(true);return;}else if(action==='create-case-inbox'){await loadCaseInbox(true);return;}else if(action==='refresh-case-inbox'){await loadCaseInbox(false);return;}else if(action==='copy-case-inbox'){const address=button.dataset.inboxAddress||'';if(address){await navigator.clipboard.writeText(address);showToast('Case forwarding address copied. Keep it private and forward only relevant replies.');}return;}else if(action==='rotate-case-inbox'){if(!window.confirm('Rotate this case inbox address? The old address will stop working.'))return;const result=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/inbox/rotate`,{method:'POST'});await loadCaseInbox(false);showToast('Case inbox address rotated. Update any forwarding rule.');return;}else if(action==='review-inbound-email'){await previewInboundEmail(button);return;}else if(action==='confirm-inbound-email'){await confirmInboundEmail(button);return;}else if(action==='discard-inbound-email'){await discardInboundEmail(button);return;}else if(action==='connect-whatsapp'){await connectCaseToWhatsApp(button);return;}else if(action==='open-evidence'){switchCaseTab('prep');const disclosure=$('#caseEvidenceDisclosure');if(disclosure){disclosure.open=true;disclosure.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});}return;}else if(action==='open-edit-details'){const editor=$('.case-edit-disclosure');if(editor){editor.open=true;editor.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});editor.querySelector('select')?.focus({preventScroll:true});}return;}else if(action==='resume-live'){await startLiveRoom(currentCaseId);return;}else if(action==='refresh-guidance'){button.disabled=true;button.textContent='Refreshing…';await api(`/api/cases/${encodeURIComponent(currentCaseId)}/refresh-guidance`,{method:'POST'});await loadCase(currentCaseId);await refreshCaseCountOnly();showToast('Your story was re-checked and the guidance plan refreshed. No payment records were accessed.');return;}else if(action==='delete-case'){const approved=window.confirm('Delete this case and all its evidence files from this device? This cannot be undone.');if(!approved)return;button.disabled=true;button.textContent='Deleting…';const deletedId=currentCaseId;await api(`/api/cases/${encodeURIComponent(deletedId)}`,{method:'DELETE'});currentCaseId=null;showView('cases');showToast(`Case ${deletedId} and its stored evidence were deleted.`);}else if(action==='update-progress'){const case_stage=$('#caseProgressSelect')?.value,note=$('#caseProgressNote')?.value?.trim()||'';if(!case_stage)return;button.disabled=true;button.textContent='Saving…';await api(`/api/cases/${encodeURIComponent(currentCaseId)}/progress`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({case_stage,note})});await loadCase(currentCaseId);await refreshCaseCountOnly();showToast('Progress saved to this device. It reflects your report, not an external verification.');}else if(action==='draft-en'||action==='draft-hi'||action==='draft-hinglish'){button.disabled=true;button.textContent='Preparing…';await api(`/api/cases/${encodeURIComponent(currentCaseId)}/draft`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({language:action==='draft-hi'?'hi':action==='draft-hinglish'?'hinglish':'en'})});await loadCase(currentCaseId);switchCaseTab('draft');showToast('Support request prepared. Review it before sharing.');}else if(action==='save-draft'){const text=$('#draftOutput')?.value?.trim()||'';if(!text){showToast('Add a message before saving it.','error');return;}button.disabled=true;button.textContent='Saving…';await api(`/api/cases/${encodeURIComponent(currentCaseId)}/draft`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});await loadCase(currentCaseId);switchCaseTab('draft');showToast('Your message edits were saved. Nothing was sent.');}else if(action==='copy-draft'){const output=$('#draftOutput'),text=output?(('value' in output)?output.value:output.textContent):'';if(!text)return;await navigator.clipboard.writeText(text);showToast('Draft copied. Review it before sending through the company’s official support channel.');}else if(action==='share-whatsapp-draft'){const output=$('#draftOutput'),text=output?.value?.trim()||'';if(!text){showToast('Prepare a support message first.','error');return;}const url=`https://wa.me/?text=${encodeURIComponent(text)}`;window.open(url,'_blank','noopener,noreferrer');showToast('WhatsApp opened with a draft. Choose the recipient and review it before sending. BolKeResolve will not track delivery.');}else if(action==='share-email-draft'){const output=$('#draftOutput'),text=output?.value?.trim()||'';if(!text){showToast('Prepare a support message first.','error');return;}const subject=`Support request: ${$('#caseDetailContent h1')?.textContent||'consumer issue'} · ${currentCaseId}`;window.location.href=`mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(text)}`;showToast('Your email app may open with a draft. Select the recipient and review it before sending.');}else if(action==='download-passport-json'){const response=await fetch(`/api/cases/${encodeURIComponent(currentCaseId)}/passport.json`,{credentials:'same-origin'});if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail||`Request failed (${response.status}).`);}const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`BolKeResolve-${currentCaseId}-passport.json`;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);showToast('Portable JSON passport downloaded. Review it before sharing.');}else if(action==='print-passport'){const link=document.createElement('a');link.href=`/api/cases/${encodeURIComponent(currentCaseId)}/passport/print`;link.target='_blank';link.rel='noopener noreferrer';document.body.appendChild(link);link.click();link.remove();showToast('Print view opened. Choose Print or Save as PDF from that page.');}else if(action==='download-case-bundle'){const response=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/evidence-bundle.zip`);const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`BolKeResolve-${currentCaseId}-complete-case.zip`;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);showToast('Complete case archive downloaded. Review the files before sharing.');}else if(action==='copy-pack'){const pack=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/action-pack`);await navigator.clipboard.writeText(pack.export_text||'');showToast('Case pack copied to clipboard. Review it before sharing.');}else if(action==='download-pack'){const pack=await api(`/api/cases/${encodeURIComponent(currentCaseId)}/action-pack`);const blob=new Blob([pack.export_text||''],{type:'text/plain;charset=utf-8'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`BolKeResolve-${currentCaseId}-action-pack.txt`;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);showToast('Case pack downloaded. Review it before sharing.');}else if(action==='speak-draft'){const output=$('#draftOutput'),text=output?(('value' in output)?output.value:output.textContent):'';if(!text)return;button.disabled=true;button.textContent='Preparing audio…';const lang=text.includes('विषय:')?'hi-IN':(/\b(Namaste|Dhanyavaad|Mujhe|Mere|batayein|ke baare mein)\b/i.test(text)?'hi-en':'en-IN');const response=await api('/api/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,language_code:lang})});const audioBlob=await response.blob(),url=URL.createObjectURL(audioBlob),audio=new Audio(url);audio.addEventListener('ended',()=>URL.revokeObjectURL(url),{once:true});await audio.play();button.disabled=false;button.textContent='Read message aloud';}}catch(err){showToast(err.message,'error');const current=$(`#caseDetailContent [data-action="${action}"]`);if(current){current.disabled=false;current.textContent=action==='delete-case'?'Delete case':action==='refresh-guidance'?'Refresh plan ↻':action==='update-progress'?'Save progress ↗':action==='draft-en'?'Prepare English draft ↗':action==='draft-hi'?'हिन्दी में तैयार करें':action==='draft-hinglish'?'Prepare in Hinglish':action==='copy-draft'?'Copy message':action==='speak-draft'?'Read aloud':'Try again';}}}
async function refreshCaseCountOnly(){try{cachedCases=await api('/api/cases');$('#navCaseCount').textContent=cachedCases.length;}catch(_){}}


// Guided chat intake: text and multi-language voice share one story and the same case engine.
let waSelectedIssue = '';
let waDescriptionParts = [];
let waChatSaved = false;
let waLatestExtractedFacts = null;
let waGuidanceSequence = 0;
let waGuidancePending = null;
let waGuidedVoiceEnabled = false;
let waVoiceStream = null, waVoiceContext = null, waVoiceSource = null, waVoiceProcessor = null, waVoiceGain = null;
let waVoiceBuffers = [], waVoiceSampleRate = 16000, waVoiceStartedAt = 0, waVoiceTimer = null, waVoiceRecording = false;
function waTime(){return new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});}
function waAddMessage(text, role='user', extra=''){
  const thread=$('#waThread'); if(!thread)return null;
  const item=document.createElement('div'); item.className=`wa-message ${role==='user'?'user-message':'bot-message'}`;
  const p=document.createElement('p'); p.textContent=text; item.appendChild(p);
  const tm=document.createElement('time'); tm.textContent=waTime(); if(role==='user'){const marks=document.createElement('span');marks.textContent=' ✓✓';tm.appendChild(marks);} item.appendChild(tm);
  if(role!=='user'){
    const listen=document.createElement('button');listen.type='button';listen.className='wa-read-message';listen.dataset.waSpeak='1';listen.textContent='Listen';listen.setAttribute('aria-label','Read this message aloud');item.appendChild(listen);
  }
  if(extra)item.insertAdjacentHTML('beforeend',extra);
  thread.appendChild(item); thread.scrollTop=thread.scrollHeight; return item;
}
function waSetQuickReplies(visible){const q=$('#waQuickReplies');if(q)q.hidden=!visible;}
function waRefreshSaveArea(){
  const area=$('#waSaveArea'); if(!area)return;
  const words=waDescriptionParts.join(' ').trim().split(/\s+/).filter(Boolean).length;
  const ok=waDescriptionParts.join(' ').trim().length>=8;
  area.hidden=!ok||waChatSaved;
  $('#waSummaryCount').textContent=`${words} word${words===1?'':'s'} in your story`;
}
function waGuessIssue(text){
  const t=text.toLowerCase();
  if(/refund|money back|paise wapas|paisa wapas|रिफंड|पैसे वापस|पैसा वापस|वापस नहीं आया/.test(t))return 'Refund not received';
  if(/duplicate|charged twice|double charge|do baar|twice|दो बार पैसे|दो बार चार्ज|डबल चार्ज|दुबारा कट/.test(t))return 'Duplicate charge';
  if(/wrong amount|incorrect amount|extra charge|charged extra|zyada paise|गलत राशि|गलत अमाउंट|ज्यादा पैसे|अधिक राशि/.test(t))return 'Incorrect amount';
  if(/order not received|not delivered|delivery not|nahi mila|nahi aaya|ऑर्डर नहीं मिला|डिलीवरी नहीं हुई|सामान नहीं आया|पार्सल नहीं आया/.test(t))return 'Order paid but not received';
  if(/unauthori[sz]ed|don't recognise|do not recognise|not my transaction|fraud|scam|अनधिकृत|मैंने नहीं किया|धोखाधड़ी|फ्रॉड/.test(t))return 'Suspected fraud or unauthorised transaction';
  const pendingWord=/pending|processing|not credited|recipient.*not|not.*received|नहीं मिला|नहीं मिले|नहीं पहुँचे|नहीं पहुंचे|प्राप्त नहीं|पेंडिंग|लंबित/.test(t);
  const paymentWord=/upi|transaction|payment|debited|deduct|kat gaye|kat gaya|यूपीआई|लेन.?देन|भुगतान|पैसे कट|पैसा कट|खाते से कट/.test(t);
  if(pendingWord&&paymentWord)return 'UPI payment pending / recipient not credited';
  if(/failed|failure|payment fail|upi fail|declined|असफल|पेमेंट फेल|भुगतान फेल|लेन.?देन असफल/.test(t))return 'Failed UPI payment';
  return 'Other payment issue';
}
function detectLanguageCode(text){
  if(/[\u0980-\u09FF]/.test(text))return 'bn-IN';
  if(/[\u0A00-\u0A7F]/.test(text))return 'pa-IN';
  if(/[\u0A80-\u0AFF]/.test(text))return 'gu-IN';
  if(/[\u0B80-\u0BFF]/.test(text))return 'ta-IN';
  if(/[\u0C00-\u0C7F]/.test(text))return 'te-IN';
  if(/[\u0C80-\u0CFF]/.test(text))return 'kn-IN';
  if(/[\u0D00-\u0D7F]/.test(text))return 'ml-IN';
  if(/[\u0900-\u097F]/.test(text))return /[ळऱॲ]|माझे|मला|आहे|झाले|काय/.test(text)?'mr-IN':'hi-IN';
  if(/\b(maine|mera|meri|mere|mujhe|paise|paisa|kya|nahi|nahin|hai|tha|hoga|kat gaye|kat gaya|bheja|bheji|aaya|aayi|gaya|gayi|mila|mili|batao|batayein)\b/i.test(text))return 'hi-IN';
  if(/[a-z]/i.test(text))return 'en-IN';
  return 'hi-IN';
}
function waSelectedLanguage(){return $('#waLanguageCode')?.value||'auto';}
function waSpeechLocale(text=''){
  const selected=waSelectedLanguage();
  return selected==='auto'?detectLanguageCode(text):(selected==='hi-IN'?'hi-IN':selected);
}
function waSpeak(text){
  if(!('speechSynthesis' in window)||typeof SpeechSynthesisUtterance==='undefined'){
    showToast('Read-aloud is not available in this browser. You can still read or copy the message.','error');return;
  }
  const utterance=new SpeechSynthesisUtterance(String(text||'').slice(0,2200));
  utterance.lang=waSpeechLocale(text);
  utterance.rate=0.94;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}
function waAppendElement(parent, tag, className, text){const el=document.createElement(tag);if(className)el.className=className;if(text!==undefined)el.textContent=text;parent.appendChild(el);return el;}
function waSafeExternalLink(label,url){
  try{const parsed=new URL(String(url||''));if(parsed.protocol!=='https:')return null;const a=document.createElement('a');a.className='wa-official-link';a.href=parsed.href;a.target='_blank';a.rel='noopener noreferrer';a.textContent=label;return a;}catch(_){return null;}
}
function waRemoveOldGuidance(){
  $$('.wa-guidance-message').forEach(el=>el.remove());
  waGuidancePending=null;
}
function waBuildGuidanceMessage(item,result,story){
  item.classList.remove('is-loading');item.replaceChildren();
  const time=document.createElement('time');time.textContent=waTime();
  const card=waAppendElement(item,'div','wa-recommendation-card');
  const top=waAppendElement(card,'div','wa-recommendation-top');
  waAppendElement(top,'span','wa-recommendation-kicker','YOUR NEXT MOVE');
  const confidence=result?.classification?.confidence||'medium';
  waAppendElement(top,'span','wa-confidence-chip',`${confidence.charAt(0).toUpperCase()+confidence.slice(1)} confidence`);
  const issue=waAppendElement(card,'p','wa-guidance-issue',`Suggested issue · ${result?.classification?.issue_type||waSelectedIssue||'Payment or consumer issue'}`);
  const steps=Array.isArray(result?.recommended_steps)?result.recommended_steps:[];
  const first=steps[0]||{};
  const urgent=result?.urgency?.level==='urgent';
  const move=waAppendElement(card,'section',`wa-guidance-first-move${urgent?' is-urgent':''}`);
  waAppendElement(move,'span','wa-guidance-kicker',urgent?'SAFETY FIRST':'START HERE');
  waAppendElement(move,'h3','',first.title||'Review the relevant support route');
  waAppendElement(move,'p','',first.detail||'Check the official source below and confirm the details before taking action.');
  if(first.why)waAppendElement(move,'small','',first.why);
  if(urgent){waAppendElement(move,'p','wa-urgent-note','If money may have been taken without your permission, contact your bank/payment provider immediately. Do not wait for this case flow to finish.');}
  const destinations=Array.isArray(result?.support_destinations)?result.support_destinations:[];
  if(destinations.length){
    const links=waAppendElement(card,'div','wa-guidance-links');
    waAppendElement(links,'p','wa-guidance-section-label','OFFICIAL SUPPORT FOR YOUR PLATFORM');
    destinations.slice(0,2).forEach(destination=>{
      const destCard=waAppendElement(links,'div','wa-support-destination');
      waAppendElement(destCard,'b','',destination.name||'Official support');
      waAppendElement(destCard,'p','',destination.action||'Open the official support channel and follow its instructions.');
      const link=waSafeExternalLink(`${destination.label||'Open official support'} ↗`,destination.url);
      if(link)destCard.appendChild(link);
      if(destination.note)waAppendElement(destCard,'small','',destination.note);
    });
  }
  const sources=Array.isArray(result?.official_sources)?result.official_sources:[];
  if(sources.length){
    const sourceBox=waAppendElement(card,'details','wa-guidance-source-details');
    waAppendElement(sourceBox,'summary','','Official guidance and sources');
    sources.slice(0,3).forEach(source=>{
      const row=waAppendElement(sourceBox,'div','wa-source-row');
      const link=waSafeExternalLink(source.title||source.organization||'Official source',source.url);
      if(link)row.appendChild(link);else waAppendElement(row,'span','',source.title||'Official source');
      if(source.summary)waAppendElement(row,'small','',source.summary);
    });
  }
  const draft=result?.suggested_support_draft;
  if(draft?.message){
    const details=waAppendElement(card,'details','wa-chat-draft');
    waAppendElement(details,'summary','','Ready-to-edit support message');
    waAppendElement(details,'p','wa-chat-draft-note',draft.notice||'Draft only. Nothing has been sent.');
    const textArea=waAppendElement(details,'textarea','wa-chat-draft-text',draft.message);
    textArea.rows=7;textArea.maxLength=5000;textArea.setAttribute('aria-label','Editable draft for the organisation support team');
    const copy=waAppendElement(details,'button','wa-copy-message','Copy message');copy.type='button';copy.dataset.waCopyDraft='1';
  }
  if(steps.length>1){
    const details=waAppendElement(card,'details','wa-guidance-more');
    waAppendElement(details,'summary','','See the next steps');
    steps.slice(1,4).forEach((step,index)=>{
      const row=waAppendElement(details,'div','wa-guidance-step');
      waAppendElement(row,'span','wa-guidance-step-num',String(index+2).padStart(2,'0'));
      const copy=waAppendElement(row,'div','');waAppendElement(copy,'b','',step.title||`Step ${index+2}`);waAppendElement(copy,'p','',step.detail||'Follow the official instructions for this step.');
    });
  }
  const caveat=waAppendElement(card,'p','wa-guidance-caveat','Guidance is based on what you told us. No bank, merchant or government record has been checked, and no complaint has been submitted.');
  const speak=waAppendElement(card,'button','wa-read-message wa-read-guidance','Listen to this next step');speak.type='button';speak.dataset.waSpeakGuidance='1';speak.setAttribute('aria-label','Read the first suggested step aloud');
  item.appendChild(time);
  item.dataset.guidanceStoryLength=String(story.length);
  $('#waThread').scrollTop=$('#waThread').scrollHeight;
}
async function waRefreshGuidance(story){
  const sequence=++waGuidanceSequence;
  waRemoveOldGuidance();
  const pending=waAddMessage('I’m checking the next step and the official support route for what you described…','bot');
  pending?.classList.add('wa-guidance-message','is-loading');waGuidancePending=pending;
  try{
    let facts=null;
    try{const extracted=await api('/api/extraction/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({description:story})});facts=extracted?.extracted_facts||null;}catch(_){facts=null;}
    if(sequence!==waGuidanceSequence)return;
    waLatestExtractedFacts=facts;
    const fields=facts?.fields||{};
    const merchantField=fields.merchant||{};
    const merchant=merchantField.value&&['medium','high'].includes(merchantField.confidence)&&!merchantField.needs_confirmation?String(merchantField.value):'';
    const amountField=fields.amount||{};
    const amountConflicts=(facts?.conflicts||[]).some(c=>c.field==='amount');
    const amount=amountField.value!==null&&amountField.value!==undefined&&!amountField.needs_confirmation&&!amountConflicts&&['medium','high'].includes(amountField.confidence)?Number(amountField.value):null;
    const dateField=fields.payment_date||{};
    const paymentDate=dateField.value&&!dateField.needs_confirmation?String(dateField.value):'';
    const statusField=fields.payment_status||{};
    const allowedStatuses=new Set(['unknown','failed','pending','successful','refund_pending','unauthorized']);
    const status=allowedStatuses.has(statusField.value)?statusField.value:'unknown';
    const issueField=fields.issue_type||{};
    const issueType=waSelectedIssue||((issueField.value&&['medium','high'].includes(issueField.confidence))?issueField.value:waGuessIssue(story));
    const payload={issue_type:issueType,merchant,amount,payment_date:paymentDate,payment_status:status,description:story};
    const result=await api('/api/resolution/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if(sequence!==waGuidanceSequence||!pending||!pending.isConnected)return;
    waBuildGuidanceMessage(pending,result,story);
  }catch(err){
    if(sequence!==waGuidanceSequence||!pending||!pending.isConnected)return;
    pending.classList.remove('is-loading');pending.replaceChildren();
    waAppendElement(pending,'p','',`I couldn’t load the guided recommendation: ${err.message||'Please try again.'}`);
    const retry=waAppendElement(pending,'button','wa-copy-message','Try again');retry.type='button';retry.dataset.waRetryGuidance='1';
  }
}
function waHandlePick(issue){
  if(waChatSaved)return;
  waSelectedIssue=issue;waAddMessage(issue,'user');waSetQuickReplies(false);
  waAddMessage('Samajh gaya. Tell me in your own words what happened. You can speak or type in one of the supported languages. You do not need every detail yet.','bot');
  $('#waMessage')?.focus();
}
$('#waQuickReplies')?.addEventListener('click',e=>{const btn=e.target.closest('[data-wa-pick]');if(btn)waHandlePick(btn.dataset.waPick);});
$('#waComposer')?.addEventListener('submit',async e=>{
  e.preventDefault(); if(waChatSaved)return;
  const input=$('#waMessage'),message=input.value.trim(); if(message.length<3)return;
  if(!waSelectedIssue)waSelectedIssue=waGuessIssue(message);
  waAddMessage(message,'user');waDescriptionParts.push(message);input.value='';waSetQuickReplies(false);waRefreshSaveArea();
  await waRefreshGuidance(waDescriptionParts.join('\n').trim());input.focus();
});
$('#waThread')?.addEventListener('click',async e=>{
  const speak=e.target.closest('[data-wa-speak]');
  if(speak){const text=speak.closest('.wa-message')?.querySelector('p')?.textContent||'';if(text)waSpeak(text);return;}
  const speakGuidance=e.target.closest('[data-wa-speak-guidance]');
  if(speakGuidance){const card=speakGuidance.closest('.wa-recommendation-card');const text=card?.querySelector('.wa-guidance-first-move')?.innerText||'';if(text)waSpeak(text);return;}
  const copy=e.target.closest('[data-wa-copy-draft]');
  if(copy){const area=copy.closest('details')?.querySelector('textarea');if(area){try{await navigator.clipboard.writeText(area.value);showToast('Draft copied. Review it before sending through the official channel.');}catch(_){area.focus();area.select();showToast('Select the message and copy it.');}}return;}
  const retry=e.target.closest('[data-wa-retry-guidance]');if(retry){await waRefreshGuidance(waDescriptionParts.join('\n').trim());return;}
  const open=e.target.closest('[data-wa-open-case]'),again=e.target.closest('[data-wa-new]');
  if(open){currentCaseId=open.dataset.waOpenCase;showView('detail');}
  if(again){
    waGuidanceSequence++;waSelectedIssue='';waDescriptionParts=[];waChatSaved=false;waLatestExtractedFacts=null;
    $('#waMessage').disabled=false;$('#waComposer button[type="submit"]').disabled=false;$('#waAttachHint').disabled=false;$('#waLanguageCode').disabled=false;$('#waVoiceButton').disabled=!waGuidedVoiceEnabled;
    $('#waThread').innerHTML='';waAddMessage('Namaste! 👋 Welcome to BolKeResolve.','bot');waAddMessage('Paise se related kya problem aa rahi hai? Choose an option below, or just tell me in your own words.','bot');
    waSetQuickReplies(true);waRefreshSaveArea();$('#waCreateCaseButton').disabled=false;$('#waCreateCaseButton').innerHTML='Save case <span>↗</span>';$('#waMessage').focus();
  }
});
$('#waAttachHint')?.addEventListener('click',()=>showToast('You can add screenshots or statements after saving your case. Please remove private account details first.'));

function waSetVoiceStatus(text,isError=false){const status=$('#waVoiceStatus');if(status){status.textContent=text;status.classList.toggle('is-error',isError);}}
function waVoiceUi(active){const button=$('#waVoiceButton');if(!button)return;button.classList.toggle('is-recording',active);button.setAttribute('aria-pressed',String(active));button.innerHTML=active?'<span aria-hidden="true">■</span> Stop and transcribe':'<span aria-hidden="true">🎙</span> Speak';}
function waCleanupRecorder(){waVoiceRecording=false;clearInterval(waVoiceTimer);waVoiceTimer=null;try{waVoiceProcessor?.disconnect();}catch(_){}try{waVoiceSource?.disconnect();}catch(_){}try{waVoiceGain?.disconnect();}catch(_){}waVoiceStream?.getTracks().forEach(track=>track.stop());waVoiceStream=null;waVoiceProcessor=null;waVoiceSource=null;waVoiceGain=null;if(waVoiceContext)waVoiceContext.close().catch(()=>{});waVoiceContext=null;waVoiceUi(false);}
function waVoiceTick(){const seconds=Math.floor((Date.now()-waVoiceStartedAt)/1000);waSetVoiceStatus(`Listening… ${formatDuration(seconds)} / 01:00. Tap Stop and transcribe when finished.`);if(seconds>=60)waStopVoiceRecording();}
async function waStartVoiceRecording(){
  if(!waGuidedVoiceEnabled){waSetVoiceStatus('Voice input is not available in this session. You can type your story instead.',false);return;}
  if(!navigator.mediaDevices?.getUserMedia){waSetVoiceStatus('Microphone access needs HTTPS or localhost on a supported browser. You can type your story instead.',true);return;}
  const button=$('#waVoiceButton');if(button)button.disabled=true;
  try{
    waVoiceStream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true}});
    const AudioCtx=window.AudioContext||window.webkitAudioContext;if(!AudioCtx)throw new Error('This browser does not support audio recording.');
    waVoiceContext=new AudioCtx({sampleRate:16000});await waVoiceContext.resume();waVoiceSampleRate=waVoiceContext.sampleRate;
    waVoiceSource=waVoiceContext.createMediaStreamSource(waVoiceStream);waVoiceProcessor=waVoiceContext.createScriptProcessor(4096,1,1);waVoiceGain=waVoiceContext.createGain();waVoiceGain.gain.value=0;
    waVoiceBuffers=[];waVoiceProcessor.onaudioprocess=event=>{if(waVoiceRecording)waVoiceBuffers.push(new Float32Array(event.inputBuffer.getChannelData(0)));};
    waVoiceSource.connect(waVoiceProcessor);waVoiceProcessor.connect(waVoiceGain);waVoiceGain.connect(waVoiceContext.destination);
    waVoiceRecording=true;waVoiceStartedAt=Date.now();waVoiceUi(true);waSetVoiceStatus('Listening… Speak naturally. Nothing is sent for transcription until you stop.');waVoiceTimer=setInterval(waVoiceTick,250);
  }catch(err){waCleanupRecorder();waSetVoiceStatus('Could not start the microphone. Check browser permission or continue by typing. '+(err?.name==='NotAllowedError'?'Allow microphone access in your browser settings.':''),true);}
  finally{if(button)button.disabled=false;}
}
async function waStopVoiceRecording(){
  if(!waVoiceRecording)return;
  waVoiceRecording=false;clearInterval(waVoiceTimer);waVoiceTimer=null;
  const sampleRate=waVoiceSampleRate,samples=concatenate(waVoiceBuffers);waVoiceBuffers=[];waCleanupRecorder();
  if(!samples?.length){waSetVoiceStatus('No audio was captured. Try again or type your story.',true);return;}
  const pcm=resample(samples,sampleRate,16000),duration=Math.round(pcm.length/16000);
  if(duration<1){waSetVoiceStatus('That recording was too short. Try again or type your story.',true);return;}
  const button=$('#waVoiceButton');if(button)button.disabled=true;
  waSetVoiceStatus('Transcribing your words… You can review the transcript before sending it.');
  try{
    const wav=encodeWav(pcm,16000),form=new FormData();form.append('audio_file',new File([wav],'guided-story.wav',{type:'audio/wav'}));form.append('language_code',waSelectedLanguage());
    const out=await api('/api/voice/transcribe',{method:'POST',body:form});const transcript=String(out.transcript||'').trim();
    if(!transcript)throw new Error('We could not hear enough words. Try again or type your story.');
    const input=$('#waMessage');input.value=[input.value.trim(),transcript].filter(Boolean).join(input.value.trim()?' ':'');input.focus();
    const lang=waSelectedLanguage()==='auto'?detectLanguageCode(transcript):waSelectedLanguage();
    waSetVoiceStatus(`Transcript ready (${languageNames[lang]||lang}). Read or edit it in the message box, then press Send. It has not been sent yet.`);
    if(out.redacted_types?.length)showToast('Some sensitive-looking details were redacted from the transcript. Review it carefully before sending.');
  }catch(err){waSetVoiceStatus(err.message||'Voice transcription is unavailable. You can type your story instead.',true);}
  finally{if(button)button.disabled=false;}
}
$('#waVoiceButton')?.addEventListener('click',()=>waVoiceRecording?waStopVoiceRecording():waStartVoiceRecording());
$('#waLanguageCode')?.addEventListener('change',()=>{const selected=waSelectedLanguage();if(waVoiceRecording){waSetVoiceStatus('Language changed for the next recording. Stop this recording before changing transcription language.',true);}else waSetVoiceStatus(selected==='auto'?'Auto-detect will try the supported Indian languages. Check the transcript before sending.':`Voice transcription language: ${languageNames[selected]||selected}. Check the transcript before sending.`);});

function liveRoomSetOptionalConsent(selector,available,statusSelector){
  const option=$(selector),label=option?.querySelector('.live-room-ai-consent'),input=label?.querySelector('input'),status=$(statusSelector);
  const enabled=Boolean(available);
  if(input){input.disabled=!enabled;if(!enabled)input.checked=false;input.setAttribute('aria-describedby',enabled?'':(status?.id||''));}
  // Some older component rules use display:grid !important. Set the hidden state
  // explicitly as well as the attribute so unavailable controls cannot leave a dead square.
  if(label){label.hidden=!enabled;label.setAttribute('aria-hidden',String(!enabled));if(enabled)label.style.removeProperty('display');else label.style.setProperty('display','none','important');}
  if(status){status.hidden=enabled;status.setAttribute('aria-live','polite');if(enabled)status.style.setProperty('display','none','important');else status.style.removeProperty('display');}
  if(option){option.classList.toggle('is-unavailable',!enabled);option.dataset.available=String(enabled);}
}
function liveRoomRenderConsentAvailability(){
  liveRoomSetOptionalConsent('#liveRoomCaseAIOption',liveRoomCaseAIAvailable,'#liveRoomCaseAIUnavailable');
  liveRoomSetOptionalConsent('#liveRoomTranslationOption',liveRoomMultilingualAvailable,'#liveRoomTranslationUnavailable');
  const workspace=$('#liveRoomCaseAIWorkspaceOption'),label=workspace?.querySelector('.live-room-ai-consent'),input=$('#liveRoomCaseAIActiveConsent'),status=$('#liveRoomCaseAIWorkspaceUnavailable');
  if(label)label.hidden=!liveRoomCaseAIAvailable;
  if(input){input.disabled=!liveRoomCaseAIAvailable||!liveRoomCaseId;if(!liveRoomCaseAIAvailable)input.checked=false;}
  if(status)status.hidden=liveRoomCaseAIAvailable;
}
async function loadPublicConfig(){
  try{
    const config=await api('/api/config');
    if(typeof config.accounts_enabled==='boolean'){accountsEnabled=config.accounts_enabled;hideAuthGate();}
    whatsappBusinessNumber=String(config.whatsapp_business_number||'').replace(/\D/g,'');
    whatsappCloudApiReady=!!config.whatsapp_cloud_api_ready;
    whatsappTwilioSandboxConfigured=!!config.twilio_whatsapp_configured;
    whatsappReminderTemplateConfigured=!!config.whatsapp_reminder_template_configured;
    liveRoomMultilingualAvailable=!!config.multilingual_guidance_available;
    liveRoomVisionAvailable=!!config.visual_evidence_ai_available;window.bolkeTimbreV3=String(config.gnani_tts_model||'').toLowerCase()==='timbre-v3.0';
    liveRoomCaseAIAvailable=!!config.case_interpretation_ai_available;
    liveRoomRenderConsentAvailability();
    waGuidedVoiceEnabled=!!config.guided_voice_enabled;
    const voiceButton=$('#waVoiceButton');
    if(voiceButton){voiceButton.disabled=!waGuidedVoiceEnabled;voiceButton.title=waGuidedVoiceEnabled?'Record up to 60 seconds, then review the transcript':'Voice input is not configured for this deployment';}
    waSetVoiceStatus(waGuidedVoiceEnabled?'Voice is ready. Your transcript will appear for review before you send it.':'Voice input is not available in this session. You can type your story instead.',false);
    const note=$('#whatsappIntegrationNote');
    const openButton=$('#openWhatsAppButton');
    if(note){note.textContent=whatsappCloudApiReady?'This opens the official BolKeResolve WhatsApp line. Send START to opt in before sharing case details.':'For now, you can start and track your case here. This message-style chat saves your case in BolKeResolve.';}
    if(openButton){openButton.innerHTML=whatsappCloudApiReady?'<span class="wa-brand-icon">◉</span> Open official WhatsApp <span>↗</span>':'<span class="wa-brand-icon">✳</span> Continue here instead <span>↓</span>';openButton.removeAttribute('aria-disabled');openButton.classList.toggle('is-unavailable',false);}
    const heroStatus=$('#caseWhatsAppStatus');if(heroStatus)heroStatus.textContent=whatsappCloudApiReady?'Ready to connect':'Keep updating here';
    const caseWaButton=$('.case-whatsapp-connect');if(caseWaButton){caseWaButton.disabled=false;caseWaButton.textContent=whatsappCloudApiReady?'Connect this case ↗':whatsappTwilioSandboxConfigured?'Link to Twilio Sandbox (test) ↗':'Continue case updates ↓';}
    const caseWaDescription=$('#caseWhatsAppDescription');if(caseWaDescription&&!whatsappCloudApiReady)caseWaDescription.textContent=whatsappTwilioSandboxConfigured?'You can link this case to the Twilio WhatsApp Sandbox for testing; the sandbox is not a production number.':'Keep your progress, notes and follow-up date together on this case page.';
  }catch(_){whatsappBusinessNumber='';whatsappCloudApiReady=false;whatsappTwilioSandboxConfigured=false;whatsappReminderTemplateConfigured=false;waGuidedVoiceEnabled=false;liveRoomMultilingualAvailable=false;liveRoomCaseAIAvailable=false;liveRoomRenderConsentAvailability();const voiceButton=$('#waVoiceButton');if(voiceButton)voiceButton.disabled=true;waSetVoiceStatus('Could not check voice configuration. You can type your story instead.',true);const note=$('#whatsappIntegrationNote');if(note)note.textContent='You can still create and track your case here. Use the message-style chat to get started.';const openButton=$('#openWhatsAppButton');if(openButton){openButton.innerHTML='<span class="wa-brand-icon">✳</span> Continue here instead <span>↓</span>';openButton.removeAttribute('aria-disabled');}}
}
$('#openWhatsAppButton')?.addEventListener('click',()=>{
  if(!whatsappCloudApiReady||!whatsappBusinessNumber){$('#waMessage')?.focus({preventScroll:false});$('#waMessage')?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});showToast('WhatsApp is not connected here yet. You can start your case in this chat instead.');return;}
  const text='START';
  const url=`https://wa.me/${whatsappBusinessNumber}?text=${encodeURIComponent(text)}`;
  window.open(url,'_blank','noopener,noreferrer');
});
$('#waCreateCaseButton')?.addEventListener('click',async()=>{
  const description=waDescriptionParts.join('\n').trim();
  if(description.length<8){waAddMessage('Please tell me a little more about what happened first.','bot');return;}
  const button=$('#waCreateCaseButton'); button.disabled=true; button.textContent='Saving…';
  try{
    const extractedFields=waLatestExtractedFacts?.fields||{};
    const amountField=extractedFields.amount||{};
    const amountConflict=(waLatestExtractedFacts?.conflicts||[]).some(c=>c.field==='amount');
    const amount=amountField.value!==null&&amountField.value!==undefined&&!amountField.needs_confirmation&&!amountConflict&&['medium','high'].includes(amountField.confidence)?Number(amountField.value):null;
    const merchantField=extractedFields.merchant||{};
    const merchant=merchantField.value&&!merchantField.needs_confirmation&&['medium','high'].includes(merchantField.confidence)?String(merchantField.value):'';
    const dateField=extractedFields.payment_date||{};
    const paymentDate=dateField.value&&!dateField.needs_confirmation?String(dateField.value):'';
    const chosenLanguage=waSelectedLanguage();
    const lang=chosenLanguage==='auto'?detectLanguageCode(description):chosenLanguage;
    const item=await api('/api/cases',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({issue_type:waSelectedIssue||extractedFields.issue_type?.value||waGuessIssue(description),merchant,amount,payment_date:/^\d{4}-\d{2}-\d{2}$/.test(paymentDate)?paymentDate:'',language_code:lang,description})});
    currentCaseId=item.case_id; waChatSaved=true; waRefreshSaveArea();
    $('#waQuickReplies').hidden=true;
    $('#waMessage').disabled=true; $('#waComposer button[type="submit"]').disabled=true; $('#waAttachHint').disabled=true; $('#waVoiceButton').disabled=true; $('#waLanguageCode').disabled=true;
    waAddMessage(`Your case ${item.case_id} is saved. You can open it any time to review the details, add evidence, or prepare a support request.`, 'bot', `<div class="wa-chat-actions"><button type="button" data-wa-open-case="${escapeHtml(item.case_id)}">View my case ↗</button><button type="button" data-wa-new="1">Start another</button></div>`);
    await refreshCaseCountOnly();
    showToast(`Case ${item.case_id} created.`);
  }catch(err){showToast(err.message,'error');button.disabled=false;button.innerHTML='Save case <span>↗</span>';}
});
function clearPendingSharedIntake(){
  pendingSharedIntakeToken='';pendingSharedIntakeData=null;pendingSharedIntakeAttachCaseId='';
  try{sessionStorage.removeItem('bolke_pending_share_token');}catch(_){}
}
function closeSharedIntakeDialog(){const dialog=$('#sharedIntakeDialog');if(dialog?.open)dialog.close();else if(dialog)dialog.removeAttribute('open');}
function setSharedIntakeText(id,value,hiddenWhenEmpty=true){const node=$(`#${id}`);if(!node)return;node.textContent=String(value||'');if(hiddenWhenEmpty)node.hidden=!value;}
async function populateSharedIntakeCases(){
  const select=$('#sharedIntakeCaseSelect'),button=$('#sharedIntakeAttachButton'),hint=$('#sharedIntakeCaseHint');
  if(!select||!button)return;
  select.innerHTML='<option value="">Choose a case…</option>';
  if(authRequired&&!signedInUser){button.disabled=true;if(hint)hint.textContent='Sign in to add to an existing case, or start a new case and sign in when saving.';return;}
  try{
    const cases=await api('/api/cases');
    cases.forEach(item=>{const option=document.createElement('option');option.value=item.case_id;option.textContent=`${item.issue_type||'Case'} · ${item.merchant||'Merchant not provided'} · ${item.case_id}`;select.appendChild(option);});
    button.disabled=!cases.length;if(hint)hint.textContent=cases.length?'Choose the case this item belongs to. Nothing is added until you click the button.':'No saved cases yet. Use the item to start a new case.';
  }catch(error){button.disabled=true;if(hint)hint.textContent='Saved cases could not be loaded. You can still use this item to start a new case.';}
}
async function showSharedIntakeDialog(token){
  pendingSharedIntakeToken=token;
  const dialog=$('#sharedIntakeDialog');
  if(!dialog)throw new Error('The shared-item review dialog is unavailable in this page.');
  setSharedIntakeText('sharedIntakeTitle','Loading shared item…',false);
  setSharedIntakeText('sharedIntakeNotice','Checking the encrypted temporary item. Nothing has been added to a case.',false);
  setSharedIntakeText('sharedIntakeText','',true);setSharedIntakeText('sharedIntakeFileMeta','',true);setSharedIntakeText('sharedIntakeSourceDomain','',true);
  if(typeof dialog.showModal==='function'){if(!dialog.open)dialog.showModal();}else dialog.setAttribute('open','open');
  try{
    const item=await api('/api/shared-intake/preview',{headers:{'X-Share-Intake-Token':token}});
    pendingSharedIntakeData=item;
    setSharedIntakeText('sharedIntakeTitle',item.title||item.filename||'Item from another app',false);
    setSharedIntakeText('sharedIntakeNotice',item.notice||'Review this item. It has not been added to a case.',false);
    setSharedIntakeText('sharedIntakeText',item.text||'',true);
    setSharedIntakeText('sharedIntakeFileMeta',item.has_file?`${item.filename||'Shared file'} · ${(Number(item.size_bytes||0)/1024).toFixed(0)} KB · ${item.mime_type||'file type not provided'}`:'',true);
    setSharedIntakeText('sharedIntakeSourceDomain',item.source_domain?`Shared from: ${item.source_domain} · sender/source not verified`: '',true);
    await populateSharedIntakeCases();
  }catch(error){closeSharedIntakeDialog();clearPendingSharedIntake();showToast(error.message||'This shared item could not be opened. Share it again or use normal upload.','error');}
}
function captureSharedIntakeTokenEarly(){
  // Strip the bearer capability from the address bar before any asynchronous app setup.
  // Retain it in memory/session storage only long enough to show the review dialog.
  try{
    const url=new URL(window.location.href);const hashParams=new URLSearchParams(url.hash.replace(/^#/,''));
    const token=url.searchParams.get('shared_intake')||hashParams.get('shared_intake');
    if(!token)return;
    if(/^[A-Za-z0-9_-]{30,100}$/.test(token)){
      preloadedSharedIntakeToken=token;
      try{sessionStorage.setItem('bolke_pending_share_token',token);}catch(_){}
    }
    url.searchParams.delete('shared_intake');hashParams.delete('shared_intake');
    url.hash=hashParams.toString()?`#${hashParams.toString()}`:'';
    history.replaceState(null,'',url.pathname+(url.search?url.search:'')+url.hash);
  }catch(_){}
}
async function handleIncomingShareTarget(){
  const url=new URL(window.location.href);
  const queryToken=url.searchParams.get('shared_intake');
  let token=queryToken||preloadedSharedIntakeToken||'';
  preloadedSharedIntakeToken='';
  if(queryToken){try{sessionStorage.setItem('bolke_pending_share_token',queryToken);}catch(_){}url.searchParams.delete('shared_intake');history.replaceState(null,'',url.pathname+(url.search?url.search:'')+url.hash);}
  if(!token){try{token=sessionStorage.getItem('bolke_pending_share_token')||'';}catch(_){token='';}}
  if(!token)return;
  if(!/^[A-Za-z0-9_-]{30,100}$/.test(token)){clearPendingSharedIntake();return;}
  try{await showSharedIntakeDialog(token);}catch(error){showToast(error.message||'Unable to review the shared item.','error');}
}
async function attachSharedIntakeToCase(caseId,includeContext=true){
  if(!pendingSharedIntakeToken)throw new Error('This shared item is no longer available. Share it again from the original app.');
  const result=await api('/api/shared-intake/attach',{method:'POST',headers:{'Content-Type':'application/json','X-Share-Intake-Token':pendingSharedIntakeToken},body:JSON.stringify({case_id:caseId,include_context:Boolean(includeContext)})});
  clearPendingSharedIntake();
  return result;
}
async function retryPendingSharedIntake(button){
  const caseId=pendingSharedIntakeAttachCaseId||currentCaseId;if(!caseId||!pendingSharedIntakeToken)return;
  if(button){button.disabled=true;button.textContent='Adding item…';}
  try{await attachSharedIntakeToCase(caseId,false);await loadCase(caseId);await refreshCaseCountOnly();showToast('Shared item added to your case.');}
  catch(error){if(button){button.disabled=false;button.textContent='Try adding item again ↗';}showToast(error.message||'The shared item could not be attached yet.','error');}
}
$('#sharedIntakeAttachButton')?.addEventListener('click',async()=>{
  const button=$('#sharedIntakeAttachButton'),caseId=$('#sharedIntakeCaseSelect')?.value||'';
  if(!caseId){showToast('Choose a saved case first.','error');return;}
  button.disabled=true;button.textContent='Adding to case…';
  try{await attachSharedIntakeToCase(caseId,true);closeSharedIntakeDialog();currentCaseId=caseId;activeCaseTab='prep';showView('detail');await refreshCaseCountOnly();showToast('Shared item added. Review its source and details in your case.');}
  catch(error){showToast(error.message||'Could not add the shared item.','error');button.disabled=false;button.textContent='Add to selected case';}
});
$('#sharedIntakeNewCaseButton')?.addEventListener('click',()=>{
  const item=pendingSharedIntakeData;if(!item||!pendingSharedIntakeToken){showToast('The shared item has expired. Share it again or use normal upload.','error');return;}
  const storyParts=[];if(item.title)storyParts.push(`Shared item: ${item.title}`);if(item.text)storyParts.push(item.text);if(item.source_domain)storyParts.push(`Source site: ${item.source_domain} (not independently verified).`);if(item.has_file&&!item.text)storyParts.push('I shared a receipt or screenshot to help explain my payment or refund issue. Please help me identify the next step.');
  const story=storyParts.join('\n\n').trim()||'I shared a receipt or link from another app and need help with a payment or refund issue.';
  const description=$('#description');if(description){description.value=story.slice(0,5000);description.dispatchEvent(new Event('input',{bubbles:true}));}
  $('#issueType').value='Other payment issue';syncIssueChoiceFromSelect();closeSharedIntakeDialog();setIntakeStep(1,{scroll:false});showView('new');if(description)description.focus({preventScroll:true});showToast('Review the shared details, choose the issue type, and save the case to add the shared file.');
});
$('#sharedIntakeDiscardButton')?.addEventListener('click',async()=>{
  const token=pendingSharedIntakeToken;const button=$('#sharedIntakeDiscardButton');if(button){button.disabled=true;button.textContent='Discarding…';}
  try{if(token)await api('/api/shared-intake/discard',{method:'DELETE',headers:{'X-Share-Intake-Token':token}});}catch(_){}
  clearPendingSharedIntake();closeSharedIntakeDialog();showToast('Shared item discarded. It was not added to a case.');if(button){button.disabled=false;button.textContent='Discard shared item';}
});
$('#sharedIntakeDialog')?.addEventListener('cancel',event=>{event.preventDefault();showToast('Choose whether to add the shared item to a case or discard it.');});
$('#sharedIntakeDialog')?.addEventListener('click',event=>{const dialog=$('#sharedIntakeDialog');if(event.target===dialog)showToast('Choose an action to finish reviewing this shared item.');});

captureSharedIntakeTokenEarly();
initialiseApplication().then(async()=>{await handleAuthActionUrl();handleIncomingShareTarget();});

// Live Resolution Room: real-time Gnani transcription, permission-based capture,
// and persistence into the existing case/timeline rather than a parallel data store.
function liveRoomStatus(text,live=false){const el=$('#liveRoomConnectionStatus');if(!el)return;el.textContent=text;el.classList.toggle('is-live',live);}
function liveRoomFeedback(text,isError=false){const el=$('#liveRoomFeedback');if(!el)return;el.textContent=text||'';el.classList.toggle('is-error',!!isError);}
function liveRoomAudioState(title,hint,active=false){const t=$('#liveRoomAudioState'),h=$('#liveRoomAudioHint'),pulse=$('#liveRoomAudioPulse');if(t)t.textContent=title;if(h)h.textContent=hint;if(pulse)pulse.classList.toggle('is-active',!!active);}
function liveRoomMicLevel(rms=0){const bar=$('#liveRoomMicLevelFill'),label=$('#liveRoomMicLevelLabel');const level=Math.max(0,Math.min(100,Math.round(Number(rms||0)*900)));if(bar)bar.style.width=`${level}%`;if(rms>.004){liveRoomAudioSignalSeen=true;if(label)label.textContent='Microphone signal detected';}else if(label&&!liveRoomAudioSignalSeen)label.textContent='Speak to test your microphone';}
function liveRoomTranscriptBubble(speaker,text,meta={}){const root=$('#liveRoomTranscript');if(!root||!text)return;root.querySelector('.live-room-transcript-empty')?.remove();const node=document.createElement('div');node.className=`live-room-turn ${speaker}`;if(meta.turnId){node.dataset.turnId=meta.turnId;}const label=document.createElement('span');label.className='live-room-turn-label';label.textContent=speaker==='user'?'You':speaker==='organisation'?'Organisation':'BolKeResolve';const body=document.createElement('div');body.className='live-room-turn-body';body.textContent=text;node.append(label,body);if(speaker==='user'&&meta.turnId){const edit=document.createElement('button');edit.type='button';edit.className='live-room-turn-edit';edit.dataset.editTurn=meta.turnId;edit.textContent='Edit transcript';node.append(edit);}root.append(node);root.scrollTop=root.scrollHeight;}
function liveRoomOfferCaptureFromIntent(text){
  const raw=String(text||'').toLowerCase();let kind='',title='',description='',button='';
  if(/\b(stop|cancel|end) (?:the )?(?:recording|clip|screen share|sharing|capture)\b|\bstop sharing\b|\bstop this process\b/.test(raw)){
    if(liveRoomClipRecorder?.state==='recording')liveRoomStopClip().catch(()=>{});
    if(liveRoomScreenStream){liveRoomStopTracks(liveRoomScreenStream);liveRoomScreenStream=null;liveRoomScreenCaptureReady=false;const preview=$('#liveRoomScreenPreview');if(preview){preview.srcObject=null;preview.hidden=true;}const control=$('#liveRoomScreenButton');if(control)control.textContent='Share screen';}
    liveRoomFeedback('Capture stopped. Anything already saved remains in this case.');return 'stopped';
  }
  const asksToRecordScreen=/\b(record|recording|capture)\b/.test(raw)&&/\b(screen|shared screen|screen i shared|screen you can see)\b/.test(raw);
  const asksCamera=/\b(open|turn on|start|switch on|enable)\b.{0,35}\bcamera\b|\bcamera\b.{0,25}\b(open|on|start|enable)\b/.test(raw);
  if(asksToRecordScreen){
    if(liveRoomScreenCaptureReady&&liveRoomScreenStream){kind='clip';title='Record the shared screen';description='Your screen is already being shared. Start a short recording when you are ready. You can stop it at any time.';button='Record shared screen';}
    else{kind='screen';title='Share the screen before recording';description='Choose the tab or window that contains the order or support reply. Once sharing starts, you can record a short clip. You can stop sharing at any time.';button='Choose screen to share';}
  }
  else if(/\b(screen|browser tab|window)\b/.test(raw)&&/\b(share|show|see|display)\b/.test(raw)){kind='screen';title='Share the relevant screen';description='Choose only the tab or window with the order, refund status or support conversation. The browser will ask you to approve it. You can stop sharing at any time.';button='Choose screen to share';}
  else if(asksCamera||(/\b(camera|show you|showing you|hold it up|hold this|show this document)\b/.test(raw)&&/\b(document|paper|receipt|photo|picture)\b/.test(raw))){kind='camera';title='Open your camera or choose an existing photo';description='Open the camera to show a document live, or choose a photo already saved on your device. Review it before adding it to this case.';button='Open camera';}
  else if(/\b(screenshot|screen shot|image|photo|picture|receipt|pdf|document|file)\b/.test(raw)&&/\b(upload|attach|send|add|choose|select|share|available|have)\b/.test(raw)){kind='file';title='Add this proof to your case';description='Choose the screenshot, receipt, refund confirmation or support reply. The original will be stored in this case.';button='Choose a file';}
  else if(/\b(record|make) (?:a )?(?:video|clip)\b/.test(raw)){kind='clip';title='Record a short evidence clip';description='Start the camera or share the relevant screen, then record up to 30 seconds. Stop whenever you are ready.';button='Start recording';}
  else return '';
  const root=$('#liveRoomTranscript');if(!root)return kind;root.querySelectorAll('.live-room-capture-intent').forEach(node=>node.remove());
  const card=document.createElement('article');card.className='live-room-capture-intent';const heading=document.createElement('b');heading.textContent=title;const note=document.createElement('p');note.textContent=description;
  const action=document.createElement('button');action.type='button';action.className='button button-dark';action.textContent=button;action.dataset.liveIntentAction=kind;
  const actions=document.createElement('div');actions.className='live-room-capture-intent-actions';actions.append(action);
  if(kind==='camera'){
    const file=document.createElement('button');file.type='button';file.className='button button-quiet';file.textContent='Choose existing photo';file.dataset.liveIntentAction='file';actions.append(file);
  }
  const cancel=document.createElement('button');cancel.type='button';cancel.className='button button-quiet';cancel.textContent='Not now';cancel.dataset.liveIntentAction='dismiss';actions.append(cancel);
  card.append(heading,note,actions);root.append(card);root.scrollTop=root.scrollHeight;return kind;
}
function liveRoomIsLowInformationUtterance(text){
  const value=String(text||'').trim().toLowerCase().replace(/[.,!?;:…]+/g,' ').replace(/\s+/g,' ').trim();
  if(!value)return true;
  const wf=activeCaseSnapshot?.resolution?.adaptive_workflow||{};
  const hasPendingQuestion=Boolean(wf.next_question?.field);
  if(hasPendingQuestion&&/^(yes|no|yeah|yep|nope|haan|han|nahi|nahin|नहीं|हाँ|जी|full|whole|entire|partial|cancelled|canceled|pending|initiated|not sure|unknown|poora|pura|पूरा|पूरे)$/.test(value))return false;
  return /^(like|um|uh|erm|hmm+|huh|ah+|oh|okay|ok|आई|ऐ|हम्म|अं|आह|hmm okay)$/.test(value);
}
function liveRoomWorkflowSignature(workflow){
  const f=workflow?.facts||{},q=workflow?.next_question||{},step=workflow?.current_step||{},e=workflow?.evidence_request||{};
  return JSON.stringify({status:workflow?.status,stage:workflow?.stage,title:workflow?.title,q:q.field||'',prompt:q.prompt||'',step:step.title||'',evidence:e.title||'',facts:{merchant:f.merchant,amount:f.amount,issue_type:f.issue_type,order_outcome:f.order_outcome,refund_status:f.refund_status,promised_timeline:f.promised_timeline,elapsed:f.elapsed,support_contacted:f.support_contacted,support_reference:f.support_reference,refund_scope:f.refund_scope,payment_app:f.payment_app,transaction_status:f.transaction_status}});
}
function liveRoomStructuredReply(workflow){
  if(!workflow)return 'Your update is saved. Open the case plan to see the current next step.';
  if(workflow.status==='question'&&workflow.next_question?.prompt){
    const q=workflow.next_question;
    return `CASE UPDATED\n\nONE DETAIL NEEDED\n${q.prompt}${q.why_it_matters?`\n\nWHY I’M ASKING\n${q.why_it_matters}`:''}`;
  }
  if(workflow.status==='action'&&workflow.current_step){
    const step=workflow.current_step,e=workflow.evidence_request;
    return `CASE UPDATED\n\nYOUR NEXT STEP\n${step.title||workflow.title||'Continue your case'}\n\nWHAT TO DO\n${step.detail||step.why||'Review the action in your case plan.'}${step.why?`\n\nWHY THIS MATTERS\n${step.why}`:''}${e?.title?`\n\nEVIDENCE TO ADD\n${e.title}${e.detail?` — ${e.detail}`:''}`:''}`;
  }
  return String(workflow.message||'Your update is saved. Continue with the next detail when you are ready.');
}


function liveRoomNormalizeLanguageCode(code){const value=String(code||'').trim();const aliases={'hi':'hi-IN','en':'en-IN','mr':'mr-IN','bn':'bn-IN','gu':'gu-IN','kn':'kn-IN','ml':'ml-IN','pa':'pa-IN','ta':'ta-IN','te':'te-IN'};const normalized=aliases[value]||value;return ['hi-IN','en-IN','mr-IN','bn-IN','gu-IN','kn-IN','ml-IN','pa-IN','ta-IN','te-IN'].includes(normalized)?normalized:'';}
function liveRoomLanguageCode(text=''){const selected=$('#liveRoomLanguage')?.value||'indic-auto';if(selected!=='indic-auto')return selected;return inferLanguageCodeFromText(text||'')||'en-IN';}
function liveRoomGuidanceText(c){const r=c?.resolution||{},fast=r.fastest_path||{},step=(r.recommended_steps||[])[0]||{};const q=r.next_question?.prompt||r.clarifying_question||'';let summary=fast.title||step.title||'Review the payment details';let reason=fast.reason||step.why||'This is the safest next step based on the information currently available.';let ask=q?`\n\nOne thing I need to ask: ${q}`:'';const urgent=r.urgency?.level==='urgent'?`${r.urgency.message||'Please contact your bank or provider immediately.'}\n\n`:'';return `${urgent}Based on what you have shared, your next move is: ${summary}. ${reason}${ask}`.slice(0,1800);}
function liveRoomApplyGuidanceOverride(){
  const override=liveRoomGuidanceOverride;
  if(!override||override.case_id!==liveRoomCaseId)return;
  const title=$('#liveRoomGuidanceTitle'),translation=$('#liveRoomGuidanceTranslation');
  const headings={'hi-IN':'आपका अगला कदम','hi-en':'Aapka next step','mr-IN':'तुमची पुढची कृती','bn-IN':'আপনার পরবর্তী পদক্ষেপ','gu-IN':'તમારું આગલું પગલું','kn-IN':'ನಿಮ್ಮ ಮುಂದಿನ ಹಂತ','ml-IN':'നിങ്ങളുടെ അടുത്ത നടപടി','pa-IN':'ਤੁਹਾਡਾ ਅਗਲਾ ਕਦਮ','ta-IN':'உங்கள் அடுத்த படி','te-IN':'మీ తదుపరి చర్య','en-IN':'Your next move'};
  if(title)title.textContent=headings[override.language_code]||'Your next move';
  // Keep the concise action/reason and structured checklist visible. The full
  // translated narration is available separately so it cannot replace the plan.
  if(translation){translation.hidden=!override.guidance_text;translation.innerHTML=override.guidance_text?`<details><summary>Read the full explanation in ${escapeHtml(override.language_label||'your language')}</summary><p>${escapeHtml(override.guidance_text)}</p></details>`:'';}
}
function liveRoomRestoreGuidanceFromTimeline(c){
  const events=Array.isArray(c?.timeline)?c.timeline:[];
  const latest=[...events].reverse().find(event=>event?.event_type==='live_room_agent_guidance');
  if(!latest||latest?.metadata?.translation_status!=='translated'||!latest?.metadata?.language_code||!latest?.message)return null;
  const prefix='BolKeResolve guidance: ';
  const text=String(latest.message).startsWith(prefix)?String(latest.message).slice(prefix.length):String(latest.message);
  const labels={'hi-IN':'Hindi','hi-en':'Hinglish','mr-IN':'Marathi','bn-IN':'Bengali','gu-IN':'Gujarati','kn-IN':'Kannada','ml-IN':'Malayalam','pa-IN':'Punjabi','ta-IN':'Tamil','te-IN':'Telugu','en-IN':'English'};
  return {case_id:c.case_id,guidance_text:text,language_code:latest.metadata.language_code,language_label:labels[latest.metadata.language_code]||latest.metadata.language_code};
}
function liveRoomEvidenceKind(file){
  const mime=String(file?.mime_type||'').toLowerCase();
  if(mime.startsWith('image/'))return 'photos';
  if(mime.startsWith('video/'))return 'videos';
  if(mime.startsWith('audio/'))return 'audio';
  return 'documents';
}
function liveRoomRenderEvidence(c){
  const files=Array.isArray(c?.evidence)?c.evidence:[];
  const host=$('#liveRoomEvidenceList');
  const count=$('#liveRoomEvidenceCount');
  if(count)count.textContent=`${files.length} ${files.length===1?'item':'items'}`;
  const importButton=$('#liveRoomReconImportButton');
  const issueName=String(c?.issue_type||'').toLowerCase();
  const resolutionFacts=c?.resolution?.adaptive_workflow?.facts||{};
  const settlementCase=issueName.includes('settlement')||issueName.includes('gateway')||resolutionFacts.issue_family==='merchant_settlement';
  if(importButton)importButton.hidden=!settlementCase;
  if(!host)return;
  const counts={all:files.length,photos:0,documents:0,audio:0,videos:0};
  files.forEach(file=>counts[liveRoomEvidenceKind(file)]++);
  const filters=[['all','All',counts.all],['photos','Photos',counts.photos],['documents','Documents',counts.documents],['audio','Audio',counts.audio],['videos','Video',counts.videos]];
  const filtered=liveRoomEvidenceFilter==='all'?files:files.filter(file=>liveRoomEvidenceKind(file)===liveRoomEvidenceFilter);
  const filterMarkup=files.length?`<div class="live-room-evidence-filters" role="group" aria-label="Filter case evidence">${filters.map(([key,label,n])=>`<button type="button" data-live-evidence-filter="${key}" class="${liveRoomEvidenceFilter===key?'is-active':''}" aria-pressed="${liveRoomEvidenceFilter===key}">${label}<span>${n}</span></button>`).join('')}</div>`:'';
  const cards=filtered.map(file=>{
    const exhibitNumber=files.indexOf(file)+1;
    const name=String(file.original_name||'Evidence');
    const mime=String(file.mime_type||'').toLowerCase();
    const kind=liveRoomEvidenceKind(file);
    const viewUrl=`/api/cases/${encodeURIComponent(c.case_id)}/evidence/${encodeURIComponent(file.evidence_id)}`;
    const inlineUrl=`${viewUrl}?inline=true`;
    const source=String(file.capture_source||'user_upload').replaceAll('_',' ');
    const size=Number(file.size_bytes||0);
    const sizeLabel=size>=1024*1024?`${(size/1024/1024).toFixed(1)} MB`:`${Math.max(1,Math.ceil(size/1024))} KB`;
    let preview='';
    if(mime.startsWith('image/'))preview=`<a class="live-room-evidence-preview" href="${escapeHtml(inlineUrl)}" target="_blank" rel="noopener"><img src="${escapeHtml(inlineUrl)}" loading="lazy" alt="Preview of ${escapeHtml(name)}"></a>`;
    else if(mime.startsWith('video/'))preview=`<video class="live-room-evidence-video" controls preload="metadata" playsinline src="${escapeHtml(inlineUrl)}">Your browser cannot preview this video.</video>`;
    else if(mime.startsWith('audio/'))preview=`<audio class="live-room-evidence-audio" controls preload="metadata" src="${escapeHtml(inlineUrl)}">Your browser cannot play this audio.</audio>`;
    else if(mime==='application/pdf')preview=`<a class="live-room-evidence-preview-link" href="${escapeHtml(inlineUrl)}" target="_blank" rel="noopener">Preview PDF ↗</a>`;
    const icon={photos:'▧',documents:'▤',audio:'♫',videos:'▶'}[kind]||'▤';
    const claimLinks=Array.isArray(file.claim_links)?file.claim_links:[];
    const claimMarkup=claimLinks.length?`<div class="live-room-claim-links">${claimLinks.map(link=>`<span class="live-room-claim-chip ${escapeHtml(link.relation)}">${escapeHtml(link.claim_label)} · ${escapeHtml(link.relation)}</span>`).join('')}</div>`:'<span class="live-room-no-claim">Not linked to a case detail yet</span>';
    const scanText=file.scan_status==='clean'?'Scan passed':file.scan_status==='pending'?'Scan pending':file.scan_status==='quarantined'?'Quarantined':'Not scanned';
    const derivatives=Array.isArray(file.derivatives)?file.derivatives:[];
    const derivativeRows=derivatives.length?`<div class="live-room-derived-list">${derivatives.slice(0,4).map(item=>{const content=item.content&&typeof item.content==='object'?item.content:{};const summary=Array.isArray(content.applied_fields)?`${content.applied_fields.length} field(s) reviewed`:Array.isArray(content.observations)?`${content.observations.length} observation(s) reviewed`:item.derivative_type==='document_fact_review'?'Document details reviewed':item.derivative_type==='visual_ai_review'?'Visual observations reviewed':'Derived information saved';return `<div><span>${escapeHtml(String(item.derivative_type||'derived').replaceAll('_',' '))}</span><b>${escapeHtml(summary)}</b><small>${escapeHtml(item.review_status||'needs review')} · ${escapeHtml(prettyDate(item.created_at))}</small></div>`;}).join('')}</div>`:'<p class="live-room-derived-empty">No extracted or reviewed information has been saved for this file.</p>';
    const captureDetails=[file.captured_at?`Captured ${prettyDate(file.captured_at)}`:'',file.session_id?`Session ${String(file.session_id).slice(0,18)}`:'',file.sha256?`SHA-256 ${String(file.sha256).slice(0,16)}…`:''].filter(Boolean).join(' · ');
    return `<article class="live-room-evidence-item live-room-evidence-card" data-evidence-card="${escapeHtml(file.evidence_id)}">
      <div class="live-room-evidence-card-top"><span class="live-room-evidence-type">EXHIBIT ${String(exhibitNumber).padStart(2,'0')}</span><span class="live-room-evidence-kind">${icon} ${kind==='photos'?'Photo':kind==='documents'?'Document':kind==='audio'?'Audio':'Video'}</span></div>
      <div class="live-room-evidence-content"><b title="${escapeHtml(name)}">${escapeHtml(name)}</b><small>${escapeHtml(sizeLabel)} · ${escapeHtml(source)} · ${escapeHtml(prettyDate(file.captured_at||file.created_at))}</small>
        <div class="live-room-evidence-status-row"><span>● Original saved</span><span>${escapeHtml(scanText)}</span></div>
        <details class="live-room-evidence-details"><summary>Preview, details and history</summary>
          ${preview}
          <div class="live-room-evidence-integrity"><span>User supplied</span><span>Not independently verified</span><span>${escapeHtml(file.verification_status||'Authenticity not independently verified')}</span></div>
          ${captureDetails?`<p class="live-room-evidence-capture-meta">${escapeHtml(captureDetails)}</p>`:''}
          <div class="live-room-evidence-actions"><a href="${escapeHtml(inlineUrl)}" target="_blank" rel="noopener">Open preview ↗</a><a href="${escapeHtml(viewUrl)}">Download original ↓</a></div>
          <div class="live-room-claim-section"><b>Related case details</b>${claimMarkup}</div>
          <details class="live-room-claim-link-editor"><summary>Link to a case detail</summary><div class="live-room-claim-link-form"><label>Case detail<select data-claim-key><option value="issue">Issue description</option><option value="order">Order / payment</option><option value="refund_promise">Refund promise</option><option value="refund_status">Refund status</option><option value="settlement">Settlement status</option><option value="support_contact">Support conversation</option><option value="support_reply">Support reply</option><option value="bank_credit">Bank credit</option><option value="reference">Payment / complaint reference</option><option value="other">Other detail</option></select></label><label>How does it relate?<select data-claim-relation><option value="supports">Supports this detail</option><option value="contradicts">Contradicts this detail</option><option value="context">Provides context</option></select></label><button type="button" class="button button-quiet" data-link-evidence-claim="${escapeHtml(file.evidence_id)}">Save link</button></div></details>
          <div class="live-room-derived-section"><b>Information derived from this original</b>${derivativeRows}</div>
        </details>
      </div>
    </article>`;
  }).join('');
  host.innerHTML=filterMarkup+(cards||`<div class="live-room-empty">${files.length?'There are no '+escapeHtml(liveRoomEvidenceFilter)+' items in this case.':'Your evidence collection is ready. Add a photo, receipt, bank/payment screenshot, support reply, PDF or recording when it is relevant to the next step.'}</div>`);
}

function liveRoomRenderGuidance(c){
  const resolution=c?.resolution||{},workflow=resolution.adaptive_workflow||{},hasAdaptive=!!resolution.adaptive_workflow,collecting=hasAdaptive&&(!workflow.intake_complete||workflow.collecting_update),fast=resolution.fastest_path||{},steps=collecting?[]:(Array.isArray(resolution.recommended_steps)?resolution.recommended_steps:[]);
  const title=$('#liveRoomGuidanceTitle'),reason=$('#liveRoomGuidanceReason'),stepsHost=$('#liveRoomGuidanceSteps'),sources=$('#liveRoomGuidanceSources');
  const progress=$('#liveRoomGuidanceProgress'),questionHost=$('#liveRoomGuidanceQuestion'),checklistHost=$('#liveRoomGuidanceChecklist'),draftHost=$('#liveRoomSupportDraft');
  if(title)title.textContent=workflow.title||fast.title||steps[0]?.title||'Tell me a little more';
  const fullReason=workflow.reason||fast.reason||steps[0]?.why||resolution.clarifying_question||'The plan will become more specific as we confirm details.';
  if(reason)reason.textContent=String(fullReason).length>175?`${String(fullReason).slice(0,172).trimEnd()}…`:fullReason;
  const whyDetails=$('#liveRoomGuidanceWhy');if(whyDetails){whyDetails.hidden=!fullReason||String(fullReason).length<=175;const body=whyDetails.querySelector('[data-guidance-why-body]');if(body)body.textContent=fullReason;}
  if(progress){const pack=c.action_pack||{},readiness=pack.readiness||{},done=collecting?0:Number(readiness.completed_required||0),total=collecting?0:Number(readiness.required_total||0);progress.hidden=!steps.length&&!total&&!workflow.stage;const stateLabel=collecting?(workflow.collecting_update?'Collecting your update':'Story collection'):workflow.status==='question'?'Gathering one missing detail':workflow.status==='action'?'Next action ready':'Case updated';progress.innerHTML=`<span>YOUR RESOLUTION PATH</span><b>${stateLabel}</b>${workflow.stage?`<small>Stage: ${escapeHtml(String(workflow.stage).replaceAll('_',' '))}</small>`:''}${total?`<small>${done} of ${total} required evidence checks ready · ${Number(readiness.percent||0)}%</small><i><em style="width:${Math.max(0,Math.min(100,Number(readiness.percent||0)))}%"></em></i>`:''}`;}
  if(stepsHost){const current=workflow.current_step||(hasAdaptive?null:steps[0]||null),remaining=steps.slice(1,5);stepsHost.innerHTML=current?`<article class="live-room-next-action"><span class="live-room-next-action-eyebrow">YOUR NEXT ACTION · STEP 1 OF ${Math.max(1,steps.length)}</span><h3>${escapeHtml(current.title||'Your next action')}</h3><p>${escapeHtml(current.detail||current.why||'Review this step before acting.')}</p>${current.why?`<details class="live-room-step-why"><summary>Why this matters</summary><small>${escapeHtml(current.why)}</small></details>`:''}${current.priority==='urgent'?'<span class="live-room-urgent-label">Time-sensitive</span>':''}</article>${remaining.length?`<details class="live-room-more-steps"><summary>See the next ${remaining.length} step${remaining.length===1?'':'s'}</summary><ol>${remaining.map(step=>`<li><b>${escapeHtml(step.title||'Next step')}</b><small>${escapeHtml(step.detail||step.why||'')}</small></li>`).join('')}</ol></details>`:''}`:'<div class="live-room-next-action"><span class="live-room-next-action-eyebrow">NEXT</span><h3>Tell us what happened</h3><p>Add one more detail or attach a relevant document. We will keep the plan tied to this case.</p></div>';}
  // When the adaptive workflow exists, it is authoritative even when its current question is intentionally null (story/update collection or an action stage). Never resurrect a stale legacy question.
  const q=hasAdaptive?workflow.next_question:resolution.next_question;
  if(questionHost){questionHost.hidden=!(q?.prompt&&Array.isArray(q.options)&&q.options.length);questionHost.innerHTML=questionHost.hidden?'':`<span class="live-room-question-eyebrow">ONE QUESTION THAT CAN CHANGE YOUR NEXT STEP</span><b>${escapeHtml(q.prompt)}</b>${q.why_it_matters?`<small>${escapeHtml(q.why_it_matters)}</small>`:''}<div class="live-room-question-options">${q.options.filter(option=>option.value!=='unknown').map(option=>`<button type="button" data-live-question-field="${escapeHtml(q.field||'')}" data-live-question-value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</button>`).join('')}</div><small class="live-room-question-boundary">Your answer updates this case's guidance. It does not check a bank or merchant account.</small>`;}
  const tasks=collecting?[]:(c.action_pack?.evidence_checklist||[]);const evidenceRequest=collecting?null:workflow.evidence_request;
  if(checklistHost){const taskMarkup=tasks.length?`<div class="live-room-checklist-heading"><div><span class="live-room-question-eyebrow">CASE-SPECIFIC DOCUMENT CHECKLIST</span><b>What may help this case</b></div><small>${tasks.filter(task=>task.checked).length}/${tasks.length} ready</small></div><div class="live-room-checklist-items">${tasks.map(task=>`<div class="live-room-checklist-item"><label><input type="checkbox" data-live-checklist-key="${escapeHtml(task.key)}" ${task.checked?'checked':''}><span><b>${escapeHtml(task.title)}</b><small>${escapeHtml(task.detail)}</small><em>${task.required?'Needed':'Helpful'}</em></span></label><button type="button" data-live-evidence-upload="${escapeHtml(task.key)}" aria-label="Add ${escapeHtml(task.title)}">＋ Add</button></div>`).join('')}</div>`:'';const requestMarkup=evidenceRequest?`<div class="live-room-evidence-request"><div><span class="live-room-question-eyebrow">EVIDENCE THAT MAY HELP NOW</span><b>${escapeHtml(evidenceRequest.title||'Add relevant proof')}</b><p>${escapeHtml(evidenceRequest.detail||'Add only evidence relevant to this step.')}</p></div><button type="button" class="button button-outline" data-live-evidence-upload="adaptive">＋ Add</button></div>`:'';checklistHost.innerHTML=taskMarkup+requestMarkup+(tasks.length||evidenceRequest?'<p class="live-room-checklist-note">Only add evidence relevant to this case. Hide unrelated personal details; never upload OTPs, PINs or passwords.</p>':'');}
  if(sources){const destinationLinks=(collecting?[]:(workflow.support_destinations||resolution.support_destinations||[])).slice(0,2).map(source=>{const url=safeHttpsUrl(source.url);return url?`<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer"><b>${escapeHtml(source.name||'Official support')}</b><span>${escapeHtml(source.action||source.label||'Open official support')} ↗</span></a>`:''}).join('');const policyLinks=(resolution.official_sources||[]).slice(0,3).map(source=>{const url=safeHttpsUrl(source.url);return url?`<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer"><b>${escapeHtml(source.organization||source.title||'Official source')}</b><span>${escapeHtml(source.title||'Review guidance')} ↗</span></a>`:''}).join('');sources.innerHTML=destinationLinks+policyLinks;}
  if(draftHost){const draft=collecting?{}:(workflow.support_draft||resolution.suggested_support_draft||{});draftHost.innerHTML=draft.message?`<div class="live-room-support-draft-card"><div><span class="live-room-question-eyebrow">READY-TO-EDIT SUPPORT MESSAGE</span><b>${escapeHtml(draft.subject||'Support follow-up')}</b></div><textarea id="liveRoomSupportDraftText" rows="7" aria-label="Editable support message">${escapeHtml(liveRoomSupportDraftEdited||draft.message)}</textarea><div class="live-room-support-draft-actions"><button type="button" class="button button-outline" data-live-copy-draft>Copy message</button><small>${escapeHtml(draft.notice||'Review and send it yourself through the official support channel.')}</small></div></div>`:'';}
  liveRoomApplyGuidanceOverride();
  const translated=$('#liveRoomGuidanceTranslation');if(translated&&(!liveRoomGuidanceOverride||liveRoomGuidanceOverride.case_id!==c.case_id)){translated.hidden=true;translated.innerHTML='';}
}
function liveRoomOpenExportDialog(){
  if(!activeCaseSnapshot?.case_id){showToast('Open a saved case before preparing an export.','error');return;}
  const host=$('#liveRoomExportEvidenceList'),dialog=$('#liveRoomExportDialog');
  const evidence=Array.isArray(activeCaseSnapshot.evidence)?activeCaseSnapshot.evidence:[];
  if(host)host.innerHTML=evidence.length?evidence.map((item,index)=>`<label class="blueprint-export-evidence-row"><input type="checkbox" data-export-evidence="${escapeHtml(item.evidence_id)}" checked><span><b>${escapeHtml(item.original_name||`Evidence ${index+1}`)}</b><small>${escapeHtml(item.mime_type||'File')} · ${escapeHtml(prettyDate(item.created_at))}</small></span></label>`).join(''):'<p>No original evidence files are attached to this case yet.</p>';
  const picker=$('#liveRoomExportEvidencePicker'),mode=$('input[name="liveRoomExportMode"]:checked')?.value||'complete';if(picker)picker.hidden=mode!=='share';
  if(typeof dialog?.showModal==='function')dialog.showModal();else showToast('This browser cannot open the export options.','error');
}
$('#liveRoomEvidenceBundleButton')?.addEventListener('click',liveRoomOpenExportDialog);
$$('input[name="liveRoomExportMode"]').forEach(input=>input.addEventListener('change',()=>{const picker=$('#liveRoomExportEvidencePicker');if(picker)picker.hidden=$('input[name="liveRoomExportMode"]:checked')?.value!=='share';}));
$('#liveRoomExportCancel')?.addEventListener('click',()=>$('#liveRoomExportDialog')?.close());
$('#liveRoomExportDownload')?.addEventListener('click',async()=>{
  const caseId=activeCaseSnapshot?.case_id;if(!caseId)return;
  const mode=$('input[name="liveRoomExportMode"]:checked')?.value||'complete';
  const params=new URLSearchParams({mode});
  if(mode==='share')params.set('include_evidence',$$('[data-export-evidence]:checked').map(input=>input.dataset.exportEvidence).join(','));
  if($('#liveRoomExportRedact')?.checked)params.set('redact_text','true');
  const button=$('#liveRoomExportDownload');button.disabled=true;button.textContent='Preparing ZIP…';
  try{const response=await api(`/api/cases/${encodeURIComponent(caseId)}/evidence-bundle.zip?${params.toString()}`);const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`BolKeResolve-${caseId}-${mode}-case.zip`;document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);$('#liveRoomExportDialog')?.close();showToast('Case archive prepared. Review the exported files before sharing.');}
  catch(error){showToast(error.message||'Could not prepare the case export.','error');}
  finally{button.disabled=false;button.textContent='Download ZIP archive ↗';}
});
$('#liveRoomBackToCaseButton')?.addEventListener('click',()=>{if(!liveRoomCaseId)return;currentCaseId=liveRoomCaseId;activeCaseTab='overview';showView('detail');});
$('#liveRoomMyCasesButton')?.addEventListener('click',()=>showView('cases'));
function liveRoomRenderFollowup(c){
  const follow=c?.follow_up||c?.action_pack?.follow_up||{},notice=$('#liveRoomFollowupNotice'),form=$('#liveRoomFollowupForm');
  if(form){form.hidden=false;const date=$('#liveRoomFollowupDate'),note=$('#liveRoomFollowupNote');if(date)date.value=follow.due_date||'';if(note)note.value=follow.note||'';}
  if(!notice)return;
  const status=c?.action_pack?.follow_up?.status||'';
  if(!follow.due_date){notice.hidden=true;notice.innerHTML='';return;}
  const label={overdue:'Follow-up is overdue',due_today:'Follow-up is due today',upcoming:'Follow-up is scheduled',completed:'Follow-up marked complete'}[status]||'Follow-up saved';
  notice.hidden=false;notice.innerHTML=`<span class="live-room-followup-status">${escapeHtml(label)}</span><b>${escapeHtml(follow.due_date)}</b>${follow.note?`<p>${escapeHtml(follow.note)}</p>`:''}${!follow.completed?'<button type="button" data-live-followup-complete>Mark complete</button>':''}`;
}
function renderLiveRoomCase(c){
  if(!c)return;
  liveRoomCaseId=c.case_id;currentCaseId=c.case_id;activeCaseSnapshot=c;
  $('#liveRoomCaseId').textContent=c.case_id;
  const caseState=`${[c.merchant,c.issue_type,money(c.amount)].filter(Boolean).join(' · ')} · ${c.case_stage||'Needs next step'}`;
  $('#liveRoomCaseState').textContent=caseState;
  const workspaceId=$('#liveRoomWorkspaceCaseId'),workspaceStatus=$('#liveRoomWorkspaceCaseStatus');if(workspaceId)workspaceId.textContent=c.case_id;if(workspaceStatus)workspaceStatus.textContent=caseState;
  $('#liveRoomOpenCaseButton').disabled=false;
  const printLink=$('#liveRoomPrintCaseButton'),bundleLink=$('#liveRoomEvidenceBundleButton');
  if(printLink){printLink.href=`/api/cases/${encodeURIComponent(c.case_id)}/passport/print`;printLink.hidden=false;}
  if(bundleLink)bundleLink.hidden=false;
  liveRoomRenderEvidence(c);
  if(!liveRoomGuidanceOverride||liveRoomGuidanceOverride.case_id!==c.case_id)liveRoomGuidanceOverride=liveRoomRestoreGuidanceFromTimeline(c);
  liveRoomRenderGuidance(c);
  liveRoomRenderFollowup(c);
}
async function liveRoomSaveUserTurn(text,languageCode,inputSource='typed'){
  if(!liveRoomCaseId)throw new Error('Your case could not be created. Please restart the session so your words and evidence can be saved.');
  const sourceMap={typed:'typed',voice:'live_speech',audio_import:'imported_call_recording',user_note:'user_note'};
  const result=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/live-room/turn`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,language_code:languageCode||'en-IN',session_id:liveRoomSessionId,input_source:sourceMap[inputSource]||'typed'})});
  renderLiveRoomCase(result);
  const savedTurn=[...(result.conversation_turns||[])].reverse().find(turn=>turn.speaker==='user'&&turn.session_id===liveRoomSessionId&&turn.input_source===(sourceMap[inputSource]||'typed'));
  const lastUserBubble=$$('.live-room-turn.user').at(-1);
  if(savedTurn&&lastUserBubble&&!lastUserBubble.querySelector('[data-edit-turn]')){lastUserBubble.dataset.turnId=savedTurn.turn_id;const edit=document.createElement('button');edit.type='button';edit.className='live-room-turn-edit';edit.dataset.editTurn=savedTurn.turn_id;edit.textContent='Edit transcript';lastUserBubble.append(edit);}
  return result;
}
function liveRoomRenderCaseAIStatus(used=null){
  liveRoomRenderConsentAvailability();
  const active=$('#liveRoomCaseAIActiveConsent');
  const status=$('#liveRoomCaseAIStatus');
  if(active){active.checked=!!liveRoomCaseAIConsent;active.disabled=!liveRoomCaseAIAvailable||!liveRoomCaseId;}
  if(!status)return;
  if(used===true){status.textContent='AI interpreted this update using the saved case context. The next action and official route still come from BolKeResolve’s reviewed workflow.';}
  else if(used===false&&liveRoomCaseAIConsent&&liveRoomCaseAIAvailable){status.textContent='AI interpretation was not used for this reply. The reviewed rule-based workflow remains active.';}
  else if(!liveRoomCaseAIAvailable){status.textContent='Case-understanding AI is not configured on this server. This case is using rule-based matching.';}
  else if(liveRoomCaseAIConsent){status.textContent='AI case understanding is enabled for this case. It interprets redacted saved text; raw audio and images are excluded.';}
  else{status.textContent='Case AI is off. Rule-based guidance remains available. You can enable AI understanding here at any time.';}
}
async function liveRoomUpdateCaseAIConsent(allowed){
  const checkbox=$('#liveRoomCaseAIActiveConsent');
  if(!liveRoomCaseId||!liveRoomCaseAIAvailable){if(checkbox)checkbox.checked=false;return;}
  const previous=liveRoomCaseAIConsent;
  if(checkbox)checkbox.disabled=true;
  try{
    const result=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/live-room/case-ai-consent`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({allowed:!!allowed,session_id:liveRoomSessionId})});
    liveRoomCaseAIConsent=!!result.allowed;
    const start=$('#liveRoomCaseAIConsent');if(start)start.checked=liveRoomCaseAIConsent;
    liveRoomRenderCaseAIStatus(null);
    showToast(liveRoomCaseAIConsent?'AI case understanding enabled for this case.':'AI case understanding turned off.','success');
  }catch(error){
    liveRoomCaseAIConsent=previous;
    if(checkbox)checkbox.checked=previous;
    liveRoomRenderCaseAIStatus(null);
    liveRoomFeedback(error.message||'We could not update the AI privacy setting.',true);
  }finally{if(checkbox)checkbox.disabled=!liveRoomCaseAIAvailable;}
}
async function liveRoomRequestGuidance(languageCode,options={}){
  const result=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/live-room/guidance`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({language_code:languageCode||'en-IN',session_id:liveRoomSessionId,finish_intake:!!options.finishIntake})});
  if(typeof result.case_interpretation_consent==='boolean')liveRoomCaseAIConsent=result.case_interpretation_consent;
  liveRoomRenderCaseAIStatus(!!result.case_interpretation_used);
  const labels={'hi-IN':'Hindi','hi-en':'Hinglish','mr-IN':'Marathi','bn-IN':'Bengali','gu-IN':'Gujarati','kn-IN':'Kannada','ml-IN':'Malayalam','pa-IN':'Punjabi','ta-IN':'Tamil','te-IN':'Telugu','en-IN':'English'};
  liveRoomGuidanceOverride=result.translation_status==='translated'?{case_id:liveRoomCaseId,guidance_text:String(result.guidance_text||''),language_code:result.language_code||'en-IN',language_label:labels[result.language_code]||result.language_code||'English'}:null;
  renderLiveRoomCase(result.case);liveRoomApplyGuidanceOverride();return result;
}
async function liveRoomCreateCaseFromStory(text,languageCode){
  // Drafts are created at session start. This guard remains for keyboard-only recovery.
  if(liveRoomCaseId)return liveRoomCaseId;
  const sessionId=liveRoomSessionId||`lr_${crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)}`;
  const result=await api('/api/live-room/cases',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({language_code:languageCode||'indic-auto',session_id:sessionId,started_at:liveRoomSessionStartedAt||new Date().toISOString()})});
  liveRoomCaseId=result.case_id;currentCaseId=result.case_id;liveRoomSessionStartRecorded=true;renderLiveRoomCase(result);await refreshCaseCountOnly();
  liveRoomFeedback(`Case ${result.case_id} created. Your conversation and evidence will be saved here as you go.`);
  return result.case_id;
}
function liveRoomQueueUserText(text,source='typed',languageCode=null){
  const run=()=>liveRoomProcessUserText(text,source,languageCode);
  liveRoomTurnQueue=liveRoomTurnQueue.then(run,run).catch(err=>{liveRoomFeedback(err.message||'We could not save that conversation turn.',true);});
  return liveRoomTurnQueue;
}
async function liveRoomProcessUserText(text,source='typed',languageCode=null){
  const clean=String(text||'').trim();if(clean.length<2)return;
  const lang=languageCode||liveRoomLanguageCode(clean);
  liveRoomTranscriptBubble('user',clean);
  // Short fillers/noise are visible in the transcript but must not trigger a
  // stale recommendation, model call, or voice response.
  if(liveRoomIsLowInformationUtterance(clean)){
    liveRoomAudioState('Still listening','I did not catch a new case detail. Keep speaking, type an update, or ask to show evidence.',liveRoomActive);
    liveRoomFeedback('No case action was triggered by that short utterance.');
    return {suppressAutoAdvance:true};
  }
  liveRoomAudioState('Updating your case','Saving what you said to this case…',false);
  liveRoomProcessing=true;
  try{
    await liveRoomCreateCaseFromStory(clean,lang);
    const saved=await liveRoomSaveUserTurn(clean,lang,source);
    const workflow=saved?.resolution?.adaptive_workflow||{};
    const captureIntent=liveRoomOfferCaptureFromIntent(clean);
    if(captureIntent){
      const captureMessages={camera:'Choose Open camera to show a document live, or Choose existing photo to attach one from your device.',file:'Choose the file you want to add. It will be saved as original evidence in this case.',screen:'Choose the relevant tab or window. After sharing starts, you can record a short clip if needed.',clip:'Start the recording when ready. You can stop it at any time.',stopped:'Capture stopped. Your saved case and evidence are unchanged.',};
      liveRoomAudioState('Evidence action ready',captureMessages[captureIntent]||'Choose the capture action shown in the conversation.',liveRoomActive);
      liveRoomFeedback(captureMessages[captureIntent]||'Your capture request is ready.');
      return {suppressAutoAdvance:true};
    }
    if(!workflow.intake_complete||workflow.collecting_update){
      const finish=$('#liveRoomFinishStoryButton');if(finish){finish.disabled=false;finish.textContent=workflow.collecting_update?'Finish update · Get next step':'Finish explaining · Build my next step';}
      liveRoomAudioState('Your story is saved','Keep explaining in your own words. Choose “Finish explaining” only when you are ready for the next step.',liveRoomActive);
      liveRoomFeedback('Saved to your case. I will wait until you finish explaining before recommending a route.');
      return;
    }
    const guidance=await liveRoomRequestGuidance(lang);
    const currentWorkflow=guidance?.workflow||guidance?.case?.resolution?.adaptive_workflow||saved?.resolution?.adaptive_workflow||workflow;
    const signature=liveRoomWorkflowSignature(currentWorkflow);
    const repeatedState=signature===liveRoomLastAssistantSignature;
    let guidanceText=liveRoomStructuredReply(currentWorkflow);
    if(repeatedState){
      guidanceText='I have saved this update. It does not change the next action yet. You do not need to repeat the earlier details. Add the evidence shown in your case plan, or tell me what changed or what support replied.';
    }else{
      liveRoomLastAssistantSignature=signature;
    }
    liveRoomTranscriptBubble('agent',guidanceText);
    liveRoomAudioState('Ready for your next detail','Your case has been updated. The next action and requested evidence are shown in your resolution plan.',liveRoomActive);
    const languageNote=guidance?.translation_status==='consent_required'?' Same-language guidance is available when you enable AI assistance.':guidance?.translation_status==='provider_not_configured'?' Same-language guidance is not configured on this server yet.':'';
    liveRoomFeedback('Your update is saved. The response above reflects the current case stage.'+languageNote);
    if(!repeatedState)liveRoomSpeak(guidanceText,guidance?.language_code||'en-IN').catch(()=>{});
  }catch(err){liveRoomFeedback(err.message||'We could not update your case.',true);liveRoomAudioState('Your message is still on screen','Try again or use the message box below.',liveRoomActive);}
  finally{liveRoomProcessing=false;}
}

async function liveRoomFinishStory({automatic=false}={}){
  if(!liveRoomCaseId)return;
  await liveRoomFlushSpeechBuffer({autoAdvance:false});
  await liveRoomTurnQueue;
  clearTimeout(liveRoomAutoAdvanceTimer);liveRoomAutoAdvanceTimer=null;
  if(automatic&&liveRoomProcessing){await liveRoomTurnQueue;}
  const button=$('#liveRoomFinishStoryButton');if(button&&!automatic){button.disabled=true;button.textContent='Building your next step…';}
  try{
    const guidance=await liveRoomRequestGuidance(liveRoomLanguageCode(),{finishIntake:true});
    const workflow=guidance?.workflow||guidance?.case?.resolution?.adaptive_workflow||activeCaseSnapshot?.resolution?.adaptive_workflow||{};
    const signature=liveRoomWorkflowSignature(workflow);
    const repeatedState=signature===liveRoomLastAssistantSignature;
    const text=repeatedState
      ? 'Your case plan is already up to date. Continue with the current question or add the evidence shown on the right.'
      : (liveRoomStructuredReply(workflow)||guidance?.guidance_text||'Your story is saved. Please answer the next question shown in your case plan.');
    liveRoomLastAssistantSignature=signature;
    liveRoomTranscriptBubble('agent',text);
    liveRoomAudioState('Your case has been understood','Answer the one question shown on the right, or add the specific evidence requested.',liveRoomActive);
    liveRoomFeedback(automatic?'You paused after explaining. I have prepared the next question from your full story.':'Your full story has been reviewed. The next question is based on the details you provided.');
    if(!repeatedState)liveRoomSpeak(text,guidance?.language_code||'en-IN').catch(()=>{});
  }catch(error){liveRoomFeedback(error.message||'We could not build the next step.',true);}
  finally{if(button&&!automatic){button.disabled=false;button.textContent='Update my case · Get next step';}}
}
async function liveRoomSpeak(text,lang){
  if(!text||!navigator.onLine)return;
  const language=(lang==='hi-IN'&&/[A-Za-z]/.test(text)&&!window.bolkeTimbreV3)?'hi-en':(lang==='indic-auto'?'en-IN':lang);
  const audioTracks=liveRoomStream?.getAudioTracks()||[];const priorEnabled=audioTracks.map(track=>track.enabled);audioTracks.forEach(track=>track.enabled=false);try{const response=await api('/api/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,language_code:language})});const blob=await response.blob();if(!blob.size)return;const url=URL.createObjectURL(blob),audio=new Audio(url);audio.addEventListener('ended',()=>URL.revokeObjectURL(url),{once:true});await audio.play();await new Promise(resolve=>{audio.addEventListener('ended',resolve,{once:true});audio.addEventListener('error',resolve,{once:true});});}catch(_){/* Voice output is optional; the guidance remains visible and saved. */}finally{audioTracks.forEach((track,index)=>track.enabled=priorEnabled[index]&&!liveRoomMuted);}
}
async function liveRoomPopulateMicDevices(){
  const select=$('#liveRoomMicDevice');if(!select||!navigator.mediaDevices?.enumerateDevices)return;
  try{
    const current=select.value;
    const devices=(await navigator.mediaDevices.enumerateDevices()).filter(device=>device.kind==='audioinput');
    const options=[{deviceId:'',label:'System default microphone'},...devices.map((device,index)=>({deviceId:device.deviceId,label:device.label||`Microphone ${index+1}`}))];
    select.innerHTML=options.map(item=>`<option value="${escapeHtml(item.deviceId)}">${escapeHtml(item.label)}</option>`).join('');
    if(options.some(item=>item.deviceId===current))select.value=current;
  }catch(_){/* device names are optional; the system default remains available */}
}
async function liveRoomRestartVoice(){
  if(!liveRoomActive)throw new Error('Start a live case before restarting voice.');
  await liveRoomFlushSpeechBuffer({autoAdvance:false});
  clearTimeout(liveRoomReconnectTimer);liveRoomReconnectTimer=null;clearTimeout(liveRoomTranscriptionTimer);liveRoomTranscriptionTimer=null;
  const oldSocket=liveRoomSocket;liveRoomSocket=null;
  try{oldSocket?.close(1000,'User restarted voice');}catch(_){}
  liveRoomReconnectAttempts=0;liveRoomAudioFrameCount=0;liveRoomAudioSignalSeen=false;liveRoomMicLevel(0);
  const retry=$('#liveRoomRetryVoiceButton');if(retry)retry.hidden=true;
  liveRoomStatus('Reconnecting voice');liveRoomAudioState('Restarting microphone','Reconnecting to the speech service. Your saved case and evidence are unchanged.',false);
  await liveRoomStartAudioPipeline();
}
async function liveRoomResetAudioGraph(){
  try{liveRoomWorklet?.disconnect();liveRoomAudioSource?.disconnect();liveRoomGain?.disconnect();}catch(_){}
  try{await liveRoomAudioContext?.close();}catch(_){}
  liveRoomWorklet=null;liveRoomAudioSource=null;liveRoomGain=null;liveRoomAudioContext=null;
}
async function liveRoomApplyMicSettings(){
  if(!liveRoomActive)throw new Error('Start a live case before changing microphone settings.');
  const selectedDevice=$('#liveRoomMicDevice')?.value||'';
  const oldAudio=liveRoomStream?.getAudioTracks()||[];
  const audioConstraints={echoCancellation:true,noiseSuppression:true,autoGainControl:true,channelCount:{ideal:1}};
  if(selectedDevice)audioConstraints.deviceId={exact:selectedDevice};
  const replacement=await navigator.mediaDevices.getUserMedia({audio:audioConstraints,video:false});
  const videoTracks=liveRoomStream?.getVideoTracks()||[];
  const replacementTracks=replacement.getAudioTracks();
  if(!replacementTracks.length){liveRoomStopTracks(replacement);throw new Error('The selected input did not provide an audio track. Choose another microphone.');}
  const next=new MediaStream([...replacementTracks,...videoTracks]);
  const oldSocket=liveRoomSocket;liveRoomSocket=null;try{oldSocket?.close(1000,'Microphone input changed');}catch(_){}
  await liveRoomResetAudioGraph();
  oldAudio.forEach(track=>{try{track.stop();}catch(_){}});
  liveRoomStream=next;liveRoomMuted=false;
  const micButton=$('#liveRoomMicToggle');if(micButton){micButton.disabled=false;micButton.textContent='Mic on';micButton.setAttribute('aria-pressed','true');}
  await liveRoomPopulateMicDevices();
  await liveRoomRestartVoice();
  const settings=$('.live-room-voice-settings');if(settings)settings.open=false;
  liveRoomFeedback('Microphone settings applied. Speak a short sentence and pause so the transcript can arrive.');
}
function liveRoomVideoHasVisibleImage(video){
  if(!video||video.videoWidth<2||video.videoHeight<2)return false;
  try{
    const canvas=document.createElement('canvas');canvas.width=16;canvas.height=9;
    const context=canvas.getContext('2d',{willReadFrequently:true});context.drawImage(video,0,0,16,9);
    const pixels=context.getImageData(0,0,16,9).data;let visible=0;
    for(let i=0;i<pixels.length;i+=4){if(pixels[i]+pixels[i+1]+pixels[i+2]>20)visible++;}
    return visible>=4;
  }catch(_){return false;}
}
async function liveRoomWaitForVideoFrame(video,timeoutMs=5000){
  if(!video)return false;
  return new Promise(resolve=>{
    let settled=false;const finish=value=>{if(settled)return;settled=true;clearTimeout(timer);clearInterval(poll);video.removeEventListener('loadeddata',onFrame);video.removeEventListener('canplay',onFrame);resolve(Boolean(value&&video.videoWidth>0&&video.videoHeight>0&&liveRoomVideoHasVisibleImage(video)));};
    const check=()=>{if(video.readyState>=2&&video.videoWidth>0&&video.videoHeight>0&&liveRoomVideoHasVisibleImage(video))finish(true);};
    const onFrame=()=>check();const timer=setTimeout(()=>finish(false),timeoutMs);const poll=setInterval(check,250);
    video.addEventListener('loadeddata',onFrame);video.addEventListener('canplay',onFrame);check();
  });
}
function liveRoomClearPauseTimers(){
  clearTimeout(liveRoomSilenceCommitTimer);liveRoomSilenceCommitTimer=null;
  clearTimeout(liveRoomAutoAdvanceTimer);liveRoomAutoAdvanceTimer=null;
}
function liveRoomScheduleAutoAdvance(){
  clearTimeout(liveRoomAutoAdvanceTimer);
  // After a transcript has been saved, briefly wait for another sentence.
  // If the user stays silent, build the next question without requiring a button.
  liveRoomAutoAdvanceTimer=setTimeout(async()=>{
    liveRoomAutoAdvanceTimer=null;
    try{
      await liveRoomTurnQueue;
      const workflow=activeCaseSnapshot?.resolution?.adaptive_workflow||{};
      if(liveRoomActive&&liveRoomCaseId&&(!workflow.intake_complete||workflow.collecting_update)){
        await liveRoomFinishStory({automatic:true});
      }
    }catch(error){liveRoomFeedback(error.message||'The next step could not be prepared automatically.',true);}
  },1400);
}
async function liveRoomFlushSpeechBuffer({autoAdvance=true}={}){
  clearTimeout(liveRoomSpeechFlushTimer);liveRoomSpeechFlushTimer=null;
  const text=liveRoomPendingSpeechText.trim();const language=liveRoomPendingSpeechLanguage||liveRoomLanguageCode(text);
  liveRoomPendingSpeechText='';liveRoomPendingSpeechLanguage='';
  if(!text)return;
  const turnResult=await liveRoomQueueUserText(text,'voice',language);
  if(autoAdvance&&!turnResult?.suppressAutoAdvance){
    const workflow=activeCaseSnapshot?.resolution?.adaptive_workflow||{};
    if(liveRoomActive&&(!workflow.intake_complete||workflow.collecting_update))liveRoomScheduleAutoAdvance();
  }
}
function liveRoomQueueSpeechSegment(text,languageCode){
  const clean=String(text||'').trim();if(!clean)return;
  liveRoomPendingSpeechText=[liveRoomPendingSpeechText,clean].filter(Boolean).join(' ').replace(/\s+/g,' ').trim();
  liveRoomPendingSpeechLanguage=languageCode||liveRoomPendingSpeechLanguage||'en-IN';
  clearTimeout(liveRoomSpeechFlushTimer);
  // Gnani may close multiple segments around natural pauses. Combine nearby
  // segments into one user turn so a mid-sentence pause cannot advance the
  // question before the rest of the answer arrives.
  liveRoomSpeechFlushTimer=setTimeout(()=>{liveRoomFlushSpeechBuffer().catch(error=>liveRoomFeedback(error.message||'Your speech could not be saved.',true));},1400);
}
function liveRoomHandleLocalSilence(rms){
  const now=performance.now();
  const profile=$('#liveRoomMicProfile')?.value||'laptop';
  const threshold=profile==='quiet'?0.0055:profile==='noisy'?0.012:0.0075;
  if(rms>=threshold){
    if(!liveRoomSpeechStartedAt)liveRoomSpeechStartedAt=now;
    liveRoomLastVoiceAt=now;liveRoomCommitSent=false;
    clearTimeout(liveRoomSilenceCommitTimer);liveRoomSilenceCommitTimer=null;
    clearTimeout(liveRoomAutoAdvanceTimer);liveRoomAutoAdvanceTimer=null;
    return;
  }
  if(!liveRoomSpeechStartedAt||liveRoomCommitSent||liveRoomSilenceCommitTimer)return;
  liveRoomSilenceCommitTimer=setTimeout(()=>{
    liveRoomSilenceCommitTimer=null;
    const silentFor=performance.now()-liveRoomLastVoiceAt;
    const speechFor=liveRoomLastVoiceAt-liveRoomSpeechStartedAt;
    if(!liveRoomActive||!liveRoomSocket||liveRoomSocket.readyState!==WebSocket.OPEN||silentFor<900||speechFor<300||liveRoomCommitSent)return;
    try{
      liveRoomSocket.send(JSON.stringify({type:'commit'}));liveRoomCommitSent=true;
      liveRoomAudioState('Pause detected','Finishing your sentence and preparing the transcript…',false);
      liveRoomFeedback('I detected a pause and sent your speech for transcription.');
    }catch(error){liveRoomFeedback(error.message||'Could not finish the speech turn automatically. You can still use Finish speaking.',true);}
  },1000);
}
function liveRoomHandleProviderMessage(raw){
  let message;try{message=JSON.parse(raw);}catch(_){return;}
  if(message.type==='connected'){
    liveRoomReconnectAttempts=0;
    const configuredRate=Number(message.sample_rate||message.config?.sample_rate||0);
    liveRoomStatus('Speech service connected',true);const retry=$('#liveRoomRetryVoiceButton');if(retry)retry.hidden=true;
    liveRoomAudioState('Microphone stream starting',configuredRate?`Gnani connected at ${configuredRate/1000} kHz. Speak when the microphone meter moves.`:'Gnani connected. Starting the microphone stream…',false);
    return;
  }
  if(message.type==='speech_start'){
    clearTimeout(liveRoomAutoAdvanceTimer);
    if(!liveRoomSpeechStartedAt)liveRoomSpeechStartedAt=performance.now();
    clearTimeout(liveRoomTranscriptionTimer);liveRoomSpeechProcessingAt=Date.now();
    liveRoomAudioState('I can hear you','Speech detected. Pause when you finish a thought.',true);
    // Watch from the first provider speech event, not only from `processing`.
    // Some rejected/unsupported auto-LID sessions never emit `processing`, so
    // without this the user can wait forever despite the microphone meter moving.
    liveRoomTranscriptionTimer=setTimeout(()=>{
      if(!liveRoomActive||!liveRoomSpeechProcessingAt)return;
      liveRoomAudioState('No transcript yet','The microphone reached the speech service, but no words came back. Your case is safe; retry voice or use a saved voice note.',false);
      liveRoomFeedback('The speech service heard a speech segment but did not return text. Automatic detection uses Prisma v3.0. Check that this API key has v3 access, then restart voice or use Record voice note as a fallback. Your case is still saved.',true);
      const retry=$('#liveRoomRetryVoiceButton');if(retry)retry.hidden=false;
    },30000);
    return;
  }
  if(message.type==='processing'){
    // Provider VAD has already closed this segment; cancel the browser-side
    // fallback commit so it cannot send a second end-of-utterance frame.
    clearTimeout(liveRoomSilenceCommitTimer);liveRoomSilenceCommitTimer=null;liveRoomCommitSent=true;
    clearTimeout(liveRoomTranscriptionTimer);liveRoomSpeechProcessingAt=Date.now();
    liveRoomAudioState('Transcribing your words','Gnani received a speech segment. Your transcript will appear here shortly…',false);
    liveRoomTranscriptionTimer=setTimeout(()=>{
      if(!liveRoomActive||!liveRoomSpeechProcessingAt)return;
      liveRoomAudioState('Transcript is taking longer than expected','Your audio reached the speech service, but no text has arrived yet. Try a shorter sentence or choose another microphone profile.',false);
      liveRoomFeedback('No transcript arrived after the speech service acknowledged your audio. Automatic language detection requires Prisma v3.0 access. Check that your API key has it, then restart voice or use Record voice note. Your case is still saved.',true);
      const retry=$('#liveRoomRetryVoiceButton');if(retry)retry.hidden=false;
    },12000);
    return;
  }
  if(message.type==='error'){
    clearTimeout(liveRoomTranscriptionTimer);liveRoomSpeechProcessingAt=0;
    liveRoomStatus('Speech needs attention',false);
    liveRoomAudioState('Live transcription stopped','Your case and captured evidence are safe. Check the message below, adjust Mic settings, or use the typed message box.',false);
    const code=String(message.code||message.error_code||'').trim();
    const detail=String(message.message||message.detail||'The speech provider could not transcribe this audio.').trim();
    liveRoomFeedback(`${code?`Gnani error ${code}: `:''}${detail} You can restart voice or type instead.`,true);
    const retry=$('#liveRoomRetryVoiceButton');if(retry)retry.hidden=false;
    try{liveRoomSocket?.close(4403,'Speech provider returned an error');}catch(_){}
    return;
  }
  if(message.type==='transcript'&&message.is_final!==false){
    liveRoomClearPauseTimers();liveRoomSpeechStartedAt=0;liveRoomLastVoiceAt=0;liveRoomCommitSent=false;
    clearTimeout(liveRoomTranscriptionTimer);liveRoomTranscriptionTimer=null;liveRoomSpeechProcessingAt=0;
    const segmentId=String(message.segment_id||message.utterance_id||'');
    if(segmentId&&liveRoomSegmentIds.has(segmentId))return;
    if(segmentId){liveRoomSegmentIds.add(segmentId);if(liveRoomSegmentIds.size>500)liveRoomSegmentIds.delete(liveRoomSegmentIds.values().next().value);}
    const text=String(message.text||'').trim();
    if(text){const retry=$('#liveRoomRetryVoiceButton');if(retry)retry.hidden=true;liveRoomAudioState('Transcript received','Saving your words to the case and preparing the next step…',false);const detected=liveRoomNormalizeLanguageCode(message.detected_language_code);const language=detected||liveRoomLanguageCode(text);liveRoomQueueSpeechSegment(text,language);const mode=$('#liveRoomLanguageModeLabel');if(mode)mode.textContent=detected?`Detected language: ${languageNames[detected]||detected}`:`Language inferred from transcript: ${languageNames[language]||'English / India'}`;}
  }
}
async function liveRoomStartAudioPipeline(){
  const audioTrack=liveRoomStream?.getAudioTracks().find(track=>track.readyState==='live');
  if(!audioTrack){liveRoomStatus('Text and evidence mode');liveRoomAudioState('Microphone unavailable','You can still type and save evidence. Check the browser microphone permission to use voice.',false);return;}
  if(liveRoomSocket&&[WebSocket.OPEN,WebSocket.CONNECTING].includes(liveRoomSocket.readyState))return;
  const selected=$('#liveRoomLanguage')?.value||'indic-auto';
  const voiceProfile=$('#liveRoomMicProfile')?.value||'laptop';
  const AudioContextClass=window.AudioContext||window.webkitAudioContext;
  if(!AudioContextClass)throw new Error('This browser does not support live audio. Use Chrome or Edge, or type instead.');
  // Keep one audio pipeline alive across temporary WebSocket reconnects. The
  // worklet emits raw 512-sample frames at the actual AudioContext sample rate.
  if(!liveRoomAudioContext||liveRoomAudioContext.state==='closed'){
    liveRoomAudioContext=new AudioContextClass({latencyHint:'interactive'});
    await liveRoomAudioContext.resume();
    const sampleRate=Number(liveRoomAudioContext.sampleRate||48000);
    if(![16000,44100,48000].includes(sampleRate))throw new Error(`Your browser audio runs at ${sampleRate} Hz, which is not supported for live transcription. Try Chrome/Edge or use typing.`);
    if(!liveRoomAudioContext.audioWorklet)throw new Error('This browser does not support the live audio processor. Use Chrome or Edge, or type instead.');
    await liveRoomAudioContext.audioWorklet.addModule('/live-pcm-processor.js');
    liveRoomAudioSource=liveRoomAudioContext.createMediaStreamSource(new MediaStream([audioTrack]));
    liveRoomWorklet=new AudioWorkletNode(liveRoomAudioContext,'bolke-pcm-processor');
    liveRoomGain=liveRoomAudioContext.createGain();liveRoomGain.gain.value=0;
    liveRoomAudioFrameCount=0;liveRoomAudioSignalSeen=false;liveRoomMicLevel(0);
    liveRoomWorklet.port.onmessage=event=>{
      const samples=event.data;
      if(!(samples instanceof Float32Array)||samples.length!==512){liveRoomFeedback('The microphone produced an unexpected audio frame. Restart voice or type instead.',true);return;}
      let sum=0;for(let i=0;i<samples.length;i++)sum+=samples[i]*samples[i];
      const rms=Math.sqrt(sum/samples.length);liveRoomMicLevel(rms);liveRoomHandleLocalSilence(rms);
      if(!liveRoomSocket||liveRoomSocket.readyState!==WebSocket.OPEN||liveRoomMuted)return;
      const pcm=new ArrayBuffer(1024),view=new DataView(pcm);
      for(let i=0;i<512;i++){const sample=Math.max(-1,Math.min(1,samples[i]));view.setInt16(i*2,sample<0?sample*32768:sample*32767,true);}
      liveRoomSocket.send(pcm);liveRoomAudioFrameCount++;
      if(liveRoomAudioFrameCount===1){const retry=$('#liveRoomRetryVoiceButton');if(retry)retry.hidden=true;liveRoomStatus(`Microphone streaming · ${(liveRoomAudioContext.sampleRate/1000).toFixed(liveRoomAudioContext.sampleRate%1000?1:0)} kHz`,true);liveRoomAudioState('Listening to you','Your voice is being streamed for transcription. Pause when you finish a thought.',true);}
    };
    liveRoomAudioSource.connect(liveRoomWorklet);liveRoomWorklet.connect(liveRoomGain);liveRoomGain.connect(liveRoomAudioContext.destination);
  }else{
    await liveRoomAudioContext.resume();
  }
  const sampleRate=Number(liveRoomAudioContext.sampleRate||48000);
  // Obtain a one-use ticket through the same-origin API (the HttpOnly session
  // cookie never enters JavaScript), then connect directly to Render. Vercel
  // static rewrites do not reliably proxy WebSocket upgrade requests.
  const authorization=await api('/api/live-room/voice-ticket',{method:'POST'});
  if(!authorization?.ticket)throw new Error('The server did not authorize live voice. Sign in again or continue by typing.');
  const socketUrl=new URL('wss://bolkeresolve.onrender.com/api/live-room/voice');
  socketUrl.searchParams.set('ticket',authorization.ticket);
  socketUrl.searchParams.set('language_code',selected);
  socketUrl.searchParams.set('sample_rate',String(sampleRate));
  socketUrl.searchParams.set('voice_profile',voiceProfile);
  const socket=new WebSocket(socketUrl.toString());liveRoomSocket=socket;socket.binaryType='arraybuffer';
  socket.addEventListener('message',event=>liveRoomHandleProviderMessage(event.data));
  socket.addEventListener('open',()=>{
    const finishButton=$('#liveRoomFinishSpeakingButton');if(finishButton)finishButton.disabled=false;
    liveRoomAudioFrameCount=0;liveRoomStatus('Speech service connected · checking mic',true);
    liveRoomAudioState('Microphone connected','Speak a short sentence. The meter must move before Gnani can receive your voice.',false);
    setTimeout(()=>{
      if(liveRoomActive&&socket===liveRoomSocket&&socket.readyState===WebSocket.OPEN&&liveRoomAudioFrameCount===0){
        liveRoomStatus('Microphone not streaming',false);
        liveRoomAudioState('No microphone audio is reaching the speech service','Check the selected input device and the browser/Windows microphone privacy permission. You can type while you check.',false);
        liveRoomFeedback('The speech service connected, but the browser sent no audio frames. Check Chrome site permissions and Windows microphone access.',true);
      }
    },3500);
    setTimeout(()=>{
      if(liveRoomActive&&socket===liveRoomSocket&&socket.readyState===WebSocket.OPEN&&liveRoomAudioFrameCount>10&&!liveRoomAudioSignalSeen){
        liveRoomAudioState('Microphone is very quiet','Audio frames are arriving, but the input level is low. Move closer to the microphone or choose another input device.',false);
        liveRoomFeedback('The microphone is sending audio frames, but the signal is very quiet. Check the input selected by Chrome.',true);
      }
    },10000);
  });
  socket.addEventListener('close',event=>{
    const finishButton=$('#liveRoomFinishSpeakingButton');if(finishButton)finishButton.disabled=true;
    if(!liveRoomActive||socket!==liveRoomSocket)return;
    if(event.code===4401){liveRoomStatus('Sign-in required');liveRoomAudioState('Voice needs sign-in','Your saved case and evidence remain safe.');return;}
    if(event.code===4403){liveRoomStatus('Voice needs attention');liveRoomAudioState('Speech provider rejected the stream','Your case is saved. Check the exact provider error above, then adjust Mic settings or restart voice.',false);const retry=$('#liveRoomRetryVoiceButton');if(retry)retry.hidden=false;return;}
    if(event.code===4429){liveRoomStatus('Voice limit reached');liveRoomAudioState('Please wait before reconnecting','Your case is saved. You can continue by typing or adding evidence.',false);liveRoomFeedback('The live speech usage limit was reached. Wait a minute before starting voice again.',true);return;}
    liveRoomStatus('Reconnecting voice');liveRoomAudioState('Reconnecting to speech','Your case is safe. You can keep typing or adding evidence meanwhile.',false);
    if(liveRoomReconnectAttempts<5){clearTimeout(liveRoomReconnectTimer);const delay=Math.min(8000,1000*Math.pow(2,liveRoomReconnectAttempts++));liveRoomReconnectTimer=setTimeout(()=>{if(liveRoomActive&&liveRoomStream?.getAudioTracks().some(track=>track.enabled))liveRoomStartAudioPipeline().catch(err=>liveRoomFeedback(err.message,true));},delay);}
    else{liveRoomStatus('Text and evidence mode');liveRoomAudioState('Voice temporarily unavailable','Continue by typing or attaching evidence.',false);liveRoomFeedback('Live speech could not reconnect after several attempts. Your saved case is safe; continue by typing or restart the voice connection.',true);}
  });
  socket.addEventListener('error',()=>{liveRoomStatus('Speech connection error');liveRoomFeedback('Live speech connection reported an error. Check the provider setup; typed input and evidence uploads remain available.',true);});
}
function liveRoomRestoreConversation(c){
  const host=$('#liveRoomTranscript');if(!host)return;
  host.innerHTML='';
  const structured=Array.isArray(c?.conversation_turns)?c.conversation_turns:[];
  const timeline=Array.isArray(c?.timeline)?c.timeline:[];
  const events=[];
  if(structured.length){
    const superseded=new Set(structured.map(turn=>turn.supersedes_turn_id).filter(Boolean));
    for(const turn of structured){
      if(superseded.has(turn.turn_id))continue;
      const text=String(turn.text||'').trim();if(!text)continue;
      events.push({kind:'turn',speaker:turn.speaker||'user',text,created_at:turn.created_at||'',turnId:turn.turn_id});
    }
  }else{
    for(const event of timeline){
      if(event.event_type!=='live_room_user_turn')continue;
      const text=String(event.message||'').replace(/^User said:\s*/,'').trim();
      if(text)events.push({kind:'turn',speaker:'user',text,created_at:event.created_at||''});
    }
  }
  // Assistant guidance is stored as timeline events. Merge it with structured user
  // turns so correcting a transcript never hides the assistant's earlier guidance.
  for(const event of timeline){
    if(event.event_type!=='live_room_agent_guidance')continue;
    const text=String(event.message||'').replace(/^BolKeResolve guidance:\s*/,'').trim();
    if(text)events.push({kind:'guidance',speaker:'agent',text,created_at:event.created_at||''});
  }
  events.sort((a,b)=>String(a.created_at).localeCompare(String(b.created_at)));
  const displayedGuidance=new Set();
  for(const item of events){
    if(item.kind==='guidance'){
      const fingerprint=item.text.replace(/\s+/g,' ').toLocaleLowerCase();
      if(displayedGuidance.has(fingerprint))continue;
      displayedGuidance.add(fingerprint);
    }
    const role=item.speaker==='organisation'?'organisation':item.speaker==='user'?'user':'agent';
    liveRoomTranscriptBubble(role,item.text,item.turnId?{turnId:item.turnId}:undefined);
  }
}

let liveRoomEditingTurnId='';
$('#liveRoomTranscript')?.addEventListener('click',event=>{
  const button=event.target.closest('[data-edit-turn]');if(!button)return;
  const turn=(activeCaseSnapshot?.conversation_turns||[]).find(item=>item.turn_id===button.dataset.editTurn);if(!turn)return;
  liveRoomEditingTurnId=turn.turn_id;$('#liveRoomTranscriptEditText').value=turn.text||'';
  const dialog=$('#liveRoomTranscriptEditDialog');if(typeof dialog?.showModal==='function')dialog.showModal();else showToast('Transcript editing is not supported in this browser.','error');
});
$('#liveRoomTranscriptEditCancel')?.addEventListener('click',()=>$('#liveRoomTranscriptEditDialog')?.close());
$('#liveRoomTranscriptEditForm')?.addEventListener('submit',async event=>{
  event.preventDefault();if(!liveRoomEditingTurnId||!liveRoomCaseId)return;
  const text=$('#liveRoomTranscriptEditText').value.trim(),button=$('#liveRoomTranscriptEditSave');if(text.length<2){showToast('Add a little more detail before saving the correction.','error');return;}
  button.disabled=true;button.textContent='Saving correction…';
  try{const result=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/conversation-turns/${encodeURIComponent(liveRoomEditingTurnId)}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});renderLiveRoomCase(result.case);liveRoomRestoreConversation(result.case);$('#liveRoomTranscriptEditDialog')?.close();liveRoomEditingTurnId='';showToast('Correction saved. The earlier transcript version remains in the case history.');}
  catch(error){showToast(error.message||'Could not save the transcript correction.','error');}
  finally{button.disabled=false;button.textContent='Save correction';}
});
$('#liveRoomTranscriptEditDialog')?.addEventListener('click',event=>{if(event.target===$('#liveRoomTranscriptEditDialog'))$('#liveRoomTranscriptEditDialog').close();});
async function startLiveRoom(existingCaseId=null){
  // Defensive guard: DOM click handlers receive an Event object. Only an actual
  // case ID string may select the resume-existing-case path.
  if(typeof existingCaseId!=='string')existingCaseId=null;
  const button=$('#liveRoomStartButton');if(liveRoomActive)return;
  if(!window.isSecureContext||!navigator.mediaDevices){liveRoomFeedback('Camera and microphone require HTTPS or localhost. You can still type or upload evidence from the standard case form.',true);return;}
  if(authRequired&&!signedInUser){pendingAuthAction='live-room';showAuthGate('Sign in to keep your conversation and evidence in a private case.');return;}
  button.disabled=true;button.textContent=existingCaseId?'Opening your case…':'Creating your case…';liveRoomFeedback(existingCaseId?'Reopening your existing case. New notes and evidence will be added to the same record.':'Creating a private draft case first, so nothing you capture is left waiting in this page.');
  try{
    if(existingCaseId)showView('liveRoom');
    liveRoomCaseId=null;liveRoomSessionStartRecorded=false;liveRoomMuted=false;liveRoomSegmentIds.clear();liveRoomPendingReviewId='';liveRoomReconnectAttempts=0;liveRoomSupportDraftEdited='';clearTimeout(liveRoomReconnectTimer);
    liveRoomSessionId=`lr_${crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)}`;liveRoomSessionStartedAt=new Date().toISOString();
    const selected=$('#liveRoomLanguage')?.value||'indic-auto';const selectedLanguage=selected;const modeLabel=$('#liveRoomLanguageModeLabel');if(modeLabel)modeLabel.textContent=selected==='indic-auto'?'Automatic language detection':`Preferred language: ${$('#liveRoomLanguage').selectedOptions[0]?.textContent||selected}`;
    let draft;
    if(existingCaseId){
      draft=await api(`/api/cases/${encodeURIComponent(existingCaseId)}`);
      liveRoomAiConsent=!!$('#liveRoomAiConsent')?.checked;liveRoomCaseAIConsent=!!$('#liveRoomCaseAIConsent')?.checked;liveRoomGuidanceOverride=null;liveRoomCaseId=draft.case_id;currentCaseId=draft.case_id;
      await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/live-room/case-ai-consent`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({allowed:liveRoomCaseAIConsent,session_id:liveRoomSessionId})});
      // Migrate older cases first, then mark the session as collecting a new update.
      if(!draft.resolution?.adaptive_workflow && String(draft.description||'').length>10){
        try{const migrated=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/live-room/guidance`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({language_code:selectedLanguage,session_id:liveRoomSessionId,finish_intake:true})});draft=migrated.case||draft;}catch(error){console.warn('Legacy case workflow migration deferred',error);}
      }
      draft=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/live-room/session-event`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event:'started',session_id:liveRoomSessionId,started_at:liveRoomSessionStartedAt})});
      liveRoomSessionStartRecorded=true;
    }else{
      draft=await api('/api/live-room/cases',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({language_code:selectedLanguage,session_id:liveRoomSessionId,started_at:liveRoomSessionStartedAt,allow_ai_assistance:!!$('#liveRoomAiConsent')?.checked,allow_ai_case_interpretation:!!$('#liveRoomCaseAIConsent')?.checked})});
      liveRoomAiConsent=!!$('#liveRoomAiConsent')?.checked;liveRoomCaseAIConsent=!!$('#liveRoomCaseAIConsent')?.checked;liveRoomGuidanceOverride=null;liveRoomCaseId=draft.case_id;currentCaseId=draft.case_id;liveRoomSessionStartRecorded=true;
    }
    renderLiveRoomCase(draft);liveRoomRenderCaseAIStatus(null);liveRoomLastAssistantSignature=liveRoomWorkflowSignature(draft?.resolution?.adaptive_workflow||{});if(existingCaseId)liveRoomRestoreConversation(draft);await refreshCaseCountOnly();
    const finishStoryButton=$('#liveRoomFinishStoryButton');
    if(finishStoryButton){const hasPriorStory=Boolean((draft.description||'').length>30)||(draft.timeline||[]).some(event=>event.event_type==='live_room_user_turn');finishStoryButton.disabled=!hasPriorStory;finishStoryButton.textContent=draft.resolution?.adaptive_workflow?.intake_complete?'Finish update · Get next step':'Finish explaining · Build my next step';}
    $('#liveRoomStart').hidden=true;$('#liveRoomWorkspace').hidden=false;
    let audioStream=null;
    // Ask for microphone access only. Camera and screen permissions are requested
    // after the user asks to show evidence or chooses a capture action.
    try{audioStream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});}catch(audioError){liveRoomFeedback('Microphone access was not granted. Your case is safe; you can type or add evidence, and turn the microphone on later.',true);}
    liveRoomStream=new MediaStream([...(audioStream?.getTracks?.()||[])]);
    const camera=$('#liveRoomCameraPreview');if(camera){camera.srcObject=null;camera.hidden=true;}
    $('#liveRoomCameraPlaceholder').hidden=false;
    $('#liveRoomCameraPlaceholder').querySelector('b').textContent='Camera is off';
    $('#liveRoomCameraPlaceholder').querySelector('small').textContent='Camera starts only when you ask to show or capture a document.';
    $('#liveRoomCameraLabel').textContent='Camera off · optional';
    liveRoomActive=true;const finishButton=$('#liveRoomFinishSpeakingButton');if(finishButton)finishButton.disabled=true;liveRoomStatus('Starting',false);
    $('#liveRoomMicToggle').disabled=!audioStream?.getAudioTracks().length;$('#liveRoomMicToggle').textContent=audioStream?.getAudioTracks().length?'Mic on':'Mic unavailable';
    if(audioStream?.getAudioTracks().length){liveRoomAudioState('Connecting to live speech','Your microphone is active. We will show the transcript only after the speech service returns it.',false);try{await liveRoomStartAudioPipeline();await liveRoomPopulateMicDevices();}catch(audioSetupError){liveRoomStatus('Text and evidence mode');liveRoomAudioState('Live voice could not start','Your draft case is safe. Type your story or upload evidence while checking microphone support.',false);liveRoomFeedback(audioSetupError.message||'Live voice could not start. You can type instead.',true);const retry=$('#liveRoomRetryVoiceButton');if(retry)retry.hidden=false;}}
    else{liveRoomStatus('Text and evidence mode');liveRoomAudioState('Your case is ready','Type your story or add photos, PDFs, recordings and screen captures.',false);const retry=$('#liveRoomRetryVoiceButton');if(retry)retry.hidden=false;}
    liveRoomFeedback(existingCaseId?`You are back in case ${liveRoomCaseId}. New conversation turns, files and updates stay in this same case.`:`Your draft case ${liveRoomCaseId} is saved. You can start speaking, take a photo, share a screen or upload a document.`);
  }catch(err){const message=err.message||'We could not create your case. Please retry.';liveRoomFeedback(message,true);showToast(message,'error');liveRoomStatus('Not started');liveRoomAudioState('Your case was not created','Try again. No media is being recorded.',false);liveRoomCaseId=null;}
  finally{button.disabled=false;button.innerHTML='Start live resolution <span>↗</span>';}
}
async function liveRoomBlobToWav(blob){
  const AudioContextClass=window.AudioContext||window.webkitAudioContext;
  const OfflineContextClass=window.OfflineAudioContext||window.webkitOfflineAudioContext;
  if(!AudioContextClass||!OfflineContextClass)throw new Error('This browser cannot prepare the voice note for transcription. Use the live microphone or type instead.');
  const decoder=new AudioContextClass();
  try{
    const decoded=await decoder.decodeAudioData(await blob.arrayBuffer());
    const duration=Math.min(60,decoded.duration);
    if(!Number.isFinite(duration)||duration<0.5)throw new Error('The voice note is too short. Record at least one second.');
    const sampleRate=16000,frameCount=Math.ceil(duration*sampleRate);
    const offline=new OfflineContextClass(1,frameCount,sampleRate),source=offline.createBufferSource();
    source.buffer=decoded;source.connect(offline.destination);source.start(0,0,duration);
    const rendered=await offline.startRendering(),samples=rendered.getChannelData(0);
    const buffer=new ArrayBuffer(44+samples.length*2),view=new DataView(buffer);
    const write=(offset,value)=>{for(let i=0;i<value.length;i++)view.setUint8(offset+i,value.charCodeAt(i));};
    write(0,'RIFF');view.setUint32(4,36+samples.length*2,true);write(8,'WAVE');write(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,sampleRate,true);view.setUint32(28,sampleRate*2,true);view.setUint16(32,2,true);view.setUint16(34,16,true);write(36,'data');view.setUint32(40,samples.length*2,true);
    for(let i=0;i<samples.length;i++){const value=Math.max(-1,Math.min(1,samples[i]));view.setInt16(44+i*2,value<0?value*32768:value*32767,true);}
    return new File([buffer],`live-voice-note-${Date.now()}.wav`,{type:'audio/wav',lastModified:Date.now()});
  }finally{try{await decoder.close();}catch(_){}}
}
function liveRoomRestoreMicAfterVoiceNote(){
  if(liveRoomActive){liveRoomMuted=liveRoomWasMutedBeforeVoiceNote;const mic=$('#liveRoomMicToggle');if(mic){mic.textContent=liveRoomMuted?'Mic off':'Mic on';mic.setAttribute('aria-pressed',String(!liveRoomMuted));}}
  const button=$('#liveRoomVoiceNoteButton');if(button){button.textContent='Record voice note';button.classList.remove('is-recording');}
}
async function liveRoomStopVoiceNote(){
  const recorder=liveRoomVoiceNoteRecorder;
  if(!recorder||recorder.state==='inactive')return liveRoomVoiceNoteStopPromise||Promise.resolve();
  clearTimeout(liveRoomVoiceNoteTimer);liveRoomVoiceNoteTimer=null;
  try{recorder.stop();}catch(err){liveRoomFeedback(err.message||'The voice note could not be stopped.',true);}
  return liveRoomVoiceNoteStopPromise||Promise.resolve();
}
async function liveRoomStartVoiceNote(){
  if(!liveRoomActive||!liveRoomCaseId)throw new Error('Start a saved live case before recording a voice note.');
  if(!window.MediaRecorder)throw new Error('This browser does not support voice-note recording. Use the live microphone or type instead.');
  const sourceTrack=liveRoomStream?.getAudioTracks().find(track=>track.readyState==='live');
  if(!sourceTrack)throw new Error('No active microphone is available. Allow microphone access or choose another input device.');
  const clone=sourceTrack.clone();liveRoomVoiceNoteTracks=new MediaStream([clone]);
  const formats=['audio/webm;codecs=opus','audio/ogg;codecs=opus','audio/mp4'];
  const mimeType=formats.find(type=>MediaRecorder.isTypeSupported?.(type))||'';
  let recorder;
  try{recorder=mimeType?new MediaRecorder(liveRoomVoiceNoteTracks,{mimeType,audioBitsPerSecond:64000}):new MediaRecorder(liveRoomVoiceNoteTracks);}
  catch(error){liveRoomStopTracks(liveRoomVoiceNoteTracks);liveRoomVoiceNoteTracks=null;throw new Error(`Voice-note recording could not start: ${error.message||'unsupported format'}. Try Chrome or Edge.`);}
  liveRoomVoiceNoteChunks=[];liveRoomWasMutedBeforeVoiceNote=liveRoomMuted;liveRoomMuted=true;
  const mic=$('#liveRoomMicToggle');if(mic){mic.textContent='Mic paused';mic.setAttribute('aria-pressed','false');}
  liveRoomVoiceNoteRecorder=recorder;
  liveRoomVoiceNoteStopPromise=new Promise(resolve=>{liveRoomResolveVoiceNoteStop=resolve;});
  recorder.ondataavailable=event=>{if(event.data?.size)liveRoomVoiceNoteChunks.push(event.data);};
  recorder.onerror=event=>liveRoomFeedback(event.error?.message||'The browser reported a voice recording error. We will save any usable audio.',true);
  recorder.onstop=async()=>{
    clearTimeout(liveRoomVoiceNoteTimer);liveRoomVoiceNoteTimer=null;
    const button=$('#liveRoomVoiceNoteButton');if(button){button.disabled=true;button.textContent='Saving voice note…';}
    try{
      const type=recorder.mimeType||liveRoomVoiceNoteChunks[0]?.type||'audio/webm';
      const blob=new Blob(liveRoomVoiceNoteChunks,{type});
      if(!blob.size)throw new Error('The browser returned an empty voice recording. Check microphone permission and try again.');
      const originalType=String(type).toLowerCase().split(';',1)[0];
      const originalExtension=originalType.includes('ogg')?'ogg':originalType.includes('mp4')?'m4a':'webm';
      const originalName=`live-voice-note-${Date.now()}.${originalExtension}`;
      const original=new File([blob],originalName,{type:originalType||'audio/webm',lastModified:Date.now()});
      await liveRoomUploadFile(original,'audio_recording',{skipAudioTranscription:true});
      const wav=await liveRoomBlobToWav(blob);
      await liveRoomTranscribeAudioEvidence(wav);
      liveRoomFeedback('Original voice recording is saved in your case. Review the transcript preview and confirm it to add your words to the case.');
    }catch(error){liveRoomFeedback(error.message||'The voice note could not be saved or transcribed.',true);}
    finally{
      liveRoomStopTracks(liveRoomVoiceNoteTracks);liveRoomVoiceNoteTracks=null;liveRoomVoiceNoteRecorder=null;liveRoomVoiceNoteChunks=[];
      liveRoomRestoreMicAfterVoiceNote();if(button)button.disabled=false;
      const resolve=liveRoomResolveVoiceNoteStop;liveRoomResolveVoiceNoteStop=null;liveRoomVoiceNoteStopPromise=null;resolve?.();
    }
  };
  recorder.start(500);
  const button=$('#liveRoomVoiceNoteButton');if(button){button.textContent='Stop voice note';button.classList.add('is-recording');}
  liveRoomAudioState('Recording a voice note','Your live stream is paused to prevent duplicate transcripts. Stop when you finish; we will save and transcribe this recording.',true);
  liveRoomFeedback('Voice note recording. It will be attached to this case, then you can review and confirm the transcript.');
  liveRoomVoiceNoteTimer=setTimeout(()=>{if(liveRoomVoiceNoteRecorder?.state==='recording')liveRoomStopVoiceNote();},60000);
}
function liveRoomFinishSpeaking(){
  clearTimeout(liveRoomSilenceCommitTimer);liveRoomSilenceCommitTimer=null;liveRoomCommitSent=true;
  if(!liveRoomSocket||liveRoomSocket.readyState!==WebSocket.OPEN){liveRoomFeedback('The live speech connection is not ready. Restart voice or use Record voice note.',true);return;}
  try{liveRoomSocket.send(JSON.stringify({type:'commit'}));liveRoomAudioState('Finishing your sentence','Sending the end-of-turn signal to the speech service. Your transcript should arrive shortly.',false);liveRoomFeedback('Your sentence was sent for transcription.');}
  catch(error){liveRoomFeedback(error.message||'Could not finish the speech turn. Use Record voice note as a fallback.',true);}
}
function liveRoomStopTracks(stream){(stream?.getTracks?.()||[]).forEach(track=>{try{track.stop();}catch(_){}});}
async function liveRoomStopClip(){
  const recorder=liveRoomClipRecorder;
  if(!recorder||recorder.state==='inactive')return liveRoomClipStopPromise||Promise.resolve();
  clearTimeout(liveRoomClipTimer);liveRoomClipTimer=null;
  try{recorder.stop();}catch(err){liveRoomFeedback(err.message||'The recording could not be stopped cleanly.',true);}
  return liveRoomClipStopPromise||Promise.resolve();
}
async function endLiveRoom({silent=false}={}){
  await liveRoomFlushSpeechBuffer({autoAdvance:false});
  liveRoomActive=false;liveRoomClearPauseTimers();liveRoomSpeechStartedAt=0;liveRoomLastVoiceAt=0;liveRoomCommitSent=false;clearTimeout(liveRoomReconnectTimer);liveRoomReconnectTimer=null;clearTimeout(liveRoomTranscriptionTimer);liveRoomTranscriptionTimer=null;liveRoomSpeechProcessingAt=0;
  // Wait for the final MediaRecorder dataavailable/stop events and the evidence
  // upload before releasing the camera/microphone tracks.
  if(liveRoomClipRecorder&&liveRoomClipRecorder.state!=='inactive')await liveRoomStopClip();
  if(liveRoomVoiceNoteRecorder&&liveRoomVoiceNoteRecorder.state!=='inactive')await liveRoomStopVoiceNote();
  if(liveRoomCaseId&&liveRoomSessionId&&liveRoomSessionStartRecorded){try{const event=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/live-room/session-event`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event:'ended',session_id:liveRoomSessionId})});renderLiveRoomCase(event);}catch(err){if(!silent)liveRoomFeedback(`Session ended. The end marker could not be saved: ${err.message}`,true);}}
  clearTimeout(liveRoomClipTimer);liveRoomClipTimer=null;
  try{liveRoomSocket?.close(1000,'Session ended by user');}catch(_){}liveRoomSocket=null;
  try{liveRoomWorklet?.disconnect();liveRoomAudioSource?.disconnect();liveRoomGain?.disconnect();}catch(_){}
  try{await liveRoomAudioContext?.close();}catch(_){}
  liveRoomWorklet=null;liveRoomAudioSource=null;liveRoomGain=null;liveRoomAudioContext=null;
  liveRoomStopTracks(liveRoomStream);liveRoomStopTracks(liveRoomScreenStream);liveRoomStream=null;liveRoomScreenStream=null;liveRoomScreenCaptureReady=false;
  const video=$('#liveRoomCameraPreview'),screenVideo=$('#liveRoomScreenPreview');if(video){video.srcObject=null;video.hidden=true;}if(screenVideo){screenVideo.srcObject=null;screenVideo.hidden=true;}$('#liveRoomCameraPlaceholder').hidden=false;$('#liveRoomCameraLabel').textContent='Camera off';$('#liveRoomMicToggle').disabled=false;$('#liveRoomMicToggle').textContent='Mic off';

  $('#liveRoomWorkspace').hidden=true;$('#liveRoomStart').hidden=false;const placeholder=$('#liveRoomCameraPlaceholder');if(placeholder){const title=placeholder.querySelector('b'),hint=placeholder.querySelector('small');if(title)title.textContent='Your camera preview';if(hint)hint.textContent='Camera is optional. You can also upload a document.';}const retry=$('#liveRoomRetryVoiceButton');if(retry)retry.hidden=true;liveRoomStatus('Session ended');liveRoomAudioState('Session ended','Your saved case and evidence remain available in My cases.');
  if(!silent)showToast(liveRoomCaseId?`Live session ended. Your case ${liveRoomCaseId} is saved.`:'Live session ended. No case was created yet.');
}
async function liveRoomCanvasFile(video,filename){if(!video||!video.videoWidth||!video.videoHeight)throw new Error('There is no active camera or shared-screen image to capture.');const canvas=document.createElement('canvas');const scale=Math.min(1,1600/video.videoWidth);canvas.width=Math.round(video.videoWidth*scale);canvas.height=Math.round(video.videoHeight*scale);const ctx=canvas.getContext('2d',{alpha:false});ctx.drawImage(video,0,0,canvas.width,canvas.height);const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',.88));if(!blob)throw new Error('The image could not be prepared. Try again.');return new File([blob],filename,{type:'image/jpeg',lastModified:Date.now()});}
async function liveRoomUploadFile(file,captureSource='user_upload',options={}){
  if(!liveRoomCaseId)throw new Error('No draft case exists. Start a session first; files are never left in a temporary page queue.');
  liveRoomFeedback(`Saving ${file.name} directly to case ${liveRoomCaseId}…`);
  const form=new FormData();form.append('file',file,file.name);form.append('capture_source',captureSource);form.append('session_id',liveRoomSessionId||'');form.append('captured_at',new Date().toISOString());
  const result=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/evidence`,{method:'POST',body:form});renderLiveRoomCase(result);
  liveRoomFeedback(`${file.name} is saved to case ${liveRoomCaseId}.`);
  const ext=(file.name.split('.').pop()||'').toLowerCase();
  if(['png','jpg','jpeg','webp','pdf'].includes(ext))await liveRoomReviewNewEvidence(result.uploaded_evidence_id||'');
  else if(!options.skipAudioTranscription&&(String(file.type||'').startsWith('audio/')||['wav','mp3','m4a','ogg','flac','aac'].includes(ext)))await liveRoomTranscribeAudioEvidence(file);
  else liveRoomFeedback('The original video is saved in your case. It is not automatically analysed or independently verified.');
}
async function liveRoomTranscribeAudioEvidence(file){
  const panel=$('#liveRoomEvidenceReview');panel.hidden=false;panel.innerHTML='<h3>Transcribing support recording…</h3><p>The original recording remains attached to your case. The transcript is only a preview until you confirm it.</p>';
  try{
    const ext=(file.name.split('.').pop()||'').toLowerCase();
    const transcribeFile=['webm','mp4'].includes(ext)?await liveRoomBlobToWav(file):file;
    const form=new FormData();form.append('audio_file',transcribeFile,transcribeFile.name);form.append('language_code',($('#liveRoomLanguage')?.value||'indic-auto')==='indic-auto'?'auto':$('#liveRoomLanguage').value);
    const data=await api('/api/voice/transcribe',{method:'POST',body:form});
    const transcript=String(data.transcript||'').trim();if(!transcript)throw new Error('No readable speech was found in this recording. The file remains saved as evidence.');
    const detected=liveRoomNormalizeLanguageCode(data.detected_language_code);
    const transcriptLanguage=detected||liveRoomLanguageCode(transcript);
    if(detected){const mode=$('#liveRoomLanguageModeLabel');if(mode)mode.textContent=`Detected language: ${languageNames[detected]||detected}`;}
    panel.innerHTML=`<h3>Review the recording transcript</h3><p>${escapeHtml(file.name)} · ${escapeHtml(data.note||'This is an automated transcript. Check names, numbers and dates against the original recording.')}</p><textarea id="liveRoomAudioTranscript" rows="5" maxlength="4000">${escapeHtml(transcript)}</textarea><div class="live-room-review-actions"><button class="button button-dark" id="liveRoomConfirmAudioTranscript" type="button">Add transcript to case</button><button class="button button-quiet" id="liveRoomDiscardAudioTranscript" type="button">Discard transcript</button></div><small>The original audio stays in evidence. Confirmed transcript text becomes a user-provided case note and is not proof that the recorded statements are true.</small>`;
    $('#liveRoomConfirmAudioTranscript')?.addEventListener('click',async()=>{const text=$('#liveRoomAudioTranscript')?.value?.trim()||'';if(text.length<2){liveRoomFeedback('Review the transcript before saving it.',true);return;}panel.hidden=true;panel.innerHTML='';await liveRoomQueueUserText(`Transcript from uploaded support recording (${file.name}): ${text}`,'audio_import',transcriptLanguage);});
    $('#liveRoomDiscardAudioTranscript')?.addEventListener('click',()=>{panel.hidden=true;panel.innerHTML='';liveRoomFeedback('Transcript preview discarded. The original recording remains in the case.');});
    liveRoomFeedback('The support recording is attached. Review the transcript and confirm before it becomes part of your case conversation.');
  }catch(err){panel.innerHTML=`<h3>Audio is saved; transcription needs attention</h3><p>${escapeHtml(err.message||'We could not transcribe this recording.')}</p><small>The original recording remains in your case. You can type the important points instead.</small>`;}
}
function liveRoomAppendVisionControls(panel,evidenceId){
  if(!panel||!evidenceId)return;
  if(!liveRoomVisionAvailable){panel.insertAdjacentHTML('beforeend','<div class="live-room-ai-review-note"><small>Visual AI analysis is not configured on this server. Your original image is saved and local OCR review remains available.</small></div>');return;}
  panel.insertAdjacentHTML('beforeend',`<div class="live-room-ai-review-note"><label><input id="liveRoomVisionConsent" type="checkbox"> <span>I agree to send this image and the relevant details I have told BolKeResolve to the configured AI provider. I will cover OTPs, PINs and other secrets first. Provider data handling follows its terms.</span></label><button type="button" class="button button-outline" id="liveRoomAnalyzeVisionButton">Understand this image with AI</button><div id="liveRoomVisionResult" aria-live="polite"></div></div>`);
  $('#liveRoomAnalyzeVisionButton')?.addEventListener('click',()=>liveRoomAnalyzeEvidenceWithAI(evidenceId));
}
async function liveRoomAnalyzeEvidenceWithAI(evidenceId){
  const consent=$('#liveRoomVisionConsent'),button=$('#liveRoomAnalyzeVisionButton'),resultPanel=$('#liveRoomVisionResult');
  if(!consent?.checked){liveRoomFeedback('Please confirm that this image may be sent to the configured AI provider before analysis.',true);return;}
  if(button){button.disabled=true;button.textContent='Reviewing image…';}
  if(resultPanel)resultPanel.textContent='Checking visible details. The original image remains saved in your case.';
  try{
    const data=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/live-room/evidence/${encodeURIComponent(evidenceId)}/analyze`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({consent_to_external_processing:true,question:'Identify only visible payment-related facts and what should be checked next.'})});
    liveRoomPendingAiAnalysisId=data.analysis_id;
    const a=data.analysis||{},facts=a.facts||{},conf=a.fact_confidence||{};
    const candidates=Object.entries(facts).map(([key,value])=>`<label class="live-room-review-candidate"><span><strong>${escapeHtml(key.replaceAll('_',' '))}: ${escapeHtml(value)}</strong><small>${escapeHtml(conf[key]||'low')} confidence · candidate only</small></span><span><input type="checkbox" data-live-ai-field="${escapeHtml(key)}"> I checked this</span></label>`).join('');
    const obs=(a.observations||[]).map(item=>`<li>${escapeHtml(item)}</li>`).join('');
    if(resultPanel)resultPanel.innerHTML=`<h3>${escapeHtml(a.document_type||'Image review')}</h3><p>${escapeHtml(a.summary||'No concise summary was returned.')}</p>${a.security_warning?'<p class="live-room-ai-warning">Sensitive information may be visible. Check and redact the original before sharing it further.</p>':''}${candidates||'<p>No structured transaction facts were detected. The original image remains saved.</p>'}${obs?`<ul>${obs}</ul>`:''}${a.suggested_question?`<p><b>Suggested question:</b> ${escapeHtml(a.suggested_question)}</p>`:''}<div class="live-room-review-actions"><button class="button button-dark" id="liveRoomConfirmAiAnalysis" type="button" disabled>Confirm selected details</button><button class="button button-quiet" id="liveRoomDiscardAiAnalysis" type="button">Discard analysis</button></div><small>${escapeHtml(data.notice||'AI observations are not independently verified.')}</small>`;
    $('#liveRoomConfirmAiAnalysis')?.addEventListener('click',liveRoomConfirmAiAnalysis);resultPanel?.querySelectorAll('[data-live-ai-field]')?.forEach(input=>input.addEventListener('change',()=>{const confirm=$('#liveRoomConfirmAiAnalysis');if(confirm)confirm.disabled=!resultPanel.querySelector('[data-live-ai-field]:checked');}));
    $('#liveRoomDiscardAiAnalysis')?.addEventListener('click',async()=>{liveRoomPendingAiAnalysisId='';if(resultPanel)resultPanel.innerHTML='';liveRoomFeedback('The AI analysis preview was discarded. The original evidence remains in your case.');});
    liveRoomFeedback('Image analysis is ready. Review the candidate facts against the original before confirming them.');
  }catch(err){if(resultPanel)resultPanel.textContent=err.message||'Visual analysis is unavailable. The original image remains saved.';liveRoomFeedback(err.message,true);}
  finally{if(button){button.disabled=false;button.textContent='Understand this image with AI';}}
}
async function liveRoomConfirmAiAnalysis(){
  const panel=$('#liveRoomVisionResult'),button=$('#liveRoomConfirmAiAnalysis');
  if(!liveRoomPendingAiAnalysisId||!panel)return;
  const accepted=[...panel.querySelectorAll('[data-live-ai-field]:checked')].map(el=>el.dataset.liveAiField);
  if(!accepted.length){liveRoomFeedback('Select at least one fact you checked against the image.',true);return;}
  if(button){button.disabled=true;button.textContent='Saving reviewed details…';}
  try{
    const confirmed=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/live-room/evidence-analysis/confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({analysis_id:liveRoomPendingAiAnalysisId,confirmed:true,accepted_fields:accepted,apply_fields:[]})});
    liveRoomPendingAiAnalysisId='';renderLiveRoomCase(confirmed.case);if(panel)panel.innerHTML='<p>Your selected visual observations are now saved with their original evidence reference. Updating your next step…</p>';
    const guidance=await liveRoomRequestGuidance(liveRoomLanguageCode());const guidanceText=guidance?.guidance_text||'';if(guidanceText){liveRoomTranscriptBubble('agent',guidanceText);liveRoomSpeak(guidanceText,guidance?.language_code||'en-IN').catch(()=>{});}if(panel)panel.innerHTML='<p>Confirmed observations saved. Your case guidance has been updated.</p>';liveRoomFeedback('Your reviewed evidence is saved and the next-step guidance has been refreshed.');
  }catch(err){if(button){button.disabled=false;button.textContent='Confirm selected details';}liveRoomFeedback(err.message,true);}
}
async function liveRoomReviewNewEvidence(evidenceId){
  if(!evidenceId)return;
  const panel=$('#liveRoomEvidenceReview');panel.hidden=false;panel.innerHTML='<h3>Reviewing your document…</h3><p>Your original file is already saved. Extracted details will remain candidates until you confirm them.</p>';
  try{
    const data=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/evidence/${encodeURIComponent(evidenceId)}/review`,{method:'POST'});
    liveRoomPendingReviewId=data.review_id;
    const fields=Object.entries(data.fields||{}).map(([key,item])=>`<label class="live-room-review-candidate"><span><strong>${escapeHtml(item.label||key)}: ${escapeHtml(key==='amount'?money(item.value):String(item.value??''))}</strong><small>${escapeHtml(item.confidence||'candidate')} confidence · ${item.mismatch?'Possible conflict with saved case':''}</small></span><span><input type="checkbox" data-live-review-field="${escapeHtml(key)}"> I checked this</span></label>`).join('');
    panel.innerHTML=`<h3>Check what we found</h3><p>${escapeHtml(data.evidence_name||'Uploaded document')} · ${escapeHtml(data.notice||'These are unverified candidates. Check the original document.')}</p>${fields||'<p>No reliable transaction fields were found. The file is still stored in your case.</p>'}<div class="live-room-review-actions"><button class="button button-dark" id="liveRoomConfirmEvidence" type="button" disabled>Save checked details</button><button class="button button-quiet" id="liveRoomDiscardEvidence" type="button">Close</button></div><small>Recording a document fact does not automatically replace your original case details.</small>`;
    $('#liveRoomConfirmEvidence')?.addEventListener('click',liveRoomConfirmEvidence);panel.querySelectorAll('[data-live-review-field]')?.forEach(input=>input.addEventListener('change',()=>{const confirm=$('#liveRoomConfirmEvidence');if(confirm)confirm.disabled=!panel.querySelector('[data-live-review-field]:checked');}));
    $('#liveRoomDiscardEvidence')?.addEventListener('click',()=>{panel.hidden=true;panel.innerHTML='';liveRoomPendingReviewId='';});
    liveRoomAppendVisionControls(panel,evidenceId);
    liveRoomFeedback('The document is attached. Review local OCR candidates, or explicitly request visual AI analysis for this image.');
  }catch(err){
    panel.innerHTML=`<h3>Local text extraction unavailable</h3><p>${escapeHtml(err.message||'No reliable text was found. The original evidence remains saved.')}</p>`;
    liveRoomAppendVisionControls(panel,evidenceId);
    liveRoomFeedback('The original file is saved. You can still request visual AI analysis if configured.',false);
  }
}
async function liveRoomConfirmEvidence(){
  const panel=$('#liveRoomEvidenceReview');if(!liveRoomPendingReviewId||!panel)return;
  const accepted=[...panel.querySelectorAll('[data-live-review-field]:checked')].map(input=>input.dataset.liveReviewField);
  if(!accepted.length){liveRoomFeedback('Select at least one detail that you checked against the original document.',true);return;}
  const button=$('#liveRoomConfirmEvidence');button.disabled=true;button.textContent='Saving…';
  try{await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/evidence-review/confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({review_id:liveRoomPendingReviewId,accepted_fields:accepted,apply_fields:[],confirmed:true})});liveRoomPendingReviewId='';panel.hidden=true;panel.innerHTML='';const latest=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}`);renderLiveRoomCase(latest);liveRoomFeedback('The details you selected are recorded with their evidence source. Updating your next step…');const guidance=await liveRoomRequestGuidance(liveRoomLanguageCode());const guidanceText=guidance?.guidance_text||'';if(guidanceText){liveRoomTranscriptBubble('agent',guidanceText);liveRoomSpeak(guidanceText,guidance?.language_code||'en-IN').catch(()=>{});}liveRoomFeedback('Your reviewed document facts are saved and the next-step guidance has been refreshed.');}
  catch(err){button.disabled=false;button.textContent='Save checked details';liveRoomFeedback(err.message,true);}
}
$('#liveRoomTranscript')?.addEventListener('click',async event=>{
  const intent=event.target.closest('[data-live-intent-action]');if(!intent)return;const kind=intent.dataset.liveIntentAction;
  if(kind==='dismiss'){intent.closest('.live-room-capture-intent')?.remove();return;}
  try{
    const tools=$('#liveRoomCaptureTools');if(tools)tools.open=true;
    if(kind==='file')$('#liveRoomFiles')?.click();
    else if(kind==='camera')$('#liveRoomOpenCameraButton')?.click();
    else if(kind==='photo')$('#liveRoomCaptureButton')?.click();
    else if(kind==='screen')$('#liveRoomScreenButton')?.click();
    else if(kind==='clip')$('#liveRoomClipButton')?.click();
    intent.disabled=true;
  }catch(error){liveRoomFeedback(error.message||'Could not start that capture action.',true);intent.disabled=false;}
});
$('#liveRoomChooseFileButton')?.addEventListener('click',()=>$('#liveRoomFiles')?.click());
$('#liveRoomSupportDraft')?.addEventListener('click',async event=>{const button=event.target.closest('[data-live-copy-draft]');if(!button)return;const text=$('#liveRoomSupportDraftText')?.value||'';if(!text.trim())return;try{await navigator.clipboard.writeText(text);showToast('Support draft copied. Review it and send through the official channel.');}catch(_){showToast('Copy is unavailable in this browser. Select the draft text and copy it manually.','error');}});
$('#liveRoomSupportDraft')?.addEventListener('input',event=>{if(event.target.id==='liveRoomSupportDraftText')liveRoomSupportDraftEdited=event.target.value;});
$('#liveRoomStartButton')?.addEventListener('click',()=>startLiveRoom());
$('#liveRoomEndButton')?.addEventListener('click',()=>endLiveRoom());
async function liveRoomAnswerQuestion(button){
  if(!liveRoomCaseId||!button)return;
  const field=button.dataset.liveQuestionField,value=button.dataset.liveQuestionValue;
  const answers={
    merchant:{Meesho:'This order is from Meesho.',Flipkart:'This order is from Flipkart.',Zomato:'This order is from Zomato.',Other:'This order is from another app or store.'},
    merchant_name:{type_name:'The exact app or store name is in my next message.'},
    refund_scope:{full_order:'The refund is for the entire order.',some_items:'The refund is for selected products or items only.',unknown:'I am not sure whether this is a full or partial refund.'},
    refund_reason:{rejected:'The app says the return or refund was rejected or is not eligible.',pickup_pending:'The app says pickup or inspection is still pending.',no_reason:'The app did not show a reason.',other:'I will type the reason shown in the app.'},
    promised_timeline_details:{type_date:'I will type the refund date or promised number of working days.'},
    support_reference_details:{type_reference:'I will type the support ticket or complaint reference.'},
    order_outcome:{cancelled:'The order was cancelled.',return_picked_up:'The return was picked up.',not_delivered:'The order was never delivered.',delivered_with_issue:'The order arrived but something was wrong.',delivered:'The order was delivered normally.'},
    refund_status:{not_initiated:'The app shows that the refund has not been initiated.',pending:'The app shows that the refund is pending or processing.',initiated:'The app shows that the refund was initiated or processed.',unknown_not_credited:'I cannot find a refund status in the app.'},
    refund_scope:{full_order:'The refund is for the entire order.',some_items:'The refund is for selected products or items only.',unknown:'I am not sure whether this is a full or partial refund.'},
    refund_reason:{rejected:'The app says the return or refund was rejected or is not eligible.',pickup_pending:'The app says pickup or inspection is still pending.',no_reason:'The app did not show a reason.',other:'I will type the reason shown in the app.'},
    promised_timeline:{given:'A refund date or timeline was shown; I can share the exact date next.',not_given:'No refund date or timeline was given.',not_sure:'I am not sure whether a refund timeline was given.'},
    support_contacted:{yes:'I have already contacted support.',no:'I have not contacted support yet.'},
    support_reference:{reference:'I have a support ticket or reference.',reply_no_ref:'I received a reply but no ticket reference.',no_response:'I have not received a reply or reference yet.'},
    payment_app:{'Google Pay':'I used Google Pay for this UPI transaction.',PhonePe:'I used PhonePe for this UPI transaction.',Paytm:'I used Paytm for this UPI transaction.',Other:'I used another UPI app for this transaction.'},
    transaction_status:{success:'The UPI transaction status is successful.',pending:'The UPI transaction status is pending.',failed:'The UPI transaction status is failed.',debit_no_credit:'Money was debited but the recipient was not credited.'},
    transaction_time:{today:'The transaction happened today.',yesterday:'The transaction happened yesterday.','2_to_5_days':'The transaction happened 2 to 5 days ago.',older:'The transaction happened more than 5 days ago.'},
    problem_type:{refund:'The problem is that a refund was not received.',order:'The order was missing, incomplete or wrong.',payment:'The payment failed or money was debited.',account:'I do not recognise this transaction; it may be unauthorised.',other:'This is another kind of issue.'}
  };
  if(['merchant_name','promised_timeline_details','support_reference_details','item_count'].includes(field)||(field==='payment_app'&&value==='Other')||(field==='refund_reason'&&value==='other')){const input=$('#liveRoomTextInput');if(input){input.focus();input.placeholder=field==='merchant_name'?'Type the exact app or store name…':field==='promised_timeline_details'?'Type the exact date or number of working days…':field==='support_reference_details'?'Type the ticket or complaint reference…':field==='item_count'?'Type the number of products or items…':field==='refund_reason'?'Type the reason shown in the app…':'Type the exact UPI app name…';}showToast('Type the requested detail in the message box, then send it.');return;}
  const answer=answers[field]?.[value];if(!answer){showToast('This answer could not be matched to the current question. Please type your answer instead.','error');return;}
  button.disabled=true;button.textContent='Saving…';
  try{await liveRoomQueueUserText(answer,'user_note',liveRoomLanguageCode(answer));}
  finally{button.disabled=false;}
}
async function liveRoomSaveChecklist(input){
  if(!liveRoomCaseId||!input?.dataset.liveChecklistKey)return;
  input.disabled=true;
  try{const result=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/checklist/${encodeURIComponent(input.dataset.liveChecklistKey)}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({checked:input.checked})});if(activeCaseSnapshot){activeCaseSnapshot.action_pack=result.action_pack;liveRoomRenderGuidance(activeCaseSnapshot);}showToast(input.checked?'Marked as ready in this case.':'Checklist updated.');}
  catch(error){input.checked=!input.checked;showToast(error.message||'Could not save this checklist update.','error');}
  finally{input.disabled=false;}
}
async function liveRoomSaveFollowup(event){
  event.preventDefault();if(!liveRoomCaseId)return;
  const button=event.submitter||$('#liveRoomFollowupForm button[type="submit"]');if(button){button.disabled=true;button.textContent='Saving…';}
  try{const updated=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/follow-up`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({due_date:$('#liveRoomFollowupDate')?.value||'',note:$('#liveRoomFollowupNote')?.value?.trim()||'',completed:false})});renderLiveRoomCase(updated);showToast('Follow-up date saved in this case. A notification is not sent unless a reminder channel is configured.');}
  catch(error){showToast(error.message||'Could not save the follow-up date.','error');}
  finally{if(button){button.disabled=false;button.textContent='Save follow-up date';}}
}
$('#liveRoomFollowupForm')?.addEventListener('submit',liveRoomSaveFollowup);
$('#liveRoomEvidenceList')?.addEventListener('click',async event=>{
  const filter=event.target.closest('[data-live-evidence-filter]');if(filter){liveRoomEvidenceFilter=filter.dataset.liveEvidenceFilter;liveRoomRenderEvidence(activeCaseSnapshot);return;}
  const linkButton=event.target.closest('[data-link-evidence-claim]');if(linkButton&&liveRoomCaseId){
    const card=linkButton.closest('[data-evidence-card]');const claimKey=card?.querySelector('[data-claim-key]')?.value||'other';const relation=card?.querySelector('[data-claim-relation]')?.value||'supports';
    const label=({issue:'Issue description',order:'Order / payment',refund_promise:'Refund promise',refund_status:'Refund status',settlement:'Settlement status',support_contact:'Support conversation',support_reply:'Support reply',bank_credit:'Bank credit',reference:'Payment / complaint reference',other:'Other case detail'})[claimKey]||'Other case detail';
    linkButton.disabled=true;linkButton.textContent='Linking…';
    try{const result=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/evidence/${encodeURIComponent(linkButton.dataset.linkEvidenceClaim)}/claims`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({claim_key:claimKey,claim_label:label,relation})});renderLiveRoomCase(result.case);showToast('Evidence linked to the selected case detail. This link does not independently verify it.');}
    catch(error){linkButton.disabled=false;linkButton.textContent='Link evidence';liveRoomFeedback(error.message||'Could not link this evidence.',true);}
  }
});
$('#liveRoomReconImportButton')?.addEventListener('click',()=>$('#liveRoomReconCsv')?.click());
$('#liveRoomReconCsv')?.addEventListener('change',async event=>{
  const file=event.target.files?.[0];event.target.value='';if(!file||!liveRoomCaseId)return;
  const panel=$('#liveRoomReconPreview');if(panel){panel.hidden=false;panel.innerHTML='<p class="live-room-recon-loading">Reading the settlement report. No values will change your case until you confirm them.</p>';}
  const form=new FormData();form.append('file',file);
  try{const data=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/reconciliation/preview`,{method:'POST',body:form});renderLiveRoomCase(data.case);liveRoomRenderReconciliationPreview(data);showToast('Settlement report saved as original evidence. Review the extracted rows before confirming.');}
  catch(error){if(panel){panel.hidden=false;panel.textContent=error.message||'The CSV could not be read.';}liveRoomFeedback(error.message||'The settlement report could not be imported.',true);}
});
function liveRoomRenderReconciliationPreview(data){
  const panel=$('#liveRoomReconPreview');if(!panel)return;const preview=data?.preview||{};const rows=Array.isArray(preview.rows)?preview.rows:[];const columns=['payment_id','order_id','settlement_id','utr','status','amount','net_amount','currency','settlement_date','fees','tax'];
  const activeColumns=columns.filter(key=>Object.prototype.hasOwnProperty.call(preview.headers_recognised||{},key));
  panel.hidden=false;panel.innerHTML=`<div class="live-room-recon-head"><div><span class="live-room-question-eyebrow">RECONCILIATION REPORT · ${escapeHtml(preview.provider||'Payment provider')}</span><h3>Review ${rows.length} imported rows</h3><p>${escapeHtml(preview.notice||'These values are user-provided and not provider-verified.')}</p></div><button type="button" class="button button-quiet" data-recon-close>Close</button></div><div class="live-room-recon-table-wrap"><table class="live-room-recon-table"><thead><tr><th>Select</th><th>Row</th>${activeColumns.map(key=>`<th>${escapeHtml(key.replaceAll('_',' '))}</th>`).join('')}</tr></thead><tbody>${rows.map((row,index)=>`<tr><td><input type="checkbox" data-recon-row="${index}" checked aria-label="Confirm row ${index+1}"></td><td>${escapeHtml(row.source_row||String(index+1))}</td>${activeColumns.map(key=>`<td>${escapeHtml(row[key]||'—')}</td>`).join('')}</tr>`).join('')}</tbody></table></div><div class="live-room-recon-actions"><button type="button" class="button button-dark" data-recon-confirm="${escapeHtml(data.import_id)}">Confirm selected rows</button><small>Confirmation adds the selected report rows to this case as user-confirmed report content. It does not verify a bank credit or change the payment status automatically.</small></div>`;
}
$('#liveRoomReconPreview')?.addEventListener('click',async event=>{
  const close=event.target.closest('[data-recon-close]');if(close){const panel=$('#liveRoomReconPreview');panel.hidden=true;panel.innerHTML='';return;}
  const confirm=event.target.closest('[data-recon-confirm]');if(!confirm||!liveRoomCaseId)return;const selected=$$('[data-recon-row]:checked',$('#liveRoomReconPreview')).map(item=>Number(item.dataset.reconRow));confirm.disabled=true;confirm.textContent='Saving…';
  try{const result=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/reconciliation/${encodeURIComponent(confirm.dataset.reconConfirm)}/confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirmed:true,selected_rows:selected})});renderLiveRoomCase(result.case);showToast(`${result.confirmed_rows} report row(s) linked to your case.`);}
  catch(error){confirm.disabled=false;confirm.textContent='Confirm selected rows';liveRoomFeedback(error.message||'Could not confirm report rows.',true);}
});
$('#liveRoomGuidanceChecklist')?.addEventListener('click',event=>{const upload=event.target.closest('[data-live-evidence-upload]');if(upload){liveRoomPendingChecklistKey=upload.dataset.liveEvidenceUpload||'';const input=$('#liveRoomFiles');if(input){input.dataset.checklistContext=liveRoomPendingChecklistKey;input.click();}}});
$('#liveRoomGuidanceChecklist')?.addEventListener('change',event=>{const input=event.target.closest('[data-live-checklist-key]');if(input)liveRoomSaveChecklist(input);});
$('#liveRoomGuidanceQuestion')?.addEventListener('click',event=>{const answer=event.target.closest('[data-live-question-field]');if(answer)liveRoomAnswerQuestion(answer);});
$('#liveRoomFollowupNotice')?.addEventListener('click',async event=>{const button=event.target.closest('[data-live-followup-complete]');if(!button||!liveRoomCaseId)return;button.disabled=true;try{const follow=activeCaseSnapshot?.follow_up||{};const updated=await api(`/api/cases/${encodeURIComponent(liveRoomCaseId)}/follow-up`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({due_date:follow.due_date||'',note:follow.note||'',completed:true})});renderLiveRoomCase(updated);showToast('Follow-up marked complete.');}catch(error){button.disabled=false;showToast(error.message||'Could not update the follow-up.','error');}});
$('#liveRoomAddEvidenceButton')?.addEventListener('click',()=>$('#liveRoomFiles')?.click());
$('#liveRoomEditCaseButton')?.addEventListener('click',()=>{if(!liveRoomCaseId)return;currentCaseId=liveRoomCaseId;activeCaseTab='overview';showView('detail');});
$('#liveRoomLanguage')?.addEventListener('change',async()=>{const auto=$('#liveRoomLanguage').value==='indic-auto',label=$('#liveRoomLanguageModeLabel');if(label)label.textContent=auto?'Automatic language detection':`Preferred language: ${$('#liveRoomLanguage').selectedOptions[0]?.textContent||'selected'}`;if(!liveRoomActive)return;try{await liveRoomRestartVoice();liveRoomFeedback(auto?'Automatic language detection is on. Speak naturally.':'Speech preference updated. Continue speaking in the selected language.');}catch(err){liveRoomFeedback(err.message||'The speech language could not be changed.',true);}});
$('#liveRoomMicToggle')?.addEventListener('click',()=>{liveRoomMuted=!liveRoomMuted;(liveRoomStream?.getAudioTracks()||[]).forEach(track=>track.enabled=!liveRoomMuted);const button=$('#liveRoomMicToggle');button.textContent=liveRoomMuted?'Mic off':'Mic on';button.setAttribute('aria-pressed',String(!liveRoomMuted));liveRoomAudioState(liveRoomMuted?'Microphone paused':'Microphone active',liveRoomMuted?'Turn the microphone back on when you are ready.':'Speak a short sentence and check that the input meter moves.',!liveRoomMuted);});
$('#liveRoomFinishSpeakingButton')?.addEventListener('click',liveRoomFinishSpeaking);
$('#liveRoomVoiceNoteButton')?.addEventListener('click',async()=>{const button=$('#liveRoomVoiceNoteButton');try{if(liveRoomVoiceNoteRecorder&&liveRoomVoiceNoteRecorder.state==='recording'){button.disabled=true;await liveRoomStopVoiceNote();}else await liveRoomStartVoiceNote();}catch(error){liveRoomFeedback(error.message||'Voice-note recording could not start.',true);}});
$('#liveRoomRetryVoiceButton')?.addEventListener('click',async()=>{const button=$('#liveRoomRetryVoiceButton');button.disabled=true;button.textContent='Restarting…';try{await liveRoomRestartVoice();liveRoomFeedback('Voice restarted. Speak a short sentence and pause so we can confirm the transcript.');}catch(err){liveRoomFeedback(err.message||'Voice could not be restarted. Check microphone permissions and the server provider key.',true);}finally{button.disabled=false;button.textContent='Restart voice';}});
$('#liveRoomApplyMicSettings')?.addEventListener('click',async()=>{const button=$('#liveRoomApplyMicSettings');button.disabled=true;button.textContent='Applying…';try{await liveRoomApplyMicSettings();}catch(err){liveRoomFeedback(err.message||'Microphone settings could not be applied.',true);}finally{button.disabled=false;button.textContent='Apply mic settings';}});
navigator.mediaDevices?.addEventListener?.('devicechange',()=>{if(liveRoomActive)liveRoomPopulateMicDevices();});
async function liveRoomEnsureCamera(){
  const existing=liveRoomStream?.getVideoTracks?.().find(track=>track.readyState==='live');if(existing)return existing;
  if(!navigator.mediaDevices?.getUserMedia)throw new Error('Camera access is unavailable in this browser. Upload a photo instead.');
  const videoStream=await navigator.mediaDevices.getUserMedia({audio:false,video:{width:{ideal:1280},height:{ideal:720},facingMode:{ideal:'environment'}}});
  const tracks=videoStream.getVideoTracks();if(!tracks.length)throw new Error('The browser did not provide a camera video track.');
  tracks.forEach(track=>liveRoomStream?.addTrack(track));const preview=$('#liveRoomCameraPreview');preview.srcObject=videoStream;preview.hidden=false;await preview.play();
  const ready=await liveRoomWaitForVideoFrame(preview,5000);if(!ready){liveRoomStopTracks(videoStream);preview.srcObject=null;preview.hidden=true;throw new Error('The camera opened but did not provide a visible frame. Check the lens/privacy shutter or upload a photo.');}
  $('#liveRoomCameraPlaceholder').hidden=true;$('#liveRoomCameraLabel').textContent='Camera on · user-controlled';
  tracks[0].addEventListener('ended',()=>{preview.srcObject=null;preview.hidden=true;$('#liveRoomCameraPlaceholder').hidden=false;$('#liveRoomCameraLabel').textContent='Camera off · optional';const toggle=$('#liveRoomOpenCameraButton');if(toggle){toggle.textContent='Open camera';toggle.setAttribute('aria-pressed','false');}});
  return tracks[0];
}
async function liveRoomToggleCamera(){
  const preview=$('#liveRoomCameraPreview');
  const videoTracks=liveRoomStream?.getVideoTracks?.().filter(track=>track.readyState==='live')||[];
  const button=$('#liveRoomOpenCameraButton');
  if(videoTracks.length){
    videoTracks.forEach(track=>{try{track.stop();}catch(_){}try{liveRoomStream.removeTrack(track);}catch(_){}});
    if(preview){preview.pause();preview.srcObject=null;preview.hidden=true;}
    $('#liveRoomCameraPlaceholder').hidden=false;$('#liveRoomCameraLabel').textContent='Camera off · optional';
    if(button){button.textContent='Open camera';button.setAttribute('aria-pressed','false');}
    liveRoomAudioState('Camera is off','Your microphone and case remain active. Open the camera whenever you want to show a document.',liveRoomActive);
    return;
  }
  await liveRoomEnsureCamera();if(button){button.textContent='Close camera';button.setAttribute('aria-pressed','true');}
  liveRoomAudioState('Camera is ready','Position the document or item in the frame, then choose Capture photo when ready.',liveRoomActive);
}
$('#liveRoomOpenCameraButton')?.addEventListener('click',async()=>{const button=$('#liveRoomOpenCameraButton');button.disabled=true;try{await liveRoomToggleCamera();}catch(error){liveRoomFeedback(error.message||'The camera could not be opened.',true);}finally{button.disabled=false;}});
$('#liveRoomCaptureButton')?.addEventListener('click',async()=>{try{await liveRoomEnsureCamera();const file=await liveRoomCanvasFile($('#liveRoomCameraPreview'),`live-evidence-${Date.now()}.jpg`);await liveRoomUploadFile(file,'camera_photo');}catch(err){liveRoomFeedback(err.message,true);}});
$('#liveRoomScreenButton')?.addEventListener('click',async()=>{try{
  if(!navigator.mediaDevices?.getDisplayMedia)throw new Error('Screen sharing is not available in this browser. Upload a screenshot instead.');
  const video=$('#liveRoomScreenPreview');
  if(!liveRoomScreenCaptureReady||!liveRoomScreenStream){
    liveRoomScreenStream=await navigator.mediaDevices.getDisplayMedia({video:{frameRate:5},audio:false});video.srcObject=liveRoomScreenStream;video.hidden=false;await video.play();
    const screenReady=await liveRoomWaitForVideoFrame(video,5000);if(!screenReady){liveRoomStopTracks(liveRoomScreenStream);liveRoomScreenStream=null;video.srcObject=null;video.hidden=true;throw new Error('The browser opened screen sharing but did not provide a frame. Select a screen or window (not a browser permission dialog), then try again.');}
    liveRoomScreenCaptureReady=true;$('#liveRoomScreenButton').textContent='Capture another frame';
    liveRoomScreenStream.getVideoTracks()[0].addEventListener('ended',()=>{liveRoomScreenCaptureReady=false;liveRoomScreenStream=null;video.srcObject=null;video.hidden=true;$('#liveRoomScreenButton').textContent='Share screen';});
    // Save the first selected frame immediately so choosing a screen is not mistaken for a saved exhibit.
    const firstFrame=await liveRoomCanvasFile(video,`shared-screen-${Date.now()}.jpg`);await liveRoomUploadFile(firstFrame,'screen_capture');
    liveRoomFeedback('Your first shared-screen frame is saved to this case. Keep sharing and capture another frame whenever you need.');
    liveRoomOfferCaptureFromIntent('record a clip of the shared screen');
    return;
  }
  const file=await liveRoomCanvasFile(video,`shared-screen-${Date.now()}.jpg`);await liveRoomUploadFile(file,'screen_capture');
  liveRoomFeedback('Another screen frame is saved to your case. Stop sharing using your browser sharing indicator when finished.');
}catch(err){liveRoomFeedback(err.message||'Screen share was cancelled.',true);}});
$('#liveRoomClipButton')?.addEventListener('click',async()=>{
  let pendingClipTracks=[];
  try{
    if(liveRoomClipRecorder&&liveRoomClipRecorder.state==='recording'){
      $('#liveRoomClipButton').textContent='Saving clip…';
      await liveRoomStopClip();
      return;
    }
    if(!window.MediaRecorder)throw new Error('This browser does not support video recording. Use Take photo or upload a short video file instead.');
    const isScreen=Boolean(liveRoomScreenCaptureReady&&liveRoomScreenStream);
    let videoTracks=isScreen?liveRoomScreenStream.getVideoTracks():(liveRoomStream?.getVideoTracks()||[]);
    if(!videoTracks.length&&!isScreen){await liveRoomEnsureCamera();videoTracks=liveRoomStream?.getVideoTracks()||[];}
    if(!videoTracks.length)throw new Error('Start a camera or screen share before recording a clip.');
    const audioTrack=liveRoomStream?.getAudioTracks().find(track=>track.readyState==='live');
    if(!videoTracks.some(track=>track.readyState==='live'))throw new Error('The camera or screen share has ended. Start it again before recording.');
    // Clone capture tracks so MediaRecorder cannot stop the live preview or the
    // audio graph when a source track ends or the recorder is stopped.
    const recordTracks=[...videoTracks,...(audioTrack?[audioTrack]:[])].map(track=>track.clone());pendingClipTracks=recordTracks;
    const recordStream=new MediaStream(recordTracks);
    const candidates=['video/webm;codecs=vp8,opus','video/webm;codecs=vp9,opus','video/webm;codecs=vp8','video/webm','video/mp4'];
    const mimeType=candidates.find(type=>window.MediaRecorder?.isTypeSupported?.(type))||'';
    liveRoomClipChunks=[];
    try{liveRoomClipRecorder=mimeType?new MediaRecorder(recordStream,{mimeType,videoBitsPerSecond:750000,audioBitsPerSecond:64000}):new MediaRecorder(recordStream);}
    catch(constructorError){liveRoomStopTracks(recordStream);throw new Error(`This browser could not start a ${mimeType||'supported'} recording: ${constructorError.message||'unsupported media format'}. Try Chrome or Edge, or capture a photo instead.`);}
    liveRoomClipStopPromise=new Promise(resolve=>{liveRoomResolveClipStop=resolve;});
    const recorder=liveRoomClipRecorder;let recorderError='';
    recorder.ondataavailable=event=>{if(event.data?.size)liveRoomClipChunks.push(event.data);};
    recorder.onerror=event=>{recorderError=event.error?.message||'The browser stopped the recording unexpectedly.';liveRoomFeedback(`${recorderError} Saving any usable part of the clip…`,true);};
    recorder.onstop=async()=>{
      clearTimeout(liveRoomClipTimer);liveRoomClipTimer=null;
      const button=$('#liveRoomClipButton');if(button)button.textContent='Record clip';
      try{
        const actualType=recorder.mimeType||mimeType||liveRoomClipChunks[0]?.type||'video/webm';
        const blob=new Blob(liveRoomClipChunks,{type:actualType});
        if(blob.size>20*1024*1024)throw new Error('This video is larger than the 20 MB evidence limit. Record a shorter clip.');
        if(!blob.size)throw new Error(recorderError||'The browser produced an empty recording. Check camera permission and use Chrome or Edge.');
        const extension=actualType.includes('mp4')?'mp4':'webm';
        const saved=await liveRoomUploadFile(new File([blob],`${isScreen?'screen':'camera'}-support-record-${Date.now()}.${extension}`,{type:actualType,lastModified:Date.now()}),isScreen?'screen_video':'camera_video');
        if(recorderError)liveRoomFeedback(`A partial clip was saved to case ${liveRoomCaseId}. The browser reported: ${recorderError}`,true);
        else liveRoomFeedback(`Video evidence saved to case ${liveRoomCaseId}. Reopen the case to play the original recording.`);
      }catch(err){liveRoomFeedback(err.message||'The clip could not be saved.',true);}
      finally{
        liveRoomStopTracks(recordStream);pendingClipTracks=[];
        liveRoomClipRecorder=null;liveRoomClipChunks=[];
        const resolve=liveRoomResolveClipStop;liveRoomResolveClipStop=null;liveRoomClipStopPromise=null;resolve?.();
      }
    };
    recorder.start(1000);
    $('#liveRoomClipButton').textContent='Stop clip';
    liveRoomFeedback(`Recording a short ${isScreen?'screen':'camera'} evidence clip${audioTrack?' with microphone narration':''}. Stop it when finished. It auto-stops after 30 seconds.`);
    liveRoomClipTimer=setTimeout(()=>{if(liveRoomClipRecorder?.state==='recording')liveRoomStopClip();},30000);
  }catch(err){
    if(pendingClipTracks.length)liveRoomStopTracks(new MediaStream(pendingClipTracks));
    pendingClipTracks=[];liveRoomClipRecorder=null;liveRoomClipChunks=[];
    liveRoomClipStopPromise=null;liveRoomResolveClipStop=null;
    const button=$('#liveRoomClipButton');if(button)button.textContent='Record clip';
    liveRoomFeedback(err.message||'The clip recorder could not start. Check camera permission and browser support.',true);
  }
});
$('#liveRoomFiles')?.addEventListener('change',async event=>{const files=[...(event.target.files||[])],taskKey=event.target.dataset.checklistContext||'';event.target.value='';event.target.dataset.checklistContext='';liveRoomPendingChecklistKey='';for(const file of files){try{await liveRoomUploadFile(file,'user_upload');}catch(err){liveRoomFeedback(`${file.name}: ${err.message}`,true);}}if(taskKey&&files.length)liveRoomFeedback('The file is saved as original evidence. Review the document checklist and mark the item ready only when it is the right document.');});
$('#liveRoomTextForm')?.addEventListener('submit',async event=>{event.preventDefault();const input=$('#liveRoomTextInput'),text=input?.value?.trim()||'';if(text.length<2)return;input.value='';await liveRoomQueueUserText(text,'typed',liveRoomLanguageCode(text));});
$('#liveRoomFinishStoryButton')?.addEventListener('click',liveRoomFinishStory);
$('#liveRoomCaseAIActiveConsent')?.addEventListener('change',event=>liveRoomUpdateCaseAIConsent(!!event.currentTarget.checked));
$('#liveRoomOpenCaseButton')?.addEventListener('click',()=>{if(!liveRoomCaseId)return;currentCaseId=liveRoomCaseId;activeCaseTab='overview';showView('detail');});
