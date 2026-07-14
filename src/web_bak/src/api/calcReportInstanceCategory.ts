import { httpClient } from 'src/api/base/httpClient'
import type { ICategoryInfo } from 'src/components/categoryList/types'

export function getCalcReportInstanceCategories() {
  return httpClient.get<ICategoryInfo[]>('/calc-report-instance-category/list')
}

export function getCalcReportInstanceCategory(categoryOid: string) {
  return httpClient.get<ICategoryInfo>(`/calc-report-instance-category/${categoryOid}`)
}

export function createCalcReportInstanceCategory(data: {
  name: string
  order?: number
  description?: string | null
}) {
  return httpClient.post<ICategoryInfo>('/calc-report-instance-category', { data })
}

export function updateCalcReportInstanceCategory(categoryOid: string, data: Partial<ICategoryInfo>) {
  return httpClient.put<ICategoryInfo>(`/calc-report-instance-category/${categoryOid}`, { data })
}

export function deleteCalcReportInstanceCategory(categoryOid: string) {
  return httpClient.delete(`/calc-report-instance-category/${categoryOid}`)
}

export function getOrCreateDefaultInstanceCategory(defaultCategoryName: string) {
  return httpClient.post<ICategoryInfo>('/calc-report-instance-category/default', {
    data: { defaultCategoryName }
  })
}
