import { motion } from 'framer-motion'
import { timerPulse } from '../../theme/motion'

type TimerSize = 'desktop' | 'large'

const sizeClasses: Record<TimerSize, string> = {
  desktop: 'text-timer-desktop',
  large: 'text-timer-xl',
}

export function TimerDisplay({ elapsed, size = 'large' }: { elapsed: string; size?: TimerSize }) {
  const parts = elapsed.split(':')
  const sz = sizeClasses[size]

  return (
    <motion.div
      className="flex items-baseline gap-1 select-none"
      animate={timerPulse.animate}
    >
      {parts.map((part, i) => (
        <span key={i} className="flex items-baseline">
          <span className={`font-mono ${sz} text-primary tabular-nums tracking-tight`}>
            {part}
          </span>
          {i < parts.length - 1 && (
            <span className={`font-mono ${sz} text-muted mx-0.5`}>:</span>
          )}
        </span>
      ))}
    </motion.div>
  )
}
