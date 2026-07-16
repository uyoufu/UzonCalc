/** Typed APIs for saved calculation instances. */

import { httpClient } from 'src/api/base/httpClient'
import type { CalcInstance } from './types'

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
/** Replace instance result and provenance from another execution. */
export function updateInstanceResult(instanceOid: string, revision: number, executionId: string) { return httpClient.put<CalcInstance>(`/calc-report-instance/${instanceOid}/result`, { data: { revision, executionId } }) }
/** Soft-delete a saved instance. */
export function deleteInstance(instanceOid: string) { return httpClient.delete<void>(`/calc-report-instance/${instanceOid}`) }
