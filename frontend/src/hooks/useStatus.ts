import { useQuery } from '@tanstack/react-query'
import { fetchStatus } from '../services/status'

export function useStatus() {
  return useQuery({
    queryKey: ['status'],
    queryFn: fetchStatus,
    refetchInterval: 5000,
  })
}
