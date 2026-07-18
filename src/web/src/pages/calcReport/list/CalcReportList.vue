<template>
  <div class="report-library row no-wrap full-height">
    <ReportCategoryPanel v-model="selectedCategoryOid" :categories="categories" @create="onOpenCategoryDialog()"
      @edit="onOpenCategoryDialog" @delete="onDeleteCategory" @organize="onOrganizeCategories"
      @access="onCategoryAccess" />
    <SharedReportList v-if="selectedCategoryOid === FixedReportCategoryFilter.Shared" :categories="categories" />
    <ReportTable v-else v-model:filter="filter" v-model:pagination="pagination" :reports="reports" :loading="loading"
      :context-menu-items="contextMenuItems" @request="onTableRequest" @create="onCreateReport"
      @import="onOpenImportDialog" @open="onOpenReport" @favorite="onToggleFavorite" />
  </div>
</template>

<script setup lang="ts">
/** Report-library page that coordinates categories, pagination, and row commands. */
defineOptions({ name: 'CalcReportList' })

import ReportCategoryPanel from './components/ReportCategoryPanel.vue'
import ReportTable from './components/ReportTable.vue'
import SharedReportList from './components/SharedReportList.vue'
import type { CalcReport, CalcReportCategory } from 'src/api/calc/types'
import { createReportCategory, deleteReportCategory, listReportCategories, recordReportCategoryAccess, reorderReportCategories, updateReportCategory, updateReportCategoryState } from 'src/api/calc/categories'
import { countCalcReports, importReportArchive, listCalcReports, type ReportListParams } from 'src/api/calc/reports'
import { importRemoteShare, previewRemoteShare, resolveBackendShareSource } from 'src/api/calc/shares'
import { useReportContextMenu } from './components/useReportContextMenu'
import { useCalcReportListDialogs } from './compositions/useCalcReportListDialogs'
import { confirmOperation, notifySuccess, notifyUntil } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'
import { useQTable } from 'src/compositions/qTableUtils'
import type { IRequestPagination, TTableFilterObject } from 'src/compositions/types'
import { FixedReportCategoryFilter, type ReportCategorySelection } from './components/reportCategoryFilter'
import { getUserSetting, upsertUserSetting } from 'src/api/userSetting'

const LAST_CATEGORY_SETTING_KEY = 'calcReport.lastCategory'

const router = useRouter()
const categories = ref<CalcReportCategory[]>([])
const selectedCategoryOid = ref<ReportCategorySelection>(null)
const categoryOptions = computed(() => categories.value.map((category) => ({ label: category.name, value: category.categoryOid })))
const { openCategoryDialog, openImportDialog, openLinkImportDialog } = useCalcReportListDialogs()

/** Refresh report categories and their derived counts. */
async function loadCategories(): Promise<void> {
  const response = await listReportCategories()
  categories.value = response.data || []
}

/** Restore the last category with local state taking precedence over server sync. */
async function initializeCategories(): Promise<void> {
  await loadCategories()
  const localSelection = localStorage.getItem(LAST_CATEGORY_SETTING_KEY)
  const serverSetting = localSelection ? null : (await getUserSetting(LAST_CATEGORY_SETTING_KEY)).data
  const candidate = localSelection || (typeof serverSetting?.categoryOid === 'string' ? serverSetting.categoryOid : null)
  const fixedValues: ReportCategorySelection[] = [null, FixedReportCategoryFilter.Favorites, FixedReportCategoryFilter.Shared]
  selectedCategoryOid.value = fixedValues.includes(candidate) || categories.value.some((category) => category.categoryOid === candidate)
    ? candidate
    : null
}

/** Convert table search and category state into API filters. */
function createReportFilter(filterValue: string): TTableFilterObject {
  const tableFilter: TTableFilterObject = { filter: filterValue }
  if (selectedCategoryOid.value === FixedReportCategoryFilter.Favorites) tableFilter.favoriteOnly = true
  else if (selectedCategoryOid.value) tableFilter.categoryOid = selectedCategoryOid.value
  return tableFilter
}

