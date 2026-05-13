import { motion } from 'framer-motion'
import type { HTMLMotionProps } from 'framer-motion'

type CardProps = HTMLMotionProps<'div'> & {
  elevated?: boolean
  glow?: boolean
}

export function Card({ elevated, glow, className = '', children, ...rest }: CardProps) {
  return (
    <motion.div
      className={`${elevated ? 'card-elevated' : 'card'} p-6 ${glow ? 'shadow-glow' : ''} ${className}`}
      {...rest}
    >
      {children}
    </motion.div>
  )
}
