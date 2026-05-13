import { useState, useEffect, useCallback } from 'react'
import { get, post } from '../services/api'

const VERIFIED_KEY = 'monitor_desktop'
const TOKEN_KEY = 'monitor_desktop_token'

/**
 * Desktop mode detection.
 * - sessionStorage carries verified result + token across client-side navigations.
 * - URL query param (?desktop=<token>) is only used on the very first page load.
 * - No optimistic display — avoids flash in browser mode with fake params.
 */
export function useIsDesktop(): boolean {
  const [desktop, setDesktop] = useState(() =>
    sessionStorage.getItem(VERIFIED_KEY) === '1'
  )

  useEffect(() => {
    if (sessionStorage.getItem(VERIFIED_KEY) === '1') return

    const params = new URLSearchParams(window.location.search)
    const token = params.get('desktop')
    if (!token) { setDesktop(false); return }

    get<{ desktop: boolean }>(`/window/mode?token=${encodeURIComponent(token)}`)
      .then((r) => {
        setDesktop(r.desktop)
        sessionStorage.setItem(VERIFIED_KEY, r.desktop ? '1' : '0')
        if (r.desktop) sessionStorage.setItem(TOKEN_KEY, token)
      })
      .catch(() => {
        setDesktop(false)
        sessionStorage.setItem(VERIFIED_KEY, '0')
      })
  }, [])

  return desktop
}

/** Window controls: minimize / maximize / close. Token-authenticated. */
export function useWindowControls() {
  const isDesktop = useIsDesktop()

  const minimize = useCallback(() => {
    if (!isDesktop) return
    const token = sessionStorage.getItem(TOKEN_KEY) || ''
    post(`/window/minimize?token=${encodeURIComponent(token)}`).catch(() => {})
  }, [isDesktop])

  const maximize = useCallback(() => {
    if (!isDesktop) return
    const token = sessionStorage.getItem(TOKEN_KEY) || ''
    post(`/window/maximize?token=${encodeURIComponent(token)}`).catch(() => {})
  }, [isDesktop])

  const close = useCallback(() => {
    if (!isDesktop) return
    const token = sessionStorage.getItem(TOKEN_KEY) || ''
    post(`/window/close?token=${encodeURIComponent(token)}`).catch(() => {})
  }, [isDesktop])

  const beginDrag = useCallback(() => {
    if (!isDesktop) return
    const token = sessionStorage.getItem(TOKEN_KEY) || ''
    post(`/window/drag?token=${encodeURIComponent(token)}`).catch(() => {})
  }, [isDesktop])

  const toggleMaximize = useCallback(() => {
    if (!isDesktop) return
    const token = sessionStorage.getItem(TOKEN_KEY) || ''
    post(`/window/toggle-maximize?token=${encodeURIComponent(token)}`).catch(() => {})
  }, [isDesktop])

  return { isDesktop, minimize, maximize, close, beginDrag, toggleMaximize }
}
