/** Typed APIs for immutable calculation-report versions. */

import { httpClient } from 'src/api/base/httpClient'
import type { CalcReportVersion, WorkspaceSnapshot } from './types'

/** Publish the current workspace. */
export function publishVersion(reportOid: string, versionName: string, description?: string | null) { return httpClient.post<CalcReportVersion>(`/calc-report/${reportOid}/versions`, { data: { versionName, description } }) }
/** List immutable versions. */
export function listVersions(reportOid: string) { return httpClient.get<CalcReportVersion[]>(`/calc-report/${reportOid}/versions`) }
/** Move the authoritative latest pointer. */
export function setLatestVersion(reportOid: string, versionName: string) { return httpClient.put<CalcReportVersion>(`/calc-report/${reportOid}/latest`, { data: { versionName } }) }
/** Restore one immutable version into the mutable workspace. */
export function restoreWorkspaceVersion(reportOid: string, versionName: string) { return httpClient.post<WorkspaceSnapshot>(`/calc-report/${reportOid}/workspace/restore`, { data: { versionName } }) }
