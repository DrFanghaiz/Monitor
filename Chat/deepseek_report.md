# DeepSeek Phase Report

## Stage: Desktop Shell Final Polish — Codex Review Fix

### Files Modified

- `desktop/shell.py` — `_create_window` now accepts `fallback_url` parameter. Browser fallback opens clean base URL (no `?desktop=<token>`), so TitleBar does not render in a normal browser.
- `frontend/index.html` — added lightweight loading indicator (previous round)

### What Was Fixed

**Browser fallback no longer receives desktop token**: When WebView2 is unavailable, `_fallback_browser` now opens the plain `http://127.0.0.1:8000` URL instead of the token-bearing `?desktop=<uuid>` URL. The frontend does not validate desktop mode, TitleBar does not render, and broken desktop controls cannot appear in a browser tab.

### Verified

- WebView2 normal path: `?desktop=<uuid>` URL → TitleBar shown ✓
- Browser fallback: clean URL → no TitleBar ✓
- Browser with fake `?desktop=1`: API `/mode` verification fails → no TitleBar ✓
- All 5 window endpoints token-protected ✓
- TypeScript 0 errors, Vite OK, Python compile OK ✓
