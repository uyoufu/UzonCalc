<template>
  <q-table class="col full-height" :rows="rows" :columns="columns" row-key="shareOid" dense binary-state-sort
    v-model:pagination="pagination" :loading="loading" :filter="filter" @request="onTableRequest">
    <template #top-right><SearchInput v-model="filter" /></template>
    <template #body="tableProps">
      <q-tr :props="tableProps">
        <q-td v-for="column in tableProps.cols" :key="column.name" :props="tableProps">{{ column.value }}</q-td>
        <ContextMenu :items="contextMenuItems" :value="tableProps.row" />
      </q-tr>
    </template>
  </q-table>
</template>

<script setup lang="ts">
/** Dedicated paginated table for same-backend shared calculation reports. */
import type { QTableColumn } from 'quasar'
import SearchInput from 'src/components/searchInput/SearchInput.vue'
import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'
import { countSharedReports, listSharedReports } from 'src/api/calc/shares'
import type { CalcReportCategory, SharedReport } from 'src/api/calc/types'
import { useQTable } from 'src/compositions/qTableUtils'
import type { IRequestPagination, TTableFilterObject } from 'src/compositions/types'
import { t } from 'src/i18n/helpers'
import { useSharedReportContextMenu } from './useSharedReportContextMenu'

const props = defineProps<{ categories: CalcReportCategory[] }>()
const columns: ComputedRef<QTableColumn[]> = computed(() => [
  { name: 'qualifiedName', label: t('calcWorkspace.reportName'), field: 'qualifiedName', align: 'left', sortable: true },
  { name: 'description', label: t('global.description'), field: 'description', align: 'left' },
  { name: 'versionName', label: t('calcWorkspace.version'), field: 'versionName', align: 'left', sortable: true },
  { name: 'sharedAt', label: t('calcWorkspace.sharedAt'), field: 'sharedAt', align: 'left', sortable: true }
])

/** Count shares matching the table query. */
async function getRowsNumberCount(filters: TTableFilterObject): Promise<number> {
  return (await countSharedReports(typeof filters.filter === 'string' ? filters.filter : undefined)).data || 0
}

/** Fetch one page of accessible shared reports. */
async function requestRows(filters: TTableFilterObject, page: IRequestPagination): Promise<SharedReport[]> {
  return (await listSharedReports({
    query: typeof filters.filter === 'string' ? filters.filter : undefined,
    ...page
  })).data || []
}

const { rows, pagination, filter, loading, onTableRequest } = useQTable<SharedReport>({
  sortBy: 'sharedAt',
  descending: true,
  rowsPerPage: 20,
  getRowsNumberCount,
  onRequest: requestRows
})
const { contextMenuItems } = useSharedReportContextMenu(computed(() => props.categories))
</script>
