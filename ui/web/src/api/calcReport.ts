import { httpClient } from 'src/api/base/httpClient'

/**
 * 计算报告信息接口
 */
export interface CalcReportInfo {
  id: number
  oid: string
  userId: number
  categoryId: number
  name: string
  description?: string | null
  cover?: string | null
}

/**
 * 获取计算报告详情
 * @param reportOid 报告OID
 */
export function getCalcReport (reportOid: string) {
  return httpClient.get<CalcReportInfo>(`/calc-report/${reportOid}`)
}

/**
 * 获取计算报告列表
 */
export function listCalcReports (data: {
  categoryId?: number
  filter?: string
  pagination: {
    skip: number
    limit: number
    sortBy?: string
    descending?: boolean
  }
}) {
  return httpClient.post<{
    items: CalcReportInfo[]
    total: number
    skip: number
    limit: number
  }>('/calc-report/list', { data })
}
