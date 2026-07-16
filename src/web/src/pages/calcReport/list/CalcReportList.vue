<template>
  <div class="report-library row no-wrap full-height">
    <ReportCategoryPanel v-model="selectedCategoryOid" :categories="categories"
      @create="openCategoryDialog()" @edit="openCategoryDialog" @delete="onDeleteCategory" @reorder="onReorderCategories" />
    <ReportTable v-model:query="query" :reports="reports" :loading="isLoading" :total="total"
      :page="page" :rows-per-page="rowsPerPage" :context-menu-items="contextMenuItems"
      @request="onTableRequest" @create="onCreateReport" @import="isImportDialogOpen = true"
      @open="onOpenReport" @favorite="onToggleFavorite" />

    <q-dialog v-model="isCategoryDialogOpen">
      <q-card class="metadata-dialog">
        <q-card-section class="text-subtitle1">{{ editingCategory ? t('calcWorkspace.editCategory') : t('calcWorkspace.newCategory') }}</q-card-section>
        <q-card-section class="q-gutter-md">
          <q-input v-model="categoryForm.name" dense outlined autofocus :label="t('calcWorkspace.categoryName')" />
          <q-input v-model="categoryForm.description" dense outlined type="textarea" :label="t('calcWorkspace.description')" />
        </q-card-section>
        <q-card-actions align="right"><CancelBtn v-close-popup /><OkBtn :disable="!categoryForm.name.trim()" @click="onSaveCategory" /></q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isReportDialogOpen">
      <q-card class="metadata-dialog">
        <q-card-section class="text-subtitle1">{{ reportDialogMode === 'copy' ? t('calcWorkspace.copyReport') : t('calcWorkspace.editMetadata') }}</q-card-section>
        <q-card-section class="q-gutter-md">
          <q-select v-model="reportForm.categoryOid" dense outlined emit-value map-options :options="categoryOptions" :label="t('calcWorkspace.categoryName')" />
          <q-input v-model="reportForm.name" dense outlined autofocus :label="t('calcWorkspace.reportName')" />
          <q-input v-model="reportForm.description" dense outlined type="textarea" :label="t('calcWorkspace.description')" />
        </q-card-section>
        <q-card-actions align="right"><CancelBtn v-close-popup /><OkBtn :disable="!reportForm.name.trim() || !reportForm.categoryOid" @click="onSaveReportDialog" /></q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isImportDialogOpen">
      <q-card class="metadata-dialog">
        <q-card-section class="text-subtitle1">{{ t('calcWorkspace.importUzc') }}</q-card-section>
        <q-card-section class="q-gutter-md">
          <q-select v-model="importForm.categoryOid" dense outlined emit-value map-options :options="categoryOptions" :label="t('calcWorkspace.categoryName')" />
          <q-input v-model="importForm.name" dense outlined :label="t('calcWorkspace.reportName')" />
          <q-file v-model="importForm.archive" dense outlined accept=".uzc" :label="t('calcWorkspace.uzcFile')" />
        </q-card-section>
        <q-card-actions align="right"><CancelBtn v-close-popup /><OkBtn :loading="isImporting" :disable="!importForm.archive || !importForm.name.trim() || !importForm.categoryOid" @click="onImportUzc" /></q-card-actions>
      </q-card>
    </q-dialog>

    <ShareManagerDialog v-model="isShareDialogOpen" :report-oid="sharingReport?.reportOid || ''" :report-name="sharingReport?.name || ''" />
  </div>
</template>

<script setup lang="ts">
/** Report-library page that coordinates categories, pagination, and row commands. */
defineOptions({ name: 'CalcReportList' })

