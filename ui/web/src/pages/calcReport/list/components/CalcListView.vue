<template>
  <q-table class="full-height" :rows="rows" :columns="columns" row-key="id" virtual-scroll
    v-model:pagination="pagination" dense :loading="loading" :filter="filter" binary-state-sort
    @request="onTableRequest">
    <template v-slot:top-left>
      <CreateBtn :tooltip="t('calcReportPage.newCalcReportTooltip')" @click="goToNewCalcReport" />
    </template>

    <template v-slot:top-right>
      <SearchInput v-model="filter" />
    </template>

    <template v-slot:body-cell-index="props">
      <QTableIndex :props="props" />
    </template>

    <template v-slot:body-cell-userId="props">
      <q-td :props="props">
        {{ props.value }}
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

const props = defineProps<{
  category: ICategoryInfo
}>()
const categoryOid = computed(() => {
  return props.category.oid
})
// 分类变化后刷新表格数据
watch(categoryOid, () => {
  refreshTable()
})

const { indexColumn, QTableIndex } = useQTableIndex()
const columns: ComputedRef<QTableColumn[]> = computed(() => [
  indexColumn,
  {
    name: 'name',
    required: true,
    label: t('calcReportPage.list.col_name'),
    align: 'left',
    field: 'name',
    sortable: true
  },
  {
    name: 'description',
    required: true,
    label: t('calcReportPage.list.col_description'),
    align: 'left',
    field: 'description',
    sortable: true
  },
  {
    name: 'createdAt',
    required: false,
    label: t('calcReportPage.list.col_createdAt'),
    align: 'left',
    field: 'createdAt',
    format: formatDate, // format 需要的 value 是 string
    sortable: true
  }
])

import { countCalcReports, listCalcReports } from 'src/api/calcReport'

async function getRowsNumberCount(filterObj: TTableFilterObject) {
  const { data } = await countCalcReports({
    categoryId: props.category.id,
    filter: filterObj.filter
  })
  return data || 0
}

async function onRequest(filterObj: TTableFilterObject, pagination: IRequestPagination) {
  const { data } = await listCalcReports({
    categoryId: props.category.id,
    filter: filterObj.filter,
    pagination
  })
  return data || []
}

const { pagination, rows, filter, onTableRequest, loading, refreshTable } = useQTable({
  getRowsNumberCount,
  onRequest
})


// #region go newCalcReport
import { useNewCalcReportRoute } from './useNewCalcReportRoute'
const { goToNewCalcReport } = useNewCalcReportRoute(categoryOid)

// #endregion
</script>

<style lang="scss" scoped></style>
