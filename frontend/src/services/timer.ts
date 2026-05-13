import { get, post, del } from './api'
import type { TimerState, TimerStopResult, HistoryResponse } from '../types'

export function fetchTimerState(): Promise<TimerState> {
  return get<TimerState>('/timer/state')
}

export function startTimer(user_name: string) {
  return post<{ success: boolean; message: string }>('/timer/start', { user_name })
}

export function stopTimer(): Promise<TimerStopResult> {
  return post<TimerStopResult>('/timer/stop')
}

export function fetchTimerHistory(search?: string): Promise<HistoryResponse> {
  const qs = search ? `?search=${encodeURIComponent(search)}` : ''
  return get<HistoryResponse>(`/timer/history${qs}`)
}

export function deleteHistoryRecord(id: number) {
  return del(`/timer/history/${id}`)
}

export function deleteHistoryBatch(ids: number[]) {
  return post<{ success: boolean; deleted: number }>('/timer/history/delete-batch', { ids })
}
