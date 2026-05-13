import { get } from './api'
import type { StatusResponse } from '../types'

export function fetchStatus(): Promise<StatusResponse> {
  return get<StatusResponse>('/status')
}
