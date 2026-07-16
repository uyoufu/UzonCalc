<template>
  <div class="instance-library row no-wrap full-height">
    <aside class="instance-categories column no-wrap">
      <div class="row items-center q-px-sm instance-categories__header">
        <div class="text-subtitle2">{{ t('calcWorkspace.instanceCategories') }}</div><q-space /><CommonBtn flat dense
          icon="add" @click="onOpenCategoryDialog()" />
      </div>
      <q-separator /><q-list dense class="col scroll">
        <q-item clickable :active="!selectedCategoryOid" @click="selectedCategoryOid = null"><q-item-section
            avatar><q-icon name="all_inbox" /></q-item-section><q-item-section>{{ t('calcWorkspace.allInstances')
            }}</q-item-section></q-item>
        <q-item v-for="category in categories" :key="category.categoryOid" clickable
          :active="selectedCategoryOid === category.categoryOid" @click="selectedCategoryOid = category.categoryOid">
          <q-item-section avatar><q-icon name="folder" /></q-item-section><q-item-section>{{ category.name
            }}</q-item-section><q-item-section side>{{ category.instanceCount }}</q-item-section>
          <ContextMenu :items="categoryMenuItems" :value="category" />
        </q-item>
      </q-list>
    </aside>
    <q-table flat dense class="col" row-key="instanceOid" :rows="instances" :columns="columns" :loading="loading"
      v-model:pagination="pagination" :filter="filter" binary-state-sort @request="onTableRequest">
      <template #top>
        <div class="row full-width">
          <div class="text-subtitle1">{{ t('calcWorkspace.savedInstances') }}</div><q-space /><SearchInput v-model="filter" />
        </div>
      </template>
      <template #body-cell-name="slotProps"><q-td :props="slotProps"><button class="instance-link"
            @click="openInstance(slotProps.row)">{{ slotProps.row.name }}</button>
          <ContextMenu :items="instanceMenuItems" :value="slotProps.row" />
        </q-td></template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
/** Saved-instance library with category filtering and optimistic metadata editing. */
defineOptions({ name: 'CalcReportInstanceList' })
import type { QTableColumn } from 'quasar'
import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'
import SearchInput from 'src/components/searchInput/SearchInput.vue'
import type { CalcInstance, CalcInstanceCategory } from 'src/api/calc/types'
import { createInstanceCategory, deleteInstanceCategory, listInstanceCategories, updateInstanceCategory } from 'src/api/calc/categories'
import { countInstances, deleteInstance, listInstances, updateInstance } from 'src/api/calc/instances'
import { useInstanceContextMenu } from './components/useInstanceContextMenu'
import { useInstanceListDialogs } from './compositions/useInstanceListDialogs'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import { confirmOperation } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'
import { useQTable } from 'src/compositions/qTableUtils'
import type { IRequestPagination, TTableFilterObject } from 'src/compositions/types'

const router = useRouter()
const categories = ref<CalcInstanceCategory[]>([])
const selectedCategoryOid = ref<string | null>(null)
const categoryOptions = computed(() => categories.value.map((category) => ({ label: category.name, value: category.categoryOid })))
const { openCategoryDialog, openInstanceDialog } = useInstanceListDialogs()
const columns: ComputedRef<QTableColumn<CalcInstance>[]> = computed(() => [
  { name: 'name', label: t('calcWorkspace.instanceName'), field: 'name', align: 'left', sortable: true },
  { name: 'reportName', label: t('calcWorkspace.reportName'), field: (row) => row.reportName || '-', align: 'left', sortable: true },
  { name: 'sourceVersion', label: t('calcWorkspace.version'), field: (row) => row.sourceVersion || 'workspace', align: 'left' },
  { name: 'description', label: t('calcWorkspace.description'), field: (row) => row.description || '-', align: 'left' },
  { name: 'updatedAt', label: t('global.lastModified'), field: 'updatedAt', format: (value) => new Date(String(value)).toLocaleString(), align: 'left', sortable: true }
])

