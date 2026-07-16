<template>
  <div class="instance-library row no-wrap full-height">
    <aside class="instance-categories column no-wrap">
      <div class="row items-center q-px-sm instance-categories__header">
        <div class="text-subtitle2">{{ t('calcWorkspace.instanceCategories') }}</div><q-space /><q-btn flat round dense
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
    <q-table flat dense class="col" row-key="instanceOid" :rows="instances" :columns="columns" :loading="isLoading"
      :pagination="pagination" :rows-number="total" @request="onRequest">
      <template #top>
        <div class="row full-width">
          <div class="text-subtitle1">{{ t('calcWorkspace.savedInstances') }}</div><q-space /><q-input v-model="query"
            dense outlined debounce="350" :placeholder="t('calcWorkspace.searchInstances')"><template #prepend><q-icon
                name="search" /></template></q-input>
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
import type { QTableColumn, QTableProps } from 'quasar'
import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'
import type { CalcInstance, CalcInstanceCategory } from 'src/api/calc/types'
import { createInstanceCategory, deleteInstanceCategory, listInstanceCategories, updateInstanceCategory } from 'src/api/calc/categories'
import { deleteInstance, listInstances, updateInstance } from 'src/api/calc/instances'
import { useInstanceContextMenu } from './components/useInstanceContextMenu'
import { useInstanceListDialogs } from './compositions/useInstanceListDialogs'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import { confirmOperation } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'

const router = useRouter()
const categories = ref<CalcInstanceCategory[]>([])
const instances = ref<CalcInstance[]>([])
const selectedCategoryOid = ref<string | null>(null)
const query = ref('')
const total = ref(0)
const page = ref(1)
const rowsPerPage = ref(20)
const isLoading = ref(false)
const pagination = computed(() => ({ page: page.value, rowsPerPage: rowsPerPage.value, rowsNumber: total.value }))
const categoryOptions = computed(() => categories.value.map((category) => ({ label: category.name, value: category.categoryOid })))
const { openCategoryDialog, openInstanceDialog } = useInstanceListDialogs()
const columns: QTableColumn<CalcInstance>[] = [
  { name: 'name', label: t('calcWorkspace.instanceName'), field: 'name', align: 'left' },
  { name: 'reportName', label: t('calcWorkspace.reportName'), field: (row) => row.reportName || '-', align: 'left' },
  { name: 'sourceVersion', label: t('calcWorkspace.version'), field: (row) => row.sourceVersion || 'workspace', align: 'left' },
  { name: 'description', label: t('calcWorkspace.description'), field: (row) => row.description || '-', align: 'left' },
  { name: 'updatedAt', label: t('global.lastModified'), field: 'updatedAt', format: (value) => new Date(String(value)).toLocaleString(), align: 'left' }
]

/** Load categories and their derived counts. */
async function loadCategories(): Promise<void> { const response = await listInstanceCategories(); categories.value = response.data || [] }
/** Load one page of saved instances. */
async function loadInstances(): Promise<void> { isLoading.value = true; try { const response = await listInstances({ categoryOid: selectedCategoryOid.value || undefined, query: query.value || undefined, offset: (page.value - 1) * rowsPerPage.value, limit: rowsPerPage.value }); instances.value = response.data?.items || []; total.value = response.data?.total || 0 } finally { isLoading.value = false } }
onMounted(async () => { await Promise.all([loadCategories(), loadInstances()]) })
watch([selectedCategoryOid, query], async () => { page.value = 1; await loadInstances() })
/** Apply server-side pagination. */
async function onRequest(request: Parameters<NonNullable<QTableProps['onRequest']>>[0]): Promise<void> { page.value = request.pagination.page; rowsPerPage.value = request.pagination.rowsPerPage; await loadInstances() }
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
    Object.assign(instance, response.data)
  })
}
/** Delete one saved instance. */
async function removeInstance(instance: CalcInstance): Promise<void> { if (!await confirmOperation(t('global.deleteConfirmation'), instance.name)) return; await deleteInstance(instance.instanceOid); instances.value = instances.value.filter((candidate) => candidate.instanceOid !== instance.instanceOid); total.value -= 1; await loadCategories() }
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
