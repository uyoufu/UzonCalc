<template>
  <div class="report-library row no-wrap full-height">
    <ReportCategoryPanel v-model="selectedCategoryOid" :categories="categories" @create="onOpenCategoryDialog()"
      @edit="onOpenCategoryDialog" @delete="onDeleteCategory" @reorder="onReorderCategories" />
    <ReportTable v-model:filter="filter" v-model:pagination="pagination" :reports="reports" :loading="loading"
      :context-menu-items="contextMenuItems" @request="onTableRequest" @create="onCreateReport"
      @import="onOpenImportDialog" @open="onOpenReport" @favorite="onToggleFavorite" />
  </div>
</template>

<script setup lang="ts">
/** Report-library page that coordinates categories, pagination, and row commands. */
defineOptions({ name: 'CalcReportList' })

import ReportCategoryPanel from './components/ReportCategoryPanel.vue'
import ReportTable from './components/ReportTable.vue'
import type { CalcReport, CalcReportCategory } from 'src/api/calc/types'
import { createReportCategory, deleteReportCategory, listReportCategories, reorderReportCategories, updateReportCategory } from 'src/api/calc/categories'
import { copyCalcReport, countCalcReports, deleteCalcReport, importUzcReport, listCalcReports, setCalcReportFavorite, updateCalcReport } from 'src/api/calc/reports'
import { showCalcReportInExplorer } from 'src/api/desktop'
import { useReportContextMenu } from './components/useReportContextMenu'
import { useCalcReportListDialogs } from './compositions/useCalcReportListDialogs'
import { useShareManagerDialog } from '../shared/useShareManagerDialog'
import { useSystemInfo } from 'src/stores/system'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'
import { useQTable } from 'src/compositions/qTableUtils'
import type { IRequestPagination, TTableFilterObject } from 'src/compositions/types'

const router = useRouter()
const systemInfo = useSystemInfo()
const categories = ref<CalcReportCategory[]>([])
const selectedCategoryOid = ref<string | null>(null)
const categoryOptions = computed(() => categories.value.map((category) => ({ label: category.name, value: category.categoryOid })))
const { openCategoryDialog, openReportDialog, openImportDialog } = useCalcReportListDialogs()
const { openShareManagerDialog } = useShareManagerDialog()

/** Refresh report categories and their derived counts. */
async function loadCategories(): Promise<void> {
  const response = await listReportCategories()
  categories.value = response.data || []
}

/** Convert table search and category state into API filters. */
function createReportFilter(filterValue: string): TTableFilterObject {
  const tableFilter: TTableFilterObject = { filter: filterValue }
  if (selectedCategoryOid.value) tableFilter.categoryOid = selectedCategoryOid.value
  return tableFilter
}

/** Return API filter parameters without the internal refresh counter. */
function getReportApiFilters(tableFilter: TTableFilterObject): { categoryOid?: string; query?: string } {
  return {
    categoryOid: typeof tableFilter.categoryOid === 'string' ? tableFilter.categoryOid : undefined,
    query: typeof tableFilter.filter === 'string' && tableFilter.filter ? tableFilter.filter : undefined
  }
}

/** Count reports matching the active table filters. */
async function getReportCount(tableFilter: TTableFilterObject): Promise<number> {
  return (await countCalcReports(getReportApiFilters(tableFilter))).data || 0
}

/** Request one sorted report page. */
async function requestReportItems(tableFilter: TTableFilterObject, pageRequest: IRequestPagination): Promise<CalcReport[]> {
  return (await listCalcReports({ ...getReportApiFilters(tableFilter), ...pageRequest })).data || []
}

const {
  rows: reports,
  pagination,
  filter,
  loading,
  onTableRequest,
  refreshTable,
  updateExistOne,
  deleteRowById
} = useQTable<CalcReport>({
  sortBy: 'updatedAt',
  descending: true,
  rowsPerPage: 20,
  filterFactor: createReportFilter,
  getRowsNumberCount: getReportCount,
  onRequest: requestReportItems
})

onMounted(loadCategories)
watch(filter, () => {
  pagination.value.page = 1
}, { flush: 'sync' })
watch(selectedCategoryOid, () => {
  pagination.value.page = 1
  refreshTable()
})

