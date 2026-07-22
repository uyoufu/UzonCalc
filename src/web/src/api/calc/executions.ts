/** Typed APIs for managed calculation execution slots. */

import { httpClient } from 'src/api/base/httpClient'
import type { CalcExecution, CalcExecutionSource } from './types'

export type ExecutionDefaults = Record<string, Record<string, unknown>>

/** Start a workspace/latest/version execution. */
export function startExecution(data: { reportOid: string; source: CalcExecutionSource; defaults?: ExecutionDefaults; isSilent?: boolean; lastHtmlPath?: string | null }) { return httpClient.post<CalcExecution>('/calc/execution', { data }) }
/** Continue the original interactive process. */
export function continueExecution(executionId: string, defaults: ExecutionDefaults, lastHtmlPath?: string | null) { return httpClient.post<CalcExecution>(`/calc/execution/${executionId}/continue`, { data: { defaults, lastHtmlPath } }) }
/** Load the active or last-successful execution for one report source. */
export function getCurrentExecution(reportOid: string, source: CalcExecutionSource) {
  return httpClient.get<CalcExecution | null>('/calc/execution/current', {
    params: { reportOid, sourceType: source.type, versionName: source.versionName }
  })
}
/** Load one execution audit. */
export function getExecution(executionId: string) { return httpClient.get<CalcExecution>(`/calc/execution/${executionId}`) }
/** Terminate an active execution. */
export function terminateExecution(executionId: string) { return httpClient.delete<void>(`/calc/execution/${executionId}`) }
