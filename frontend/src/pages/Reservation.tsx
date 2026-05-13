import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useReservations, useCreateReservation, useCancelReservation } from '../hooks/useReservation'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { fadeInUp, staggerContainer } from '../theme/motion'

function todayStr(): string {
  return new Date().toISOString().slice(0, 10)
}

function getDates(): { date: string; label: string }[] {
  const dates: { date: string; label: string }[] = []
  const now = new Date()
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  for (let i = 0; i < 7; i++) {
    const d = new Date(now)
    d.setDate(d.getDate() + i)
    const ds = d.toISOString().slice(0, 10)
    const wd = weekdays[d.getDay()]
    dates.push({
      date: ds,
      label: i === 0 ? `今天 ${d.getMonth() + 1}/${d.getDate()}` : i === 1 ? `明天 ${d.getMonth() + 1}/${d.getDate()}` : `${d.getMonth() + 1}/${d.getDate()} ${wd}`,
    })
  }
  return dates
}

export function Reservation() {
  const dates = getDates()
  const [selDate, setSelDate] = useState(todayStr())
  const [showAdd, setShowAdd] = useState(false)
  const [newName, setNewName] = useState('')
  const [startH, setStartH] = useState(9)
  const [endH, setEndH] = useState(10)
  const [error, setError] = useState('')

  const { data } = useReservations(selDate)
  const create = useCreateReservation()
  const cancel = useCancelReservation()

  const reservations = data?.reservations ?? []
  const reservedMap = new Map<number, { user_name: string; id: number }>()
  for (const r of reservations) {
    for (let h = r.start_hour; h < r.end_hour; h++) {
      reservedMap.set(h, { user_name: r.user_name, id: r.id })
    }
  }

  const currentHour = new Date().getHours()
  const isToday = selDate === todayStr()

  const hours = Array.from({ length: 14 }, (_, i) => i + 8)

  function handleCreate() {
    setError('')
    if (!newName.trim()) { setError('请输入姓名'); return }
    if (startH >= endH) { setError('结束时间必须晚于开始时间'); return }
    create.mutate(
      { user_name: newName.trim(), date: selDate, start_hour: startH, end_hour: endH },
      {
        onSuccess: () => { setShowAdd(false); setNewName(''); setError('') },
        onError: (e) => setError(e.message),
      },
    )
  }

  return (
    <motion.div className="space-y-6" variants={staggerContainer} initial="hidden" animate="visible">
      <motion.div variants={fadeInUp} className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-primary tracking-tight font-display">预约管理</h1>
        <Button size="sm" onClick={() => setShowAdd(true)}>+ 新建预约</Button>
      </motion.div>

      <motion.div variants={fadeInUp} className="flex gap-6">
        {/* Date selector */}
        <div className="w-48 shrink-0 space-y-1">
          {dates.map((d) => (
            <button key={d.date}
              onClick={() => setSelDate(d.date)}
              className={`w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150
                ${selDate === d.date ? 'bg-accent-cyan/10 text-accent-cyan ring-1 ring-accent-cyan/20' : 'text-secondary hover:text-primary hover:bg-white/5'}`}
            >
              {d.label}
            </button>
          ))}
        </div>

        {/* Time slots */}
        <div className="flex-1">
          <Card>
            <div className="text-sm font-semibold text-secondary mb-4 font-display">{selDate}</div>
            <div className="space-y-1.5">
              {hours.map((h) => {
                const res = reservedMap.get(h)
                const past = isToday && h < currentHour
                let status: 'available' | 'reserved' | 'past' = 'available'
                if (res) status = 'reserved'
                else if (past) status = 'past'

                const bg = status === 'reserved' ? 'bg-accent-red/5 border-accent-red/15' :
                           status === 'past' ? 'bg-white/[0.02] border-transparent' :
                           'bg-accent-green/5 border-accent-green/10 hover:border-accent-green/20'

                return (
                  <div key={h}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-colors ${bg}`}
                  >
                    <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                      status === 'reserved' ? 'bg-accent-red' : status === 'past' ? 'bg-muted' : 'bg-accent-green'}`} />
                    <span className={`text-sm tabular-nums w-24 shrink-0 ${status === 'past' ? 'text-muted/50' : 'text-primary'}`}>
                      {String(h).padStart(2, '0')}:00 - {String(h + 1).padStart(2, '0')}:00
                    </span>
                    {status === 'reserved' ? (
                      <>
                        <span className="flex-1 text-sm text-accent-red font-medium truncate">{res!.user_name}</span>
                        <button onClick={() => cancel.mutate(res!.id)}
                          className="text-xs text-accent-red/60 hover:text-accent-red transition-colors px-2 py-1 rounded hover:bg-accent-red/10">
                          取消
                        </button>
                      </>
                    ) : status === 'past' ? (
                      <span className="flex-1 text-xs text-muted/40">已过期</span>
                    ) : (
                      <span className="flex-1 text-xs text-accent-green/60">可预约</span>
                    )}
                  </div>
                )
              })}
            </div>
          </Card>
        </div>
      </motion.div>

      {/* Add modal */}
      <AnimatePresence>
        {showAdd && (
          <motion.div className="fixed inset-0 z-50 flex items-center justify-center bg-overlay"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setShowAdd(false)}>
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="card-elevated p-6 w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
              <h2 className="text-lg font-bold text-primary font-display mb-5">新建预约</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-xs text-muted block mb-1.5">姓名</label>
                  <input type="text" value={newName} onChange={(e) => setNewName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-input bg-input border border-border text-primary
                               placeholder:text-muted text-sm outline-none focus:border-accent-cyan transition-colors" />
                </div>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="text-xs text-muted block mb-1.5">开始</label>
                    <select value={startH} onChange={(e) => setStartH(+e.target.value)}
                      className="w-full px-3 py-2.5 rounded-input bg-input border border-border text-primary text-sm outline-none">
                      {hours.map((h) => <option key={h} value={h}>{String(h).padStart(2, '0')}:00</option>)}
                    </select>
                  </div>
                  <div className="flex-1">
                    <label className="text-xs text-muted block mb-1.5">结束</label>
                    <select value={endH} onChange={(e) => setEndH(+e.target.value)}
                      className="w-full px-3 py-2.5 rounded-input bg-input border border-border text-primary text-sm outline-none">
                      {hours.map((h) => <option key={h} value={h}>{String(h).padStart(2, '0')}:00</option>)}
                    </select>
                  </div>
                </div>
                {error && <p className="text-xs text-accent-red">{error}</p>}
                <div className="flex gap-3 pt-2">
                  <Button variant="ghost" size="sm" className="flex-1" onClick={() => setShowAdd(false)}>取消</Button>
                  <Button size="sm" className="flex-1" onClick={handleCreate} disabled={create.isPending}>
                    {create.isPending ? '创建中…' : '确认预约'}
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