/** Navigate to a preallocated new workspace. */
async function onCreateReport(): Promise<void> {
  await router.push({ path: '/calc-report/new', query: { categoryOid: selectedCategoryOid.value || categories.value[0]?.categoryOid } })
}
/** Open a report workspace. */
async function onOpenReport(report: CalcReport): Promise<void> { await router.push(`/calc-report/${report.reportOid}/workspace`) }
/** Open latest execution for a report. */
async function onRunReport(report: CalcReport): Promise<void> { await router.push({ path: `/calc-report/${report.reportOid}/run`, query: { source: 'latest' } }) }
/** Open immutable versions for a report. */
async function onOpenVersions(report: CalcReport): Promise<void> { await router.push(`/calc-report/${report.reportOid}/versions`) }

/** Open category metadata and persist a confirmed change. */
async function onOpenCategoryDialog(category?: CalcReportCategory): Promise<void> {
  const input = await openCategoryDialog(category)
  if (!input) return

  if (category) await updateReportCategory(category.categoryOid, input)
  else await createReportCategory(input)
  await loadCategories()
}
/** Delete an empty category after confirmation. */
async function onDeleteCategory(category: CalcReportCategory): Promise<void> {
  if (!await confirmOperation(t('global.deleteConfirmation'), category.name)) return
  await deleteReportCategory(category.categoryOid)
  if (selectedCategoryOid.value === category.categoryOid) selectedCategoryOid.value = null
  await loadCategories()
}
/** Persist drag-and-drop report-category ordering. */
async function onReorderCategories(value: CalcReportCategory[]): Promise<void> {
  categories.value = value
  const response = await reorderReportCategories(value.map((category) => ({ categoryOid: category.categoryOid, sortOrder: category.sortOrder })))
  categories.value = response.data || value
}

/** Open report metadata or copy controls and refresh confirmed changes. */
async function onOpenReportDialog(report: CalcReport, mode: 'edit' | 'copy'): Promise<void> {
  const input = await openReportDialog(report, mode, categoryOptions.value)
  if (!input) return

  const updatedReport = mode === 'copy'
    ? (await copyCalcReport(report.reportOid, input)).data
    : (await updateCalcReport(report.reportOid, input)).data
  await loadCategories()
  const hasCategoryMismatch = Boolean(selectedCategoryOid.value && updatedReport.categoryOid !== selectedCategoryOid.value)
  if (mode === 'copy' || filter.value || hasCategoryMismatch) {
    pagination.value.page = 1
    refreshTable()
    return
  }
  updateExistOne(updatedReport, 'reportOid')
}
/** Toggle favorite state and patch only the affected row. */
async function onToggleFavorite(report: CalcReport): Promise<void> {
  const response = await setCalcReportFavorite(report.reportOid, !report.isFavorite)
  updateExistOne(response.data, 'reportOid')
}
/** Delete a report and refresh its category count. */
async function onDeleteReport(report: CalcReport): Promise<void> {
  if (!await confirmOperation(t('global.deleteConfirmation'), report.name)) return
  await deleteCalcReport(report.reportOid)
  deleteRowById(report.reportOid, 'reportOid')
  await loadCategories()
}
/** Import a UZC archive and refresh the report library after success. */
async function onOpenImportDialog(): Promise<void> {
  const input = await openImportDialog(categoryOptions.value)
  if (!input) return

  await importUzcReport(input.categoryOid, input.name, input.archive)
  await loadCategories()
  pagination.value.page = 1
  refreshTable()
  notifySuccess(t('calcWorkspace.importComplete'))
}
/** Open share-link management in the existing report dialog. */
async function onShareReport(report: CalcReport): Promise<void> {
  await openShareManagerDialog(report.reportOid, report.name)
}
const { items: contextMenuItems } = useReportContextMenu({
  open: onOpenReport,
  run: onRunReport,
  versions: onOpenVersions,
  edit: (report) => onOpenReportDialog(report, 'edit'),
  copy: (report) => onOpenReportDialog(report, 'copy'),
  favorite: onToggleFavorite,
  share: onShareReport,
  showInExplorer: async (report) => { await showCalcReportInExplorer(report.reportOid) },
  remove: onDeleteReport,
  isDesktop: () => systemInfo.isLocalhost
})
</script>

<style scoped>
.report-library {
  min-height: 620px;
  height: 100%;
  background: #fff;
  overflow: hidden;
}

@media (max-width: 900px) {
  .report-library {
    overflow-x: auto;
  }
}
</style>
