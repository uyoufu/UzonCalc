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
export function getCalcReport(reportOid: string) {
  return httpClient.get<CalcReportInfo>(`/calc-report/${reportOid}`)
}

export function countCalcReports(data: { categoryId?: number; filter?: string }) {
  return httpClient.post<number>('/calc-report/count', { data })
}

/**
 * 获取计算报告列表
 */
export function listCalcReports(data: {
  categoryId?: number
  filter?: string
  pagination: {
    skip: number
    limit: number
    sortBy?: string
    descending?: boolean
  }
}) {
  return httpClient.post<CalcReportInfo[]>('/calc-report/list', { data })
}

/**
 * 保存计算报告文件
 * @param data 保存请求数据（包含报告名称和代码内容）
 */
export function saveCalcReport(data: { reportName: string; code: string; reportOid?: string; categoryOid?: string }) {
  return httpClient.post<string>('/calc-report/save', { data })
}
