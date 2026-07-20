/** Fixed filters displayed alongside persisted calculation-report categories. */

/** Identify report-list filters that are not persisted report categories. */
export const FixedReportCategoryFilter = {
  Favorites: 'favorites',
  Shared: 'shared'
} as const
export type FixedReportCategoryFilter = typeof FixedReportCategoryFilter[keyof typeof FixedReportCategoryFilter]

export type ReportCategorySelection = string | null