/** Return API filter parameters without the internal refresh counter. */
function getReportApiFilters(tableFilter: TTableFilterObject): ReportListParams {
  return {
    categoryOid: typeof tableFilter.categoryOid === 'string' ? tableFilter.categoryOid : undefined,
    query: typeof tableFilter.filter === 'string' && tableFilter.filter ? tableFilter.filter : undefined,
    favoriteOnly: tableFilter.favoriteOnly === true ? true : undefined
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

onMounted(initializeCategories)
watch(filter, () => {
  pagination.value.page = 1
}, { flush: 'sync' })
let categorySettingTimer: ReturnType<typeof setTimeout> | undefined
watch(selectedCategoryOid, (selection) => {
  pagination.value.page = 1
  if (selection !== FixedReportCategoryFilter.Shared) refreshTable()
  if (selection === null) localStorage.removeItem(LAST_CATEGORY_SETTING_KEY)
  else localStorage.setItem(LAST_CATEGORY_SETTING_KEY, selection)
  clearTimeout(categorySettingTimer)
  categorySettingTimer = setTimeout(() => {
    void upsertUserSetting(LAST_CATEGORY_SETTING_KEY, { value: { categoryOid: selection } })
  }, 400)
})

/** Navigate to a preallocated new workspace. */
async function onCreateReport(): Promise<void> {
  const selectedPersistedCategoryOid = categories.value.some((category) => category.categoryOid === selectedCategoryOid.value)
    ? selectedCategoryOid.value
    : undefined
  await router.push({ path: '/calc-report/new', query: { categoryOid: selectedPersistedCategoryOid || categories.value[0]?.categoryOid } })
}
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
/** Persist pin/hide changes and manual order after menu or drag operations. */
async function onOrganizeCategories(value: CalcReportCategory[]): Promise<void> {
  const previous = new Map(categories.value.map((category) => [category.categoryOid, category]))
  categories.value = value
  await Promise.all(value.map((category) => {
    const original = previous.get(category.categoryOid)
    if (original?.isPinned === category.isPinned && original?.isHidden === category.isHidden) return Promise.resolve()
    return updateReportCategoryState(category.categoryOid, { isPinned: category.isPinned, isHidden: category.isHidden })
  }))
  const pinned = value.filter((category) => category.isPinned)
  const response = await reorderReportCategories(pinned.map((category, manualOrder) => ({ categoryOid: category.categoryOid, manualOrder })))
  categories.value = response.data || value
}

/** Record one persisted category use and reload LFU-Aging order. */
async function onCategoryAccess(category: CalcReportCategory): Promise<void> {
  await recordReportCategoryAccess(category.categoryOid)
  await loadCategories()
}

/** Import a portable file or public share link and refresh the library. */
async function onOpenImportDialog(kind: 'file' | 'link'): Promise<void> {
  if (kind === 'link') {
    const input = await openLinkImportDialog(categoryOptions.value)
    if (!input) return
    const source = resolveBackendShareSource(input.source)
    const preview = (await previewRemoteShare(source)).data
    if (!preview.canEdit && !await confirmOperation(t('calcWorkspace.executionRiskTitle'), t('calcWorkspace.executionRiskMessage'))) return
    await notifyUntil(
      async () => await importRemoteShare(source, input.categoryOid, input.name, input.shouldSync),
      t('calcWorkspace.importingArchive')
    )
    await refreshAfterImport()
    return
  }
  const input = await openImportDialog(categoryOptions.value)
  if (!input) return

  await notifyUntil(
    async () => await importReportArchive(input.categoryOid, input.name, input.archive),
    t('calcWorkspace.importingArchive')
  )
  await refreshAfterImport()
}

/** Reload categories and the first report page after a completed import. */
async function refreshAfterImport(): Promise<void> {
  await loadCategories()
  pagination.value.page = 1
  refreshTable()
  notifySuccess(t('calcWorkspace.importComplete'))
}
const {
  items: contextMenuItems,
  onOpenReport,
  onToggleFavorite
} = useReportContextMenu({
  categories,
  selectedCategoryOid,
  filter,
  pagination,
  refreshTable,
  updateReportRow: updateExistOne,
  deleteReportRow: deleteRowById
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
