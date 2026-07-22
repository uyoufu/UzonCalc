/** Typed APIs for version sharing and receiver-owned imports. */

import { httpClient } from 'src/api/base/httpClient'
import { useConfig } from 'src/config'
import type { ReportSyncStatus, ShareAccessType, SharedReport, ShareLink, SharePreview } from './types'

export interface ShareLinkInput { versionName: string; accessType: ShareAccessType; recipientUserOids?: string[]; recipientDepartmentOids?: string[]; canEdit: boolean; canShare: boolean; expiresAt?: string | null; maxUseCount?: number | null; note?: string | null }
export interface ShareUserOption { userOid: string; username: string; nickName: string | null }
export interface ShareDepartmentOption { departmentOid: string; parentOid: string | null; name: string }

/** Create a share link and return its stable owner-visible token. */
export function createShareLink(reportOid: string, data: ShareLinkInput) { return httpClient.post<ShareLink>(`/calc-report/${reportOid}/shares`, { data }) }
/** List owned share links with their stable owner-visible tokens. */
export function listShareLinks(reportOid: string) { return httpClient.get<ShareLink[]>(`/calc-report/${reportOid}/shares`) }
/** Replace the settings of one active share link without rotating its token. */
export function updateShareLink(shareOid: string, data: ShareLinkInput) { return httpClient.put<ShareLink>(`/calc-report/shares/${shareOid}`, { data }) }
/** Revoke one share link idempotently. */
export function revokeShareLink(shareOid: string) { return httpClient.delete<ShareLink>(`/calc-report/shares/${shareOid}`) }
/** Preview a share without consuming it. */
export function previewShare(token: string) { return httpClient.get<SharePreview>(`/calc-report/shared/${token}/preview`) }
/** Import a complete approved share closure. */
export function importShare(token: string, categoryOid: string, name?: string | null, shouldSync = false) { return httpClient.post<{ reportOid: string; versionName: string; importedReportCount: number }>(`/calc-report/shared/${token}/import`, { data: { categoryOid, name, shouldSync } }) }
/** Preview a cross-backend public share through the local SSRF boundary. */
export function previewRemoteShare(source: string) { return httpClient.post<SharePreview>('/calc-report/imports/link/preview', { data: { source } }) }
/** Download a local share after applying public or authenticated audience rules. */
export function downloadShare(token: string) { return httpClient.getBlob(`/calc-report/shared/${token}/archive`) }
/** Proxy-download a remote public share through the local SSRF boundary. */
export function downloadRemoteShare(source: string) { return httpClient.postBlob('/calc-report/imports/link/archive', { data: { source } }) }
/** Import a cross-backend public share through its v4 archive. */
export function importRemoteShare(source: string, categoryOid: string, name?: string | null, shouldSync = false) { return httpClient.post<{ reportOid: string; versionName: string; importedReportCount: number }>('/calc-report/imports/link', { data: { source, categoryOid, name, shouldSync } }) }
/** Count same-backend shares available to the current user. */
export function countSharedReports(query?: string) { return httpClient.get<number>('/calc-report/shared/count', { params: { query } }) }
/** List one page of same-backend shares available to the current user. */
export function listSharedReports(params: { query?: string; skip: number; limit: number; sortBy: string; descending: boolean }) { return httpClient.get<SharedReport[]>('/calc-report/shared/items', { params }) }
/** Import one same-backend catalog share. */
export function importCatalogShare(shareOid: string, categoryOid: string, name?: string | null, shouldSync = false) { return httpClient.post<{ reportOid: string; versionName: string; importedReportCount: number }>(`/calc-report/shared/catalog/${shareOid}/import`, { data: { categoryOid, name, shouldSync } }) }
/** Download an authorized same-backend catalog share archive. */
export function exportCatalogShare(shareOid: string) { return httpClient.getBlob(`/calc-report/shared/catalog/${shareOid}/archive`) }
/** Check a synchronized report's upstream state. */
export function getReportSyncStatus(reportOid: string) { return httpClient.get<ReportSyncStatus>(`/calc-report/${reportOid}/sync`) }
/** Atomically update a synchronized report to upstream latest. */
export function synchronizeReport(reportOid: string) { return httpClient.post<ReportSyncStatus>(`/calc-report/${reportOid}/sync`) }
/** Search active users available to specified-user shares. */
export function listShareUserOptions(query?: string) { return httpClient.get<ShareUserOption[]>('/calc-report/share-directory/users', { params: { query } }) }
/** List departments available to department-scoped shares. */
export function listShareDepartmentOptions() { return httpClient.get<ShareDepartmentOption[]>('/calc-report/share-directory/departments') }

/** Build the browser-facing URL for one stable owner-visible share token. */
export function buildFrontendShareUrl(token: string): string {
  const config = useConfig()
  const backendUrl = new URL(`${config.baseUrl}${config.api}/calc-report/shared/${token}/preview`, window.location.origin)
  const source = btoa(backendUrl.toString()).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '')
  const frontendUrl = new URL('/calc-report/shared/import', window.location.origin)
  frontendUrl.searchParams.set('source', source)
  return frontendUrl.toString()
}

/** Resolve one local or remote share-result path without leaking local credentials remotely. */
export function resolveShareResultUrl(path: string, isLocalBackend: boolean, authToken = ''): string {
  const url = new URL(path, useConfig().baseUrl)
  if (isLocalBackend && authToken) url.searchParams.set('token', authToken)
  return url.toString()
}

/** Resolve either a frontend share URL or a direct backend URL to its backend source. */
export function resolveBackendShareSource(value: string): string {
  const candidate = new URL(value.trim(), window.location.origin)
  const source = candidate.searchParams.get('source')
  if (!source) return candidate.toString()
  return atob(source.replaceAll('-', '+').replaceAll('_', '/').padEnd(Math.ceil(source.length / 4) * 4, '='))
}
