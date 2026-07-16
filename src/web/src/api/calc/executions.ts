/** Typed APIs for managed calculation execution and history. */

import { httpClient } from 'src/api/base/httpClient'
import type { CalcExecution, CalcExecutionSource, PaginatedResult } from './types'

export type ExecutionDefaults = Record<string, Record<string, unknown>>

/** Start a workspace/latest/version execution. */
export function startExecution(data: { reportOid: string; source: CalcExecutionSource; defaults?: ExecutionDefaults; isSilent?: boolean; lastHtmlPath?: string | null }) { return httpClient.post<CalcExecution>('/calc/execution', { data }) }
/** Continue the original interactive process. */
export function continueExecution(executionId: string, defaults: ExecutionDefaults, lastHtmlPath?: string | null) { return httpClient.post<CalcExecution>(`/calc/execution/${executionId}/continue`, { data: { defaults, lastHtmlPath } }) }
/** List persisted execution audits. */
export function listExecutions(params: { offset?: number; limit?: number }) { return httpClient.get<PaginatedResult<CalcExecution>>('/calc/execution', { params }) }
/** Load one execution audit. */
export function getExecution(executionId: string) { return httpClient.get<CalcExecution>(`/calc/execution/${executionId}`) }
/** Terminate an active execution. */
export function terminateExecution(executionId: string) { return httpClient.delete<void>(`/calc/execution/${executionId}`) }
