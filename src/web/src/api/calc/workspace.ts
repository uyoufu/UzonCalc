/** Typed APIs for complete calculation-report workspaces. */

import { httpClient } from 'src/api/base/httpClient'
import type { ReportDependency, WorkspaceBuild, WorkspaceSaveRequest, WorkspaceSnapshot } from './types'

export interface WorkspaceUpload { path: string; content: Blob }

/** Save a complete optimistic workspace snapshot. */
export function saveWorkspace(reportOid: string, snapshot: WorkspaceSaveRequest, uploads: WorkspaceUpload[]) {
  const data = new FormData()
  data.append('snapshot', JSON.stringify(snapshot))
  uploads.forEach((upload) => data.append('files', upload.content, upload.path))
  return httpClient.put<WorkspaceSnapshot>(`/calc-report/${reportOid}/workspace`, { data })
}

/** Load workspace metadata without file bytes. */
export function getWorkspace(reportOid: string) { return httpClient.get<WorkspaceSnapshot>(`/calc-report/${reportOid}/workspace`) }
/** Load one workspace file as a Blob. */
export async function getWorkspaceFile(reportOid: string, path: string): Promise<Blob> {
  const response = await httpClient.getBlob(`/calc-report/${reportOid}/workspace/file`, { params: { path } })
  return response.data
}
/** Load dependency declarations for a workspace. */
export function getWorkspaceDependencies(reportOid: string) { return httpClient.get<ReportDependency[]>(`/calc-report/${reportOid}/workspace/dependencies`) }
/** Replace dependencies without modifying file bytes. */
export function replaceWorkspaceDependencies(reportOid: string, workspaceRevision: number, dependencies: ReportDependency[]) {
  return httpClient.put<WorkspaceSnapshot>(`/calc-report/${reportOid}/workspace/dependencies`, { data: { workspaceRevision, dependencies } })
}
/** Load lazy build state for the configured runtime. */
export function getWorkspaceBuild(reportOid: string) { return httpClient.get<WorkspaceBuild>(`/calc-report/${reportOid}/workspace/build`) }
