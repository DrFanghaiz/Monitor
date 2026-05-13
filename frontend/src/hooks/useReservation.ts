import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchReservations, createReservation, cancelReservation } from '../services/reservation'

export function useReservations(date?: string) {
  return useQuery({
    queryKey: ['reservations', date],
    queryFn: () => fetchReservations(date),
  })
}

export function useCreateReservation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createReservation,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reservations'] }),
  })
}

export function useCancelReservation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: cancelReservation,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reservations'] }),
  })
}
