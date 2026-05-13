import { motion } from 'framer-motion'

type ButtonVariant = 'primary' | 'danger' | 'ghost'

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-accent-blue text-white hover:brightness-110 shadow-lg shadow-accent-blue/20',
  danger:
    'bg-accent-red text-white hover:brightness-110 shadow-lg shadow-accent-red/20',
  ghost:
    'bg-white/5 text-secondary hover:bg-white/10',
}

type ButtonProps = {
  variant?: ButtonVariant
  size?: 'sm' | 'md' | 'lg'
  children: React.ReactNode
  className?: string
  disabled?: boolean
  onClick?: () => void
}

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  disabled,
  onClick,
}: ButtonProps) {
  const sizeStyles = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-sm font-semibold',
    lg: 'px-8 py-4 text-base font-semibold',
  }

  return (
    <motion.button
      whileHover={disabled ? undefined : { scale: 1.02 }}
      whileTap={disabled ? undefined : { scale: 0.98 }}
      onClick={onClick}
      disabled={disabled}
      className={`
        inline-flex items-center justify-center gap-2 rounded-button
        transition-all duration-200
        disabled:opacity-40 disabled:cursor-not-allowed
        ${sizeStyles[size]} ${variantStyles[variant]} ${className}
      `}
    >
      {children}
    </motion.button>
  )
}
