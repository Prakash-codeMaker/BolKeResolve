/*
 * Capture the one-time Share-to-Case capability from the URL fragment before
 * the page body, remote fonts, or app UI are parsed. URL fragments are never
 * included in the HTTP request. The token is moved into sessionStorage for the
 * short review flow, then removed from the address bar immediately.
 * The token is sent to API routes only in X-Share-Intake-Token headers.
 */
(() => {
  'use strict';
  try {
    const url = new URL(window.location.href);
    const hashParams = new URLSearchParams(url.hash.replace(/^#/, ''));
    const token = url.searchParams.get('shared_intake') || hashParams.get('shared_intake');
    if (!token) return;
    if (/^[A-Za-z0-9_-]{30,100}$/.test(token)) {
      try { sessionStorage.setItem('bolke_pending_share_token', token); } catch (_) {}
    }
    url.searchParams.delete('shared_intake');
    hashParams.delete('shared_intake');
    url.hash = hashParams.toString() ? `#${hashParams.toString()}` : '';
    history.replaceState(null, '', url.pathname + url.search + url.hash);
  } catch (_) {
    // The application remains usable; a failed capture simply requires sharing again.
  }
})();
