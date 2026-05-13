import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTimerHistory, useDeleteHistory, useDeleteHistoryBatch } from '../hooks/useTimer'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { fadeInUp, staggerContainer } from '../theme/motion'

export function History() {
  const [search, setSearch] = useState('')
  const [editMode, setEditMode] = useState(false)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const { data, isLoading } = useTimerHistory(search || undefined)
  const deleteOne = useDeleteHistory()
  const deleteBatch = useDeleteHistoryBatch()

  const records = data?.records ?? []
  const maxDur = Math.max(...records.map((r) => r.duration_seconds), 1)

  function toggleSelect(id: number) {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (selected.size === records.length) { setSelected(new Set()); return }
    setSelected(new Set(records.map((r) => r.id)))
  }

  return (
    <motion.div className="space-y-6" variants={staggerContainer} initial="hidden" animate="visible">
      {/* Header */}
      <motion.div variants={fadeInUp} className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-primary tracking-tight font-display">历史记录</h1>
        <div className="flex items-center gap-3">
          <div className="relative">
            <input
              type="text" placeholder="搜索姓名…" value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-48 px-4 py-2 rounded-input bg-input border border-border text-primary
                         placeholder:text-muted text-sm outline-none focus:border-accent-cyan transition-colors"
            />
          </div>
          <Button variant="ghost" size="sm" onClick={() => { setEditMode(!editMode); setSelected(new Set()) }}>
            {editMode ? '完成' : '编辑'}
          </Button>
        </div>
      </motion.div>

      {/* Batch actions */}
      <AnimatePresence>
        {editMode && selected.size > 0 && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
            <Card className="flex items-center justify-between border-accent-red/30">
              <span className="text-sm text-secondary">已选 {selected.size} 条</span>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={toggleAll}>
                  {selected.size === records.length ? '取消全选' : '全选'}
                </Button>
                <Button variant="danger" size="sm" disabled={deleteBatch.isPending}
                  onClick={() => { deleteBatch.mutate([...selected]); setSelected(new Set()); setEditMode(false) }}>
                  删除选中
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Records */}
      <motion.div variants={fadeInUp}>
        <Card>
          {isLoading ? (
            <p className="text-sm text-muted py-8 text-center">加载中…</p>
          ) : records.length === 0 ? (
            <p className="text-sm text-muted py-8 text-center">
              {search ? '无匹配记录' : '暂无使用记录'}
            </p>
          ) : (
            <div className="space-y-0.5">
              {records.map((r) => {
                const durMin = Math.floor(r.duration_seconds / 60)
                const pct = Math.min(r.duration_seconds / maxDur, 1)
                return (
                  <div key={r.id}
                    className={`flex items-center gap-3 py-3 px-3 rounded-lg transition-colors
                               ${editMode && selected.has(r.id) ? 'bg-accent-cyan/5 ring-1 ring-accent-cyan/20' : 'hover:bg-white/[0.03]'}`}
                    onClick={() => editMode && toggleSelect(r.id)}
                  >
                    {editMode && (
                      <div className={`w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${selected.has(r.id) ? 'bg-accent-cyan border-accent-cyan' : 'border-border'}`}>
                        {selected.has(r.id) && <span className="text-[10px] text-white">✓</span>}
                      </div>
                    )}
                    {/* Avatar */}
                    <div className="w-8 h-8 rounded-full bg-accent-cyan/15 flex items-center justify-center
                                  text-xs font-bold text-accent-cyan shrink-0">
                      {r.user_name[0]}
                    </div>
                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-primary font-medium truncate">{r.user_name}</div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-muted tabular-nums">{r.start_time?.slice(5, 16)}</span>
                        <span className="text-[10px] text-muted">→</span>
                        <span className="text-xs text-muted tabular-nums">{r.end_time?.slice(11, 16)}</span>
                        {/* Duration bar */}
                        <div className="flex-1 h-1 bg-border rounded-full min-w-[40px] max-w-[120px]">
                          <div className="h-full rounded-full bg-accent-cyan/40" style={{ width: `${pct * 100}%` }} />
                        </div>
                      </div>
                    </div>
                    {/* Duration + delete */}
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-xs text-accent-cyan font-mono tabular-nums">{durMin}min</span>
                      {!editMode && (
                        <button onClick={() => deleteOne.mutate(r.id)}
                          className="w-6 h-6 rounded-full bg-accent-red/10 text-accent-red text-xs
                                     hover:bg-accent-red/20 transition-colors flex items-center justify-center">
                          ×
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </Card>
      </motion.div>
    </motion.div>
  )
}
