import { get } from './api'
import type { UserStatsResponse, HourlyStat, DailyStat, DistributionStat } from '../types'

export function fetchUserStats(filter_mode = 'all'): Promise<UserStatsResponse> {
  return get<UserStatsResponse>(`/statistics/users?filter_mode=${filter_mode}`)
}

export function fetchHourlyStats(): Promise<{ hourly: HourlyStat[] }> {
  return get<{ hourly: HourlyStat[] }>('/statistics/hourly')
}

export function fetchDailyStats(days = 30): Promise<{ daily: DailyStat[] }> {
  return get<{ daily: DailyStat[] }>(`/statistics/daily?days=${days}`)
}

export function fetchDistribution(filter_mode = 'all'): Promise<{ distribution: DistributionStat[] }> {
  return get<{ distribution: DistributionStat[] }>(`/statistics/distribution?filter_mode=${filter_mode}`)
}
