import { httpClient } from 'src/api/base/httpClient'
import type { ICategoryInfo } from 'src/components/categoryList/types'

export interface ICalcReportCategory extends ICategoryInfo {
  userId: number
  status: number
  cover?: string
  total: number
}

/**
 * 获取所有计算报告分类
 * @returns 分类列表
 */
export function getCalcReportCategories () {
  return httpClient.get<ICalcReportCategory[]>('/calc-report-category/list')
}

/**
 * 创建计算报告分类
 * @param data 分类信息
 * @returns 创建后的分类信息
 */
export function createCalcReportCategory (data: {
  name: string
  order: number
  description?: string | null
  cover?: string | null
}) {
  return httpClient.post<ICalcReportCategory>('/calc-report-category', {
    data
  })
}

/**
 * 更新计算报告分类
 * @param id 分类ID
 * @param data 分类信息
 * @returns 更新后的分类信息
 */
export function updateCalcReportCategory (id: number, data: Partial<ICalcReportCategory>) {
  return httpClient.put<ICalcReportCategory>(`/calc-report-category/${id}`, {
    data
  })
}

/**
 * 删除计算报告分类
 * @param id 分类ID
 */
export function deleteCalcReportCategory (id: number) {
  return httpClient.delete(`/calc-report-category/${id}`)
}
