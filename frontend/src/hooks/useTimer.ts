import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchTimerState, startTimer, stopTimer,
  fetchTimerHistory, deleteHistoryRecord, deleteHistoryBatch,
} from '../services/timer'

export function useTimerState() {
  return useQuery({
    queryKey: ['timer-state'],
    queryFn: fetchTimerState,
    refetchInterval: (query) => (query.state.data?.is_running ? 1000 : 5000),
  })
}

export function useTimerStart() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (user_name: string) => startTimer(user_name),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['timer-state'] })
      qc.invalidateQueries({ queryKey: ['status'] })
    },
  })
}

export function useTimerStop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: stopTimer,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['timer-state'] })
      qc.invalidateQueries({ queryKey: ['status'] })
    },
  })
}

export function useTimerHistory(search?: string) {
  return useQuery({
    queryKey: ['timer-history', search],
    queryFn: () => fetchTimerHistory(search),
  })
}

export function useDeleteHistory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteHistoryRecord(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timer-history'] }),
  })
}

export function useDeleteHistoryBatch() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ids: number[]) => deleteHistoryBatch(ids),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timer-history'] }),
  })
}
