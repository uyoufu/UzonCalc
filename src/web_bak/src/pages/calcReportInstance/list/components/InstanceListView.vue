<template>
  <q-table class="full-height" :rows="rows" :columns="columns" row-key="id" virtual-scroll
    v-model:pagination="pagination" dense :loading="loading" :filter="filter" binary-state-sort
    @request="onTableRequest">
    <template v-slot:top-right>
      <SearchInput v-model="filter" />
    </template>

    <template v-slot:body-cell-index="props">
      <QTableIndex :props="props" />
      <ContextMenu :items="itemContextMenuItems" :value="props.row"></ContextMenu>
    </template>

    <template v-slot:body-cell-name="props">
      <q-td :props="props">
        <ClickableText :text="props.value" @click="onViewCalcReportInstance(props.row)" />
      </q-td>
    </template>
  </q-table>
</template>

<script lang="ts" setup>
import { t } from 'src/i18n/helpers'
import type { QTableColumn } from 'quasar'
import { useQTable, useQTableIndex } from 'src/compositions/qTableUtils'
import type { IRequestPagination, TTableFilterObject } from 'src/compositions/types'
import SearchInput from 'src/components/searchInput/SearchInput.vue'
import { formatDate } from 'src/utils/format'
import type { ICategoryInfo } from 'src/components/categoryList/types'
import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'
import ClickableText from 'src/components/clickableText/ClickableText.vue'
import { countCalcReportInstances, listCalcReportInstances } from 'src/api/calcReportInstance'
import { useInstanceListStore } from '../compositions/useInstanceListStore'
import { useContextMenu } from './useContextMenu'

const props = defineProps<{
  category: ICategoryInfo
}>()

const categoryId = computed(() => props.category.id)
watch(categoryId, () => {
  refreshTable()
})

const { instanceListUpdateSignal } = useInstanceListStore()
watch(instanceListUpdateSignal, () => {
  refreshTable()
})

const { indexColumn, QTableIndex } = useQTableIndex()
const columns: ComputedRef<QTableColumn[]> = computed(() => [
  indexColumn,
  {
    name: 'name',
    required: true,
    label: t('calcReportInstancePage.list.col_name'),
    align: 'left',
    field: 'name',
    sortable: true
  },
  {
    name: 'description',
    required: true,
    label: t('calcReportInstancePage.list.col_description'),
    align: 'left',
    field: 'description',
    sortable: true
  },
  {
    name: 'reportName',
    required: true,
    label: t('calcReportInstancePage.list.col_reportName'),
    align: 'left',
    field: 'reportName',
    sortable: true
  },
  {
    name: 'version',
    required: true,
    label: t('calcReportInstancePage.list.col_version'),
    align: 'left',
    field: 'version',
    sortable: true
  },
  {
    name: 'lastModified',
    required: false,
    label: t('calcReportInstancePage.list.col_lastModified'),
    align: 'left',
    field: 'lastModified',
    format: formatDate,
    sortable: true
  },
  {
    name: 'createdAt',
    required: false,
    label: t('calcReportInstancePage.list.col_createdAt'),
    align: 'left',
    field: 'createdAt',
    format: formatDate,
    sortable: true
  }
])

async function getRowsNumberCount(filterObj: TTableFilterObject) {
  const { data } = await countCalcReportInstances({
    categoryId: props.category.id,
    filter: filterObj.filter
  })
  return data || 0
}

async function onRequest(filterObj: TTableFilterObject, pagination: IRequestPagination) {
  const { data } = await listCalcReportInstances({
    categoryId: props.category.id,
    filter: filterObj.filter,
    pagination
  })
  return data || []
}

const { pagination, rows, filter, onTableRequest, loading, refreshTable, deleteRowById } = useQTable({
  getRowsNumberCount,
  onRequest
})

const { itemContextMenuItems, onViewCalcReportInstance } = useContextMenu(deleteRowById)
</script>

<style lang="scss" scoped></style>
