import { useState } from 'react'
import { motion } from 'framer-motion'
import { useStatus } from '../hooks/useStatus'
import { useTimerStart, useTimerState } from '../hooks/useTimer'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { StatusBadge } from '../components/ui/StatusBadge'
import { TimerDisplay } from '../components/timer/TimerDisplay'
import { fadeInUp, staggerContainer } from '../theme/motion'

export function Dashboard() {
  const { data: status, isLoading } = useStatus()
  const { data: timerState } = useTimerState()
  const startTimer = useTimerStart()
  const [quickName, setQuickName] = useState('')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-muted text-sm">
        加载中…
      </div>
    )
  }

  const s = status!
  const isActive = timerState?.is_running ?? false

  return (
    <motion.div
      className="space-y-6"
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
    >
      {/* Page header */}
      <motion.div variants={fadeInUp} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-primary tracking-tight font-display">控制台</h1>
          <p className="text-sm text-muted mt-1">{s.timestamp}</p>
        </div>
        <StatusBadge status={s.computer_status} />
      </motion.div>

      {/* Main status card */}
      <motion.div variants={fadeInUp}>
        <Card elevated glow={s.computer_status === 'remote_controlled'}>
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            {/* Left: machine identity + quick start */}
            <div className="space-y-4 flex-1">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-accent-cyan/10 flex items-center justify-center">
                  <span className="text-xl text-accent-cyan">⬡</span>
                </div>
                <div>
                  <div className="text-sm font-semibold text-primary">公用计算机</div>
                  <div className="text-xs text-muted">
                    {isActive ? `当前: ${timerState?.current_user}` : '就绪'}
                  </div>
                </div>
              </div>

              {!isActive && (
                <div className="flex gap-3 max-w-md">
                  <input
                    type="text"
                    placeholder="输入姓名快速开始…"
                    value={quickName}
                    onChange={(e) => setQuickName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && quickName.trim()) {
                        startTimer.mutate(quickName.trim())
                        setQuickName('')
                      }
                    }}
                    className="flex-1 px-4 py-2.5 rounded-input bg-input border border-border
                               text-primary placeholder:text-muted text-sm outline-none
                               focus:border-accent-cyan transition-colors"
                  />
                  <Button
                    size="sm"
                    disabled={!quickName.trim() || startTimer.isPending}
                    onClick={() => {
                      if (quickName.trim()) {
                        startTimer.mutate(quickName.trim())
                        setQuickName('')
                      }
                    }}
                  >
                    开始
                  </Button>
                </div>
              )}
            </div>

            {/* Right: current session */}
            {isActive && timerState && (
              <div className="flex flex-col items-end gap-1">
                <div className="text-xs text-muted uppercase tracking-wider mb-1">当前会话</div>
                <TimerDisplay elapsed={timerState.elapsed_formatted} />
                <div className="text-sm text-accent-cyan font-semibold mt-2">
                  {timerState.current_user}
                </div>
              </div>
            )}
          </div>
        </Card>
      </motion.div>

      {/* Stat cards row */}
      <motion.div
        variants={fadeInUp}
        className="grid grid-cols-1 sm:grid-cols-3 gap-4"
      >
        <Card>
          <div className="text-xs text-muted uppercase tracking-wider mb-2">今日使用记录</div>
          <div className="text-2xl font-bold text-primary tabular-nums">
            {s.today_records.length}
          </div>
          <div className="text-xs text-muted mt-1">条会话</div>
        </Card>

        <Card>
          <div className="text-xs text-muted uppercase tracking-wider mb-2">今日预约</div>
          <div className="text-2xl font-bold text-primary tabular-nums">
            {s.today_reservations.length}
          </div>
          <div className="text-xs text-muted mt-1">项预约</div>
        </Card>

        <Card>
          <div className="text-xs text-muted uppercase tracking-wider mb-2">远程控制</div>
          <div className="flex items-center gap-2 mt-1">
            <span className={s.remote_control.is_remote ? 'dot-red' : 'dot-green'} />
            <span
              className={`text-lg font-bold ${s.remote_control.is_remote ? 'text-accent-red' : 'text-accent-green'}`}
            >
              {s.remote_control.is_remote ? s.remote_control.remote_type : '安全'}
            </span>
          </div>
          {s.remote_control.is_remote && (
            <div className="text-xs text-muted mt-1">
              已持续 {s.remote_control.elapsed_formatted}
            </div>
          )}
        </Card>
      </motion.div>

      {/* Recent activity */}
      <motion.div variants={fadeInUp}>
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-secondary uppercase tracking-wider">
              今日活动
            </h2>
          </div>
          {s.today_records.length === 0 ? (
            <p className="text-sm text-muted py-4 text-center">今日暂无使用记录</p>
          ) : (
            <div className="space-y-1">
              {s.today_records.map((r) => {
                const durMin = Math.floor(r.duration_seconds / 60)
                return (
                  <div
                    key={r.id}
                    className="flex items-center justify-between py-2.5 px-3 rounded-lg
                               hover:bg-white/[0.03] transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-accent-cyan/15 flex items-center justify-center
                                    text-xs font-bold text-accent-cyan">
                        {r.user_name[0]}
                      </div>
                      <span className="text-sm text-primary font-medium">{r.user_name}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-xs text-muted tabular-nums">
                        {r.start_time?.slice(11, 16)} - {r.end_time?.slice(11, 16)}
                      </span>
                      <span className="text-xs text-accent-cyan font-mono tabular-nums">
                        {durMin}min
                      </span>
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
