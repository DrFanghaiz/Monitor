# Codex Review

## Status

**Decision: APPROVED**

**Stage:** Desktop Shell Final Polish - Codex Review Fix

## Findings

No blocking findings.

## Verified From Source

### Browser fallback no longer receives desktop token

**File:** `desktop/shell.py`

The normal WebView2 shell path still opens the token-bearing URL:

```python
url = f"{base}{'?desktop=' + _desktop_token if not dev_mode else ''}"
```

But fallback now receives the clean base URL:

```python
_create_window(url, fallback_url=base)
```

And both WebView2 failure paths use:

```python
_fallback_browser(fallback_url or url)
```

This means:

- Normal WebView2 shell keeps `?desktop=<uuid>` and shows TitleBar.
- Browser fallback opens `http://127.0.0.1:8000` without `desktop` token.
- Browser fallback does not render desktop-only TitleBar.
- Browser fallback does not expose non-functional desktop window controls.

### Previous checks remain valid

- TitleBar visible strings are correct in UTF-8 source.
- Window control endpoints remain token-protected.
- Close cleanup path remains present in `desktop/shell.py`.
- Startup loading indicator exists in `frontend/index.html`.

## Residual Notes

These are known non-blocking limitations:

- Edge resize is not implemented.
- Standalone restore button is not exposed.
- System-level window state changes can still drift from `_window_maximized`.
- `webview2==0.0.4` package maturity remains a packaging/runtime risk.

## Next Decision

Desktop shell final polish stage is approved. Recommended next step: release packaging verification.
