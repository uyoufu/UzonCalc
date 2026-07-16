/** Typed HTTP functions for calculation-report metadata. */

import { httpClient } from 'src/api/base/httpClient'
import type { CalcReport, WorkspaceSnapshot } from './types'

export interface ReportListParams {
  categoryOid?: string
  query?: string
  favoriteOnly?: boolean
}

export interface ReportItemsParams extends ReportListParams {
  skip: number
  limit: number
  sortBy: string
  descending: boolean
}

export interface ReportMetadataInput {
  categoryOid: string
  name: string
  description?: string | null
  cover?: string | null
}

/** Count reports owned by the current user. */
export function countCalcReports(params: ReportListParams) {
  return httpClient.get<number>('/calc-report/count', { params })
}

/** List one page of reports owned by the current user. */
export function listCalcReports(params: ReportItemsParams) {
  return httpClient.get<CalcReport[]>('/calc-report/items', { params })
}

/** Load one report by OID. */
export function getCalcReport(reportOid: string) {
  return httpClient.get<CalcReport>(`/calc-report/${reportOid}`)
}

/** Update report display metadata. */
export function updateCalcReport(reportOid: string, data: ReportMetadataInput) {
  return httpClient.put<CalcReport>(`/calc-report/${reportOid}`, { data })
}

/** Copy a report workspace into a new owned report. */
export function copyCalcReport(reportOid: string, data: ReportMetadataInput & { reportOid?: string }) {
  return httpClient.post<CalcReport>(`/calc-report/${reportOid}/copy`, { data })
}

/** Change the current user's favorite state for a report. */
export function setCalcReportFavorite(reportOid: string, isFavorite: boolean) {
  return isFavorite
    ? httpClient.put<CalcReport>(`/calc-report/${reportOid}/favorite`)
    : httpClient.delete<CalcReport>(`/calc-report/${reportOid}/favorite`)
}

/** Soft-delete an owned report. */
export function deleteCalcReport(reportOid: string) {
  return httpClient.delete<void>(`/calc-report/${reportOid}`)
}

/** Import one legacy UZC archive as an unpublished workspace. */
export function importUzcReport(categoryOid: string, name: string, archive: File) {
  const data = new FormData()
  data.append('categoryOid', categoryOid)
  data.append('name', name)
  data.append('archive', archive, archive.name)
  return httpClient.postForm<WorkspaceSnapshot>('/calc-report/imports/uzc', { data })
}
