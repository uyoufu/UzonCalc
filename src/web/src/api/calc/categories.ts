/** Typed category APIs for reports and saved calculation instances. */

import { httpClient } from 'src/api/base/httpClient'
import type { CalcInstanceCategory, CalcReportCategory } from './types'

export interface CategoryInput { name: string; description?: string | null }

/** List report categories. */
export function listReportCategories() { return httpClient.get<CalcReportCategory[]>('/calc-report-category') }
/** Create a report category. */
export function createReportCategory(data: CategoryInput) { return httpClient.post<CalcReportCategory>('/calc-report-category', { data }) }
/** Get or create a report category by its default name. */
export function ensureDefaultReportCategory(data: CategoryInput) { return httpClient.post<CalcReportCategory>('/calc-report-category/default', { data }) }
/** Update a report category. */
export function updateReportCategory(categoryOid: string, data: CategoryInput) { return httpClient.put<CalcReportCategory>(`/calc-report-category/${categoryOid}`, { data }) }
/** Replace report category ordering. */
export function reorderReportCategories(data: Array<{ categoryOid: string; manualOrder: number }>) { return httpClient.put<CalcReportCategory[]>('/calc-report-category/order', { data }) }
/** Update report-category pinning or visibility. */
export function updateReportCategoryState(categoryOid: string, data: { isPinned?: boolean; isHidden?: boolean }) { return httpClient.put<CalcReportCategory>(`/calc-report-category/${categoryOid}/state`, { data }) }
/** Record category use for LFU-Aging ordering. */
export function recordReportCategoryAccess(categoryOid: string) { return httpClient.post<CalcReportCategory>(`/calc-report-category/${categoryOid}/access`) }
/** Delete an empty report category. */
export function deleteReportCategory(categoryOid: string) { return httpClient.delete<void>(`/calc-report-category/${categoryOid}`) }

/** List instance categories. */
export function listInstanceCategories() { return httpClient.get<CalcInstanceCategory[]>('/calc-report-instance-category') }
/** Create an instance category. */
export function createInstanceCategory(data: CategoryInput) { return httpClient.post<CalcInstanceCategory>('/calc-report-instance-category', { data }) }
/** Get or create an instance category by its default name. */
export function ensureDefaultInstanceCategory(data: CategoryInput) { return httpClient.post<CalcInstanceCategory>('/calc-report-instance-category/default', { data }) }
/** Update an instance category. */
export function updateInstanceCategory(categoryOid: string, data: CategoryInput) { return httpClient.put<CalcInstanceCategory>(`/calc-report-instance-category/${categoryOid}`, { data }) }
/** Delete an empty instance category. */
export function deleteInstanceCategory(categoryOid: string) { return httpClient.delete<void>(`/calc-report-instance-category/${categoryOid}`) }
