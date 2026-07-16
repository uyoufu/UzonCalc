/** Typed APIs for version sharing and receiver-owned imports. */

import { httpClient } from 'src/api/base/httpClient'
import type { ShareAccessType, ShareLink, SharePreview } from './types'

export interface ShareLinkInput { versionName: string; accessType: ShareAccessType; recipientUserOids?: string[]; expiresAt?: string | null; maxUseCount?: number | null }

/** Create a share link and return its one-time secret token. */
export function createShareLink(reportOid: string, data: ShareLinkInput) { return httpClient.post<ShareLink>(`/calc-report/${reportOid}/shares`, { data }) }
/** List share links without their secret tokens. */
export function listShareLinks(reportOid: string) { return httpClient.get<ShareLink[]>(`/calc-report/${reportOid}/shares`) }
/** Revoke one share link idempotently. */
export function revokeShareLink(shareOid: string) { return httpClient.delete<ShareLink>(`/calc-report/shares/${shareOid}`) }
/** Preview a share without consuming it. */
export function previewShare(token: string) { return httpClient.get<SharePreview>(`/calc-report/shared/${token}/preview`) }
/** Import a complete approved share closure. */
export function importShare(token: string, categoryOid: string, name?: string | null) { return httpClient.post<{ reportOid: string; versionName: string; importedReportCount: number }>(`/calc-report/shared/${token}/import`, { data: { categoryOid, name } }) }
