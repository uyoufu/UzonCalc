/** Fixed filters displayed alongside persisted calculation-report categories. */

/** Identify report-list filters that are not persisted report categories. */
export enum FixedReportCategoryFilter {
  Favorites = 'favorites'
}

export type ReportCategorySelection = string | FixedReportCategoryFilter | null
