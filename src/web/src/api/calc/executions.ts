/** Typed APIs for managed calculation execution and history. */

import { httpClient } from 'src/api/base/httpClient'
import type { CalcExecution, CalcExecutionSource } from './types'

export interface ExecutionItemsParams {
  skip: number
  limit: number
  sortBy: string
  descending: boolean
  reportOid?: string
}

export type ExecutionDefaults = Record<string, Record<string, unknown>>

/** Start a workspace/latest/version execution. */
export function startExecution(data: { reportOid: string; source: CalcExecutionSource; defaults?: ExecutionDefaults; isSilent?: boolean; lastHtmlPath?: string | null }) { return httpClient.post<CalcExecution>('/calc/execution', { data }) }
/** Continue the original interactive process. */
export function continueExecution(executionId: string, defaults: ExecutionDefaults, lastHtmlPath?: string | null) { return httpClient.post<CalcExecution>(`/calc/execution/${executionId}/continue`, { data: { defaults, lastHtmlPath } }) }
/** Count persisted execution audits. */
export function countExecutions(reportOid?: string) { return httpClient.get<number>('/calc/execution/count', { params: { reportOid } }) }
/** List one page of persisted execution audits. */
export function listExecutions(params: ExecutionItemsParams) { return httpClient.get<CalcExecution[]>('/calc/execution/items', { params }) }
/** Load one execution audit. */
export function getExecution(executionId: string) { return httpClient.get<CalcExecution>(`/calc/execution/${executionId}`) }
/** Terminate an active execution. */
export function terminateExecution(executionId: string) { return httpClient.delete<void>(`/calc/execution/${executionId}`) }
