import { NavLink, useLocation, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'

const navItems = [
  { to: '/', label: '控制台', icon: '◈' },
  { to: '/timer', label: '计时', icon: '◉' },
  { to: '/history', label: '历史', icon: '▦' },
  { to: '/statistics', label: '统计', icon: '▤' },
  { to: '/reservation', label: '预约', icon: '◫' },
  { to: '/settings', label: '设置', icon: '◎' },
]

export function Sidebar() {
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const desktopParam = searchParams.get('desktop')
  const suffix = desktopParam ? `?desktop=${desktopParam}` : ''

  return (
    <aside className="w-56 shrink-0 border-r border-border-subtle bg-surface flex flex-col">
      <div className="px-5 py-7">
        <div className="flex items-center gap-3">
          <span className="text-2xl text-accent-cyan">⬡</span>
          <div>
            <div className="text-sm font-semibold text-primary tracking-wide font-display">Monitor</div>
            <div className="text-xs text-muted">公用机管理</div>
          </div>
        </div>
      </div>

      <hr className="sep mx-4" />

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const active = location.pathname === item.to
          return (
            <NavLink key={item.to} to={`${item.to}${suffix}`} className="block">
              <motion.div
                whileHover={{ x: 2 }}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                  transition-colors duration-150
                  ${active
                    ? 'bg-accent-cyan/10 text-accent-cyan'
                    : 'text-secondary hover:text-primary hover:bg-white/5'
                  }
                `}
              >
                <span className="text-lg">{item.icon}</span>
                {item.label}
              </motion.div>
            </NavLink>
          )
        })}
      </nav>

      <div className="px-4 py-4 border-t border-border-subtle">
        <div className="text-xs text-muted">v3.0.0</div>
      </div>
    </aside>
  )
}
