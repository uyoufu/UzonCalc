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

const { indexColumn, QTableIndex } = useQTableIndex()
const columns: QTableColumn[] = [
  indexColumn,
  {
    name: 'userId',
    required: true,
    label: '用户名',
    align: 'left',
    field: 'userId',
    sortable: true
  },
  {
    name: 'createDate',
    required: false,
    label: '注册日期',
    align: 'left',
    field: 'createDate',
    format: formatDate, // format 需要的 value 是 string
    sortable: true
  }
]
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function getRowsNumberCount(filterObj: TTableFilterObject) {
  return 0
}
// eslint-disable-next-line @typescript-eslint/no-unused-vars, @typescript-eslint/require-await
async function onRequest(filterObj: TTableFilterObject, pagination: IRequestPagination) {
  return []
}

const { pagination, rows, filter, onTableRequest, loading } = useQTable({
  getRowsNumberCount,

  onRequest
})


// #region go newCalcReport
import { useNewCalcReportRoute } from '../../new/useNewCalcReportRoute'
const { goToNewCalcReport } = useNewCalcReportRoute()

// #endregion
</script>

<style lang="scss" scoped></style>
