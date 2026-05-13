import { get, post } from './api'
import type { ReservationListResponse } from '../types'

export function fetchReservations(date?: string): Promise<ReservationListResponse> {
  const qs = date ? `?date=${encodeURIComponent(date)}` : ''
  return get<ReservationListResponse>(`/reservations${qs}`)
}

export function createReservation(body: {
  user_name: string
  date: string
  start_hour: number
  end_hour: number
}) {
  return post<{ success: boolean; message: string; id: number }>('/reservations', body)
}

export function cancelReservation(id: number) {
  return post<{ success: boolean }>(`/reservations/${id}/cancel`)
}
