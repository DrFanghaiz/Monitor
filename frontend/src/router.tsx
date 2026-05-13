import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from './layout/AppShell'
import { Dashboard } from './pages/Dashboard'
import { Timer } from './pages/Timer'
import { History } from './pages/History'
import { Statistics } from './pages/Statistics'
import { Reservation } from './pages/Reservation'
import { Settings } from './pages/Settings'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'timer', element: <Timer /> },
      { path: 'history', element: <History /> },
      { path: 'statistics', element: <Statistics /> },
      { path: 'reservation', element: <Reservation /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
])
