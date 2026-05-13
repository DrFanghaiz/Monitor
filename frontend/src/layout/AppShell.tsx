import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TitleBar } from '../components/ui/TitleBar'

function getLayoutMode(pathname: string): 'dashboard' | 'timer' | 'default' {
  if (pathname === '/timer') return 'timer'
  if (pathname === '/') return 'dashboard'
  return 'default'
}

export function AppShell() {
  const location = useLocation()
  const mode = getLayoutMode(location.pathname)

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-root">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TitleBar />

        {/* Dashboard */}
        {mode === 'dashboard' && (
          <main className="flex-1 overflow-y-auto">
            <div className="px-8 lg:px-12 py-8 max-w-[1200px] mx-auto">
              <Outlet />
            </div>
          </main>
        )}

        {/* Timer — fills available height */}
        {mode === 'timer' && (
          <main className="flex-1 overflow-y-auto bg-timer">
            <Outlet />
          </main>
        )}

        {/* Default */}
        {mode === 'default' && (
          <main className="flex-1 overflow-y-auto">
            <div className="max-w-5xl mx-auto px-6 lg:px-10 py-8">
              <Outlet />
            </div>
          </main>
        )}
      </div>
    </div>
  )
}
