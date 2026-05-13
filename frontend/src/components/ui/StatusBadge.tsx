import { motion } from 'framer-motion'
import { statusDotPulse } from '../../theme/motion'

type StatusType = 'idle' | 'in_use' | 'remote_controlled'

const config: Record<StatusType, { label: string; dot: string; bg: string; text: string }> = {
  idle: {
    label: '空闲',
    dot: 'dot-green',
    bg: 'bg-accent-green/10',
    text: 'text-accent-green',
  },
  in_use: {
    label: '使用中',
    dot: 'dot-cyan',
    bg: 'bg-accent-cyan/10',
    text: 'text-accent-cyan',
  },
  remote_controlled: {
    label: '远程控制中',
    dot: 'dot-red',
    bg: 'bg-accent-red/10',
    text: 'text-accent-red',
  },
}

export function StatusBadge({ status }: { status: StatusType }) {
  const c = config[status] ?? config.idle
  return (
    <span
      className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-sm font-semibold ${c.bg} ${c.text}`}
    >
      {status === 'remote_controlled' ? (
        <motion.span className={c.dot} animate={statusDotPulse.animate} />
      ) : (
        <span className={c.dot} />
      )}
      {c.label}
    </span>
  )
}
