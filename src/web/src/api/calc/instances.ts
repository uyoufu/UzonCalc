/** Typed APIs for saved calculation instances. */

import { httpClient } from 'src/api/base/httpClient'
import type { CalcExecution, CalcInstance } from './types'
import type { ExecutionDefaults } from './executions'

export interface InstanceListParams {
  categoryOid?: string
  query?: string
}

export interface InstanceItemsParams extends InstanceListParams {
  skip: number
  limit: number
  sortBy: string
  descending: boolean
}

/** Count saved calculation instances. */
export function countInstances(params: InstanceListParams) { return httpClient.get<number>('/calc-report-instance/count', { params }) }
/** List one page of saved calculation instances. */
export function listInstances(params: InstanceItemsParams) { return httpClient.get<CalcInstance[]>('/calc-report-instance/items', { params }) }
/** Create an instance from a completed execution. */
export function createInstance(data: { categoryOid: string; executionId: string; name: string; description?: string | null }) { return httpClient.post<CalcInstance>('/calc-report-instance', { data }) }
/** Load one saved instance. */
export function getInstance(instanceOid: string) { return httpClient.get<CalcInstance>(`/calc-report-instance/${instanceOid}`) }
/** Update instance metadata with optimistic revision. */
export function updateInstance(instanceOid: string, data: { revision: number; categoryOid: string; name: string; description?: string | null }) { return httpClient.put<CalcInstance>(`/calc-report-instance/${instanceOid}`, { data }) }
/** Load the active or last-successful execution retained by an instance. */
export function getInstanceExecution(instanceOid: string) { return httpClient.get<CalcExecution | null>(`/calc-report-instance/${instanceOid}/execution`) }
/** Run the immutable bundle retained by an instance. */
export function startInstanceExecution(instanceOid: string, data: { defaults?: ExecutionDefaults; isSilent?: boolean; lastHtmlPath?: string | null }) {
  return httpClient.post<CalcExecution>(`/calc-report-instance/${instanceOid}/execution`, { data })
}
/** Physically delete a saved instance. */
export function deleteInstance(instanceOid: string) { return httpClient.delete<void>(`/calc-report-instance/${instanceOid}`) }
/** Enable anonymous access for a saved instance. */
export function shareInstance(instanceOid: string) { return httpClient.put<{ instanceOid: string; shareOid: string; token: string; createdAt: string }>(`/calc-report-instance/${instanceOid}/share`) }
/** Revoke anonymous access for a saved instance. */
export function revokeInstanceShare(instanceOid: string) { return httpClient.delete<void>(`/calc-report-instance/${instanceOid}/share`) }
/** Load a read-only instance using an anonymous share token. */
export function getSharedInstance(token: string) { return httpClient.get<CalcInstance>(`/calc-report-instance/shared/${token}`) }
