<template>
  <div class="report-library row no-wrap full-height">
    <ReportCategoryPanel v-model="selectedCategoryOid" :categories="categories" @create="onOpenCategoryDialog()"
      @edit="onOpenCategoryDialog" @delete="onDeleteCategory" @reorder="onReorderCategories" />
    <ReportTable v-model:query="query" :reports="reports" :loading="isLoading" :total="total" :page="page"
      :rows-per-page="rowsPerPage" :context-menu-items="contextMenuItems" @request="onTableRequest"
      @create="onCreateReport" @import="onOpenImportDialog" @open="onOpenReport" @favorite="onToggleFavorite" />
  </div>
</template>

<script setup lang="ts">
/** Report-library page that coordinates categories, pagination, and row commands. */
defineOptions({ name: 'CalcReportList' })

import ReportCategoryPanel from './components/ReportCategoryPanel.vue'
import ReportTable from './components/ReportTable.vue'
import type { CalcReport, CalcReportCategory } from 'src/api/calc/types'
import { createReportCategory, deleteReportCategory, listReportCategories, reorderReportCategories, updateReportCategory } from 'src/api/calc/categories'
import { copyCalcReport, deleteCalcReport, importUzcReport, listCalcReports, setCalcReportFavorite, updateCalcReport } from 'src/api/calc/reports'
import { showCalcReportInExplorer } from 'src/api/desktop'
import { useReportContextMenu } from './components/useReportContextMenu'
import { useCalcReportListDialogs } from './compositions/useCalcReportListDialogs'
import { useShareManagerDialog } from '../shared/useShareManagerDialog'
import { useSystemInfo } from 'src/stores/system'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'

const router = useRouter()
const systemInfo = useSystemInfo()
const categories = ref<CalcReportCategory[]>([])
const selectedCategoryOid = ref<string | null>(null)
const reports = ref<CalcReport[]>([])
const query = ref('')
const total = ref(0)
const page = ref(1)
const rowsPerPage = ref(20)
const isLoading = ref(false)
const categoryOptions = computed(() => categories.value.map((category) => ({ label: category.name, value: category.categoryOid })))
const { openCategoryDialog, openReportDialog, openImportDialog } = useCalcReportListDialogs()
const { openShareManagerDialog } = useShareManagerDialog()

/** Refresh report categories and their derived counts. */
async function loadCategories(): Promise<void> {
  const response = await listReportCategories()
  categories.value = response.data || []
}

/** Load one page of reports from the current filter. */
async function loadReports(): Promise<void> {
  isLoading.value = true
  try {
    const response = await listCalcReports({
      categoryOid: selectedCategoryOid.value || undefined,
      query: query.value || undefined,
      offset: (page.value - 1) * rowsPerPage.value,
      limit: rowsPerPage.value
    })
    reports.value = response.data?.items || []
    total.value = response.data?.total || 0
  } finally {
    isLoading.value = false
  }
}

watch([selectedCategoryOid, query], async () => { page.value = 1; await loadReports() })
onMounted(async () => { await Promise.all([loadCategories(), loadReports()]) })

/** Apply server-side table pagination. */
async function onTableRequest(nextPage: number, nextRowsPerPage: number): Promise<void> {
  page.value = nextPage
  rowsPerPage.value = nextRowsPerPage
  await loadReports()
}

/** Navigate to a preallocated new workspace. */
async function onCreateReport(): Promise<void> {
  await router.push({ path: '/calc-report/new', query: { categoryOid: selectedCategoryOid.value || categories.value[0]?.categoryOid } })
}
/** Open a report workspace. */
async function onOpenReport(report: CalcReport): Promise<void> { await router.push(`/calc-report/${report.reportOid}/workspace`) }
/** Open latest execution for a report. */
async function onRunReport(report: CalcReport): Promise<void> { await router.push({ path: `/calc-report/${report.reportOid}/run`, query: { source: 'latest' } }) }

/** Open category metadata and persist a confirmed change. */
async function onOpenCategoryDialog(category?: CalcReportCategory): Promise<void> {
  const isSaved = await openCategoryDialog(category, async (input) => {
    if (category) await updateReportCategory(category.categoryOid, input)
    else await createReportCategory(input)
  })
  if (isSaved) await loadCategories()
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
  const isSaved = await openReportDialog(report, mode, categoryOptions.value, async (input) => {
    if (mode === 'copy') await copyCalcReport(report.reportOid, input)
    else {
      const response = await updateCalcReport(report.reportOid, input)
      Object.assign(report, response.data)
    }
  })
  if (!isSaved) return
  await Promise.all([loadReports(), loadCategories()])
}
/** Toggle favorite state and patch only the affected row. */
async function onToggleFavorite(report: CalcReport): Promise<void> {
  const response = await setCalcReportFavorite(report.reportOid, !report.isFavorite)
  Object.assign(report, response.data)
}
/** Delete a report and refresh its category count. */
async function onDeleteReport(report: CalcReport): Promise<void> {
  if (!await confirmOperation(t('global.deleteConfirmation'), report.name)) return
  await deleteCalcReport(report.reportOid)
  reports.value = reports.value.filter((candidate) => candidate.reportOid !== report.reportOid)
  total.value -= 1
  await loadCategories()
}
/** Import a UZC archive and refresh the report library after success. */
async function onOpenImportDialog(): Promise<void> {
  const isImported = await openImportDialog(categoryOptions.value, async (input) => {
    await importUzcReport(input.categoryOid, input.name, input.archive)
  })
  if (!isImported) return
  await Promise.all([loadReports(), loadCategories()])
  notifySuccess(t('calcWorkspace.importComplete'))
}
/** Open the shared report-link manager from a row action. */
async function onShareReport(report: CalcReport): Promise<void> {
  await openShareManagerDialog(report.reportOid, report.name)
}

const { items: contextMenuItems } = useReportContextMenu({
  open: onOpenReport,
  run: onRunReport,
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
