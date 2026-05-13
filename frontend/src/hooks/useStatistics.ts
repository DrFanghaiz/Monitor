import { useQuery } from '@tanstack/react-query'
import { fetchUserStats, fetchHourlyStats, fetchDailyStats, fetchDistribution } from '../services/statistics'

export function useUserStats(filterMode = 'all') {
  return useQuery({ queryKey: ['user-stats', filterMode], queryFn: () => fetchUserStats(filterMode) })
}

export function useHourlyStats() {
  return useQuery({ queryKey: ['hourly-stats'], queryFn: fetchHourlyStats })
}

export function useDailyStats(days = 30) {
  return useQuery({ queryKey: ['daily-stats', days], queryFn: () => fetchDailyStats(days) })
}

export function useDistribution(filterMode = 'all') {
  return useQuery({ queryKey: ['distribution', filterMode], queryFn: () => fetchDistribution(filterMode) })
}
