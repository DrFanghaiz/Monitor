import { motion } from 'framer-motion'
import { useTimerState, useTimerStart, useTimerStop } from '../hooks/useTimer'
import { useStatus } from '../hooks/useStatus'
import { TimerDisplay } from '../components/timer/TimerDisplay'
import { TimerControls } from '../components/timer/TimerControls'
import { fadeInUp, fadeInScale, statusDotPulse } from '../theme/motion'

export function Timer() {
  const { data: timerState, isLoading } = useTimerState()
  const { data: status } = useStatus()
  const startTimer = useTimerStart()
  const stopTimer = useTimerStop()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-muted text-sm">
        加载中…
      </div>
    )
  }

  const isRunning = timerState?.is_running ?? false
  const remoteActive = status?.remote_control.is_remote ?? false

  return (
    <div className="relative h-full flex flex-col items-center justify-center">
      {/* Ambient glow — scaled for desktop window */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div
          className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                      w-[200px] h-[200px] rounded-full blur-3xl opacity-20 transition-colors duration-700
                      ${isRunning
                        ? remoteActive ? 'bg-accent-red' : 'bg-accent-cyan'
                        : 'bg-accent-blue'
                      }`}
        />
      </div>

      <motion.div
        className="relative z-10 flex flex-col items-center gap-5 text-center"
        variants={fadeInScale}
        initial="hidden"
        animate="visible"
      >
        {/* Status */}
        <motion.div variants={fadeInUp} className="flex items-center gap-2.5">
          {isRunning ? (
            <>
              {remoteActive ? (
                <motion.span className="dot-red" animate={statusDotPulse.animate} />
              ) : (
                <span className="dot-green" />
              )}
              <span className={`text-sm font-medium ${remoteActive ? 'text-accent-red' : 'text-accent-green'}`}>
                {remoteActive ? '远程控制 · 会话进行中' : '会话进行中'}
              </span>
            </>
          ) : (
            <>
              <span className="dot-cyan" />
              <span className="text-sm font-medium text-muted">等待开始</span>
            </>
          )}
        </motion.div>

        {/* User identity */}
        {isRunning && timerState && (
          <motion.div variants={fadeInUp} className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-accent-cyan/15 flex items-center justify-center
                          text-lg font-bold text-accent-cyan ring-1 ring-accent-cyan/20 shrink-0">
              {timerState.current_user?.[0] ?? '?'}
            </div>
            <div className="text-base font-semibold text-accent-cyan">
              {timerState.current_user}
            </div>
          </motion.div>
        )}

        {/* Timer — desktop tier */}
        <motion.div variants={fadeInUp}>
          <TimerDisplay
            elapsed={timerState?.elapsed_formatted ?? '00:00:00'}
            size="desktop"
          />
        </motion.div>

        {/* Sub info */}
        {isRunning && timerState && (
          <motion.div variants={fadeInUp} className="text-sm text-muted">
            开始于 {timerState.start_time}
          </motion.div>
        )}

        {/* Controls */}
        <motion.div variants={fadeInUp}>
          <TimerControls
            isRunning={isRunning}
            userName={timerState?.current_user ?? ''}
            onStart={(name) => startTimer.mutate(name)}
            onStop={() => stopTimer.mutate()}
            loading={startTimer.isPending || stopTimer.isPending}
          />
        </motion.div>

        {/* Remote warning */}
        {remoteActive && (
          <motion.div
            variants={fadeInUp}
            className="px-4 py-2 rounded-xl bg-accent-red/10 border border-accent-red/20
                       text-sm text-accent-red font-medium"
          >
            检测到远程控制: {status?.remote_control.remote_type}
            {' · '}
            已持续 {status?.remote_control.elapsed_formatted}
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}
