import { httpClient } from 'src/api/base/httpClient'

/**
 * 计算报告信息接口
 */
export interface ICalcReportInfo {
  id: number
  oid: string
  userId: number
  categoryId: number
  name: string
  description?: string | null
  cover?: string | null
}

import type { ICategoryInfo } from 'src/components/categoryList/types'

/**
 * 获取计算报告详情
 * @param reportOid 报告OID
 * @param stopNotifyError 是否停止通知错误，默认为 false, 为 true, 错误提示将由调用方处理
 */
export function getCalcReport(reportOid: string, stopNotifyError = false) {
  return httpClient.get<ICalcReportInfo>(`/calc-report/${reportOid}`, { stopNotifyError })
}

/**
 * 获取计算报告所属的分类信息
 * @param reportOid 报告OID
 */
export function getCalcReportCategory(reportOid: string) {
  return httpClient.get<ICategoryInfo>(`/calc-report/${reportOid}/category`)
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
  return httpClient.post<ICalcReportInfo[]>('/calc-report/list', { data })
}

/**
 * 保存计算报告文件
 * @param data 保存请求数据（包含报告名称和代码内容）
 */
export function saveCalcReport(data: { reportName: string; code: string; reportOid?: string; categoryOid?: string }) {
  return httpClient.post<string>('/calc-report/save', { data })
}

/**
 * 更新计算报告
 * @param reportOid 报告OID
 * @param data 更新数据
 */
export function updateCalcReport(
  reportOid: string,
  data: {
    name: string
    description?: string | null
    categoryId: number
    cover?: string | null
  }
) {
  return httpClient.put<ICalcReportInfo>(`/calc-report/${reportOid}`, { data })
}

/**
 * 删除计算报告
 * @param reportOid 报告OID
 */
export function deleteCalcReport(reportOid: string) {
  return httpClient.delete(`/calc-report/${reportOid}`)
}
