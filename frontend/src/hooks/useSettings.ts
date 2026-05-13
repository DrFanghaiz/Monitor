import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchSettings, changeAdminPassword, changeWebPassword,
  createBackup, fetchBackups,
} from '../services/settings'

export function useSettings() {
  return useQuery({ queryKey: ['settings'], queryFn: fetchSettings })
}

export function useChangeAdminPassword() {
  return useMutation({ mutationFn: (body: { old_password: string; new_password: string }) => changeAdminPassword(body.old_password, body.new_password) })
}

export function useChangeWebPassword() {
  return useMutation({ mutationFn: (new_password: string) => changeWebPassword(new_password) })
}

export function useCreateBackup() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: createBackup, onSuccess: () => qc.invalidateQueries({ queryKey: ['backups'] }) })
}

export function useBackups() {
  return useQuery({ queryKey: ['backups'], queryFn: fetchBackups })
}