/** Load categories and their derived counts. */
async function loadCategories(): Promise<void> { const response = await listInstanceCategories(); categories.value = response.data || [] }
/** Convert table search and category state into API filters. */
function createInstanceFilter(filterValue: string): TTableFilterObject {
  const tableFilter: TTableFilterObject = { filter: filterValue }
  if (selectedCategoryOid.value) tableFilter.categoryOid = selectedCategoryOid.value
  return tableFilter
}
/** Return API filter parameters without the internal refresh counter. */
function getInstanceApiFilters(tableFilter: TTableFilterObject): { categoryOid?: string; query?: string } {
  return {
    categoryOid: typeof tableFilter.categoryOid === 'string' ? tableFilter.categoryOid : undefined,
    query: typeof tableFilter.filter === 'string' && tableFilter.filter ? tableFilter.filter : undefined
  }
}
/** Count saved instances matching the active table filters. */
async function getInstanceCount(tableFilter: TTableFilterObject): Promise<number> {
  return (await countInstances(getInstanceApiFilters(tableFilter))).data || 0
}
/** Request one sorted saved-instance page. */
async function requestInstanceItems(tableFilter: TTableFilterObject, pageRequest: IRequestPagination): Promise<CalcInstance[]> {
  return (await listInstances({ ...getInstanceApiFilters(tableFilter), ...pageRequest })).data || []
}
const {
  rows: instances,
  pagination,
  filter,
  loading,
  onTableRequest,
  refreshTable,
  updateExistOne,
  deleteRowById
} = useQTable<CalcInstance>({
  sortBy: 'updatedAt',
  descending: true,
  rowsPerPage: 20,
  filterFactor: createInstanceFilter,
  getRowsNumberCount: getInstanceCount,
  onRequest: requestInstanceItems
})
onMounted(loadCategories)
watch(filter, () => {
  pagination.value.page = 1
}, { flush: 'sync' })
watch(selectedCategoryOid, () => {
  pagination.value.page = 1
  refreshTable()
})
/** Open category metadata and persist a confirmed change. */
async function onOpenCategoryDialog(category?: CalcInstanceCategory): Promise<void> {
  const isSaved = await openCategoryDialog(category, async (input) => {
    if (category) await updateInstanceCategory(category.categoryOid, input)
    else await createInstanceCategory(input)
  })
  if (isSaved) await loadCategories()
}
/** Delete one empty instance category. */
async function removeCategory(category: CalcInstanceCategory): Promise<void> { if (!await confirmOperation(t('global.deleteConfirmation'), category.name)) return; await deleteInstanceCategory(category.categoryOid); await loadCategories() }
const categoryMenuItems: IContextMenuItem<CalcInstanceCategory>[] = [
  { name: 'edit', label: t('global.edit'), icon: 'edit', color: 'grey-9', onClick: onOpenCategoryDialog },
  { name: 'delete', label: t('global.delete'), icon: 'delete', color: 'negative', onClick: removeCategory }
]
/** Navigate to an instance detail. */
async function openInstance(instance: CalcInstance): Promise<void> { await router.push(`/calc-report-instance/${instance.instanceOid}`) }
/** Open optimistic instance metadata editing and patch the confirmed row. */
async function editInstance(instance: CalcInstance): Promise<void> {
  await openInstanceDialog(instance, categoryOptions.value, async (input) => {
    const response = await updateInstance(instance.instanceOid, { revision: instance.revision, ...input })
    updateExistOne(response.data, 'instanceOid')
  })
}
/** Delete one saved instance. */
async function removeInstance(instance: CalcInstance): Promise<void> { if (!await confirmOperation(t('global.deleteConfirmation'), instance.name)) return; await deleteInstance(instance.instanceOid); deleteRowById(instance.instanceOid, 'instanceOid'); await loadCategories() }
const { items: instanceMenuItems } = useInstanceContextMenu({ open: openInstance, edit: editInstance, remove: removeInstance })
</script>

<style scoped>
.instance-library {
  min-height: 620px;
  height: 100%;
  background: #fff;
  overflow: hidden;
}

.instance-categories {
  width: 240px;
  min-width: 240px;
  border-right: 1px solid #e4e7ec;
}

.instance-categories__header {
  min-height: 44px;
}

.instance-link {
  border: 0;
  padding: 0;
  color: #1565c0;
  background: transparent;
  cursor: pointer;
  font: inherit;
}
</style>