import ReportCategoryPanel from './components/ReportCategoryPanel.vue'
import ReportTable from './components/ReportTable.vue'
import ShareManagerDialog from '../shared/ShareManagerDialog.vue'
import CancelBtn from 'src/components/quasarWrapper/buttons/CancelBtn.vue'
import OkBtn from 'src/components/quasarWrapper/buttons/OkBtn.vue'
import type { CalcReport, CalcReportCategory } from 'src/api/calc/types'
import { createReportCategory, deleteReportCategory, listReportCategories, reorderReportCategories, updateReportCategory } from 'src/api/calc/categories'
import { copyCalcReport, deleteCalcReport, importUzcReport, listCalcReports, setCalcReportFavorite, updateCalcReport } from 'src/api/calc/reports'
import { showCalcReportInExplorer } from 'src/api/desktop'
import { useReportContextMenu } from './components/useReportContextMenu'
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
const isCategoryDialogOpen = ref(false)
const editingCategory = ref<CalcReportCategory | null>(null)
const categoryForm = reactive({ name: '', description: '' })
const isReportDialogOpen = ref(false)
const reportDialogMode = ref<'edit' | 'copy'>('edit')
const editingReport = ref<CalcReport | null>(null)
const reportForm = reactive({ categoryOid: '', name: '', description: '' })
const isImportDialogOpen = ref(false)
const isImporting = ref(false)
const importForm = reactive<{ categoryOid: string; name: string; archive: File | null }>({ categoryOid: '', name: '', archive: null })
const isShareDialogOpen = ref(false)
const sharingReport = ref<CalcReport | null>(null)

const categoryOptions = computed(() => categories.value.map((category) => ({ label: category.name, value: category.categoryOid })))

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

/** Open the category metadata dialog. */
function openCategoryDialog(category?: CalcReportCategory): void {
  editingCategory.value = category || null
  categoryForm.name = category?.name || ''
  categoryForm.description = category?.description || ''
  isCategoryDialogOpen.value = true
}
/** Create or update a category and refresh counts. */
async function onSaveCategory(): Promise<void> {
  if (editingCategory.value) await updateReportCategory(editingCategory.value.categoryOid, categoryForm)
  else await createReportCategory(categoryForm)
  isCategoryDialogOpen.value = false
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

/** Open report metadata or copy dialog. */
function openReportDialog(report: CalcReport, mode: 'edit' | 'copy'): void {
  editingReport.value = report
  reportDialogMode.value = mode
  reportForm.categoryOid = report.categoryOid
  reportForm.name = mode === 'copy' ? `${report.name} - Copy` : report.name
  reportForm.description = report.description || ''
  isReportDialogOpen.value = true
}
/** Save report metadata or create a copy. */
async function onSaveReportDialog(): Promise<void> {
  if (!editingReport.value) return
  if (reportDialogMode.value === 'copy') await copyCalcReport(editingReport.value.reportOid, reportForm)
  else {
    const response = await updateCalcReport(editingReport.value.reportOid, reportForm)
    Object.assign(editingReport.value, response.data)
  }
  isReportDialogOpen.value = false
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
/** Import a UZC archive into the selected category. */
async function onImportUzc(): Promise<void> {
  if (!importForm.archive) return
  isImporting.value = true
  try {
    await importUzcReport(importForm.categoryOid, importForm.name, importForm.archive)
    isImportDialogOpen.value = false
    importForm.archive = null
    await Promise.all([loadReports(), loadCategories()])
    notifySuccess(t('calcWorkspace.importComplete'))
  } finally { isImporting.value = false }
}
/** Open the shared report-link manager from a row action. */
function onShareReport(report: CalcReport): void { sharingReport.value = report; isShareDialogOpen.value = true }

const { items: contextMenuItems } = useReportContextMenu({
  open: onOpenReport,
  run: onRunReport,
  edit: (report) => openReportDialog(report, 'edit'),
  copy: (report) => openReportDialog(report, 'copy'),
  favorite: onToggleFavorite,
  share: onShareReport,
  showInExplorer: async (report) => { await showCalcReportInExplorer(report.reportOid) },
  remove: onDeleteReport,
  isDesktop: () => systemInfo.isLocalhost
})
</script>

<style scoped>
.report-library { min-height: 620px; height: 100%; background: #fff; overflow: hidden; }
.metadata-dialog { width: min(520px, 92vw); max-width: 520px; }
@media (max-width: 900px) { .report-library { overflow-x: auto; } }
</style>
