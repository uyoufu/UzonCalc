/* eslint-disable @typescript-eslint/no-explicit-any */
import { httpClient } from 'src/api/base/httpClient'

export interface ICalcReportInstanceInfo {
  id: number
  oid: string
  userId: number
  categoryId: number
  reportId: number
  reportOid: string
  reportName?: string | null
  name: string
  description?: string | null
  defaults: Record<string, Record<string, any>>
  resultPath?: string | null
  createdAt: string
  version: number
  lastModified: string
}

export function getCalcReportInstance(instanceOid: string) {
  return httpClient.get<ICalcReportInstanceInfo>(`/calc-report-instance/${instanceOid}`)
}

export function countCalcReportInstances(data: { categoryId?: number; filter?: string }) {
  return httpClient.post<number>('/calc-report-instance/count', { data })
}

export function listCalcReportInstances(data: {
  categoryId?: number
  filter?: string
  pagination: {
    skip: number
    limit: number
    sortBy?: string
    descending?: boolean
  }
}) {
  return httpClient.post<ICalcReportInstanceInfo[]>('/calc-report-instance/list', { data })
}

export function saveCalcReportInstance(data: {
  name: string
  description?: string | null
  categoryId: number
  reportOid: string
  defaults: Record<string, Record<string, any>>
  resultPath: string
}) {
  return httpClient.post<ICalcReportInstanceInfo>('/calc-report-instance', { data })
}

export function updateCalcReportInstance(
  instanceOid: string,
  data: {
    name: string
    description?: string | null
    categoryId: number
  }
) {
  return httpClient.put<ICalcReportInstanceInfo>(`/calc-report-instance/${instanceOid}`, { data })
}

export function updateCalcReportInstanceResult(
  instanceOid: string,
  data: {
    name: string
    description?: string | null
    categoryId: number
    reportOid: string
    defaults: Record<string, Record<string, any>>
    resultPath: string
  }
) {
  return httpClient.put<ICalcReportInstanceInfo>(`/calc-report-instance/${instanceOid}/result`, { data })
}

export function deleteCalcReportInstance(instanceOid: string) {
  return httpClient.delete(`/calc-report-instance/${instanceOid}`)
}
