import { useRef, useCallback } from 'react'
import { useWindowControls } from '../../hooks/useDesktop'

const DRAG_THRESHOLD = 4

export function TitleBar() {
  const { isDesktop, minimize, maximize, close, beginDrag, toggleMaximize } = useWindowControls()
  const dragState = useRef<{ sx: number; sy: number; dragging: boolean } | null>(null)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return  // left button only
    dragState.current = { sx: e.clientX, sy: e.clientY, dragging: false }
  }, [])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const ds = dragState.current
    if (!ds || ds.dragging) return
    const dx = Math.abs(e.clientX - ds.sx)
    const dy = Math.abs(e.clientY - ds.sy)
    if (dx > DRAG_THRESHOLD || dy > DRAG_THRESHOLD) {
      ds.dragging = true
      beginDrag()
    }
  }, [beginDrag])

  const clearDrag = useCallback(() => {
    dragState.current = null
  }, [])

  const handleDoubleClick = useCallback(() => {
    dragState.current = null
    toggleMaximize()
  }, [toggleMaximize])

  if (!isDesktop) return null

  return (
    <div className="flex items-center h-8 bg-surface border-b border-border-subtle shrink-0 select-none">
      {/* Title area: press + move >4px = drag; double-click = maximize */}
      <div className="flex items-center gap-2 pl-3 flex-1 h-full cursor-default"
           onMouseDown={handleMouseDown}
           onMouseMove={handleMouseMove}
           onMouseUp={clearDrag}
           onMouseLeave={clearDrag}
           onDoubleClick={handleDoubleClick}>
        <span className="text-sm text-accent-cyan">⬡</span>
        <span className="text-[11px] text-muted font-medium tracking-wide">
          Monitor · 公用机管理系统
        </span>
      </div>

      {/* Window controls */}
      <div className="flex h-full">
        <button onClick={minimize}
          className="w-[46px] h-full flex items-center justify-center text-muted hover:bg-white/8 transition-colors"
          title="最小化">
          <svg width="10" height="1" viewBox="0 0 10 1"><rect width="10" height="1" fill="currentColor" /></svg>
        </button>
        <button onClick={maximize}
          className="w-[46px] h-full flex items-center justify-center text-muted hover:bg-white/8 transition-colors"
          title="最大化">
          <svg width="10" height="10" viewBox="0 0 10 10"><rect x="0.5" y="0.5" width="9" height="9" rx="1" fill="none" stroke="currentColor" strokeWidth="1" /></svg>
        </button>
        <button onClick={close}
          className="w-[46px] h-full flex items-center justify-center text-muted hover:bg-accent-red hover:text-white transition-colors"
          title="关闭">
          <svg width="10" height="10" viewBox="0 0 10 10"><path d="M1 1l8 8M9 1l-8 8" stroke="currentColor" strokeWidth="1.2" /></svg>
        </button>
      </div>
    </div>
  )
}
