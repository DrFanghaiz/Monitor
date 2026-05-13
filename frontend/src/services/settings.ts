import { get, post } from './api'
import type { SettingsInfo, BackupItem } from '../types'

export function fetchSettings(): Promise<SettingsInfo> {
  return get<SettingsInfo>('/settings')
}

export function changeAdminPassword(old_password: string, new_password: string) {
  return post<{ success: boolean }>('/settings/password/admin', { old_password, new_password })
}

export function changeWebPassword(new_password: string) {
  return post<{ success: boolean }>('/settings/password/web', { new_password })
}

export function createBackup() {
  return post<{ success: boolean; path: string }>('/settings/backup')
}

export function fetchBackups(): Promise<{ backups: BackupItem[] }> {
  return get<{ backups: BackupItem[] }>('/settings/backups')
}
