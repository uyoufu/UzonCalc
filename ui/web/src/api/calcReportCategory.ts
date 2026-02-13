import { httpClient } from 'src/api/base/httpClient'
import type { ICategoryInfo } from 'src/components/categoryList/types'

/**
 * 获取所有计算报告分类
 * @returns 分类列表
 */
export function getCalcReportCategories() {
  return httpClient.get<ICategoryInfo[]>('/calc-report-category/list')
}

/**
 * 获取单个计算报告分类
 * @param categoryOid 分类 OID
 * @returns 分类信息
 */
export function getCalcReportCategory(categoryOid: string) {
  return httpClient.get<ICategoryInfo>(`/calc-report-category/${categoryOid}`)
}

/**
 * 创建计算报告分类
 * @param data 分类信息
 * @returns 创建后的分类信息
 */
export function createCalcReportCategory(data: {
  name: string
  order?: number
  description?: string | null
  cover?: string | null
}) {
  return httpClient.post<ICategoryInfo>('/calc-report-category', {
    data
  })
}

/**
 * 更新计算报告分类
 * @param categoryOid 分类ID
 * @param data 分类信息
 * @returns 更新后的分类信息
 */
export function updateCalcReportCategory(categoryOid: string, data: Partial<ICategoryInfo>) {
  return httpClient.put<ICategoryInfo>(`/calc-report-category/${categoryOid}`, {
    data
  })
}

/**
 * 删除计算报告分类
 * @param categoryOid 分类ID
 */
export function deleteCalcReportCategory(categoryOid: string) {
  return httpClient.delete(`/calc-report-category/${categoryOid}`)
}

/**
 * 获取或创建默认分类
 * 如果用户没有任何有效分类，则使用默认名称创建一个分类后返回
 * @param defaultCategoryName 默认分类名称
 * @returns 分类信息
 */
export function getOrCreateDefaultCategory(defaultCategoryName: string) {
  return httpClient.post<ICategoryInfo>('/calc-report-category/default', {
    data: { defaultCategoryName }
  })
}
