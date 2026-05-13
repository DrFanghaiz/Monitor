/* ---- Status ---- */

export interface LocalUseState {
  current_user: string | null
  start_time: string | null
  elapsed_seconds: number
  elapsed_formatted: string
}

export interface RemoteControlState {
  is_remote: boolean
  remote_type: string | null
  start_time: string | null
  elapsed_seconds: number
  elapsed_formatted: string
}

export interface StatusResponse {
  timestamp: string
  computer_status: 'idle' | 'in_use' | 'remote_controlled'
  local_use: LocalUseState
  remote_control: RemoteControlState
  today_records: HistoryRecord[]
  today_reservations: ReservationRecord[]
}

/* ---- Timer ---- */

export interface TimerState {
  is_running: boolean
  current_user: string | null
  start_time: string | null
  elapsed_seconds: number
  elapsed_formatted: string
}

export interface TimerStopResult {
  success: boolean
  user_name: string
  duration_seconds: number
  duration_formatted: string
  elapsed_formatted: string
}

/* ---- History ---- */

export interface HistoryRecord {
  id: number
  user_name: string
  start_time: string
  end_time: string
  duration_seconds: number
  created_at?: string
}

export interface HistoryResponse {
  records: HistoryRecord[]
}

/* ---- Statistics ---- */

export interface UserStat {
  user_name: string
  total_seconds: number
  last_seen: string | null
}

export interface UserStatsResponse {
  users: UserStat[]
}

export interface HourlyStat {
  date: string
  hour: number
  hours: number
}

export interface DailyStat {
  date: string
  hours: number
  users: number
}

export interface DistributionStat {
  user_name: string
  total_seconds: number
}

/* ---- Reservation ---- */

export interface ReservationRecord {
  id: number
  user_name: string
  date: string
  start_hour: number
  end_hour: number
  status: string
}

export interface ReservationSlot {
  hour: number
  time_text: string
  status: 'available' | 'reserved' | 'past'
  user_name: string | null
  reservation_id: number | null
}

export interface ReservationListResponse {
  reservations: ReservationRecord[]
}

/* ---- Settings ---- */

export interface SettingsInfo {
  web_server_port: number
  web_server_enabled: boolean
  tunnel_enabled: boolean
  tunnel_mode: string
  auto_backup: boolean
  backup_retention_days: number
  remote_monitor_enabled: boolean
}

export interface BackupItem {
  name: string
  path: string
  size: number
  created: string
  is_manual: boolean
}
