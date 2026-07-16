<template>
  <div class="execution-history full-height">
    <q-table flat dense class="full-height" row-key="executionId" :rows="executions" :columns="columns"
      :loading="loading" v-model:pagination="pagination" :filter="filter" binary-state-sort @request="onTableRequest">
      <template #top>
        <div class="text-subtitle1">{{ t('calcWorkspace.executionHistory') }}</div><q-space /><q-btn flat round dense
          icon="refresh" @click="refreshTable" />
      </template>
      <template #body-cell-status="slotProps"><q-td :props="slotProps"><q-chip dense square
            :color="statusColor(slotProps.row.status)" text-color="white">{{ slotProps.row.status
            }}</q-chip></q-td></template>
      <template #body-cell-actions="slotProps"><q-td :props="slotProps"><q-btn flat round dense icon="info"
            @click="openExecutionDetailDialog(slotProps.row)" /><q-btn
            v-if="['pending', 'running'].includes(slotProps.row.status)" flat round dense icon="stop" color="negative"
            @click="onTerminate(slotProps.row)" /></q-td></template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
/** Paginated managed-execution audit and termination page. */
defineOptions({ name: 'CalcExecutionHistory' })
import type { QTableColumn } from 'quasar'
import type { CalcExecution, ExecutionStatus } from 'src/api/calc/types'
import { countExecutions, listExecutions, terminateExecution } from 'src/api/calc/executions'
import { t } from 'src/i18n/helpers'
import { useExecutionDetailDialog } from './compositions/useExecutionDetailDialog'
import { useQTable } from 'src/compositions/qTableUtils'
import type { IRequestPagination, TTableFilterObject } from 'src/compositions/types'

const { openExecutionDetailDialog } = useExecutionDetailDialog()
const columns: ComputedRef<QTableColumn<CalcExecution>[]> = computed(() => [
  { name: 'createdAt', label: t('calcWorkspace.startedAt'), field: 'createdAt', format: (value) => new Date(String(value)).toLocaleString(), align: 'left', sortable: true },
  { name: 'reportOid', label: 'Report OID', field: 'reportOid', align: 'left' },
  { name: 'sourceType', label: t('calcWorkspace.executionSource'), field: (row) => row.resolvedVersion ? `${row.sourceType}:${row.resolvedVersion}` : row.sourceType, align: 'left' },
  { name: 'backendMode', label: t('calcWorkspace.backend'), field: 'backendMode', align: 'left' },
  { name: 'status', label: t('calcWorkspace.state'), field: 'status', align: 'left', sortable: true },
  { name: 'actions', label: '', field: 'executionId', align: 'right' }
])
/** Count execution audit rows for the current user. */
async function getExecutionCount(): Promise<number> {
  return (await countExecutions()).data || 0
}
/** Request one sorted execution audit page. */
async function requestExecutionItems(_tableFilter: TTableFilterObject, pageRequest: IRequestPagination): Promise<CalcExecution[]> {
  return (await listExecutions(pageRequest)).data || []
}
const {
  rows: executions,
  pagination,
  filter,
  loading,
  onTableRequest,
  refreshTable,
  updateExistOne
} = useQTable<CalcExecution>({
  sortBy: 'createdAt',
  descending: true,
  rowsPerPage: 20,
  getRowsNumberCount: getExecutionCount,
  onRequest: requestExecutionItems
})
/** Terminate one active execution and patch its local state. */
async function onTerminate(execution: CalcExecution): Promise<void> { await terminateExecution(execution.executionId); updateExistOne({ ...execution, status: 'cancelled' }, 'executionId') }
/** Map execution status to semantic color. */
function statusColor(status: ExecutionStatus): string { return ({ pending: 'grey-7', running: 'info', succeeded: 'positive', failed: 'negative', cancelled: 'warning', expired: 'deep-orange' })[status] }
</script>

<style scoped>
.execution-history {
  min-height: 620px;
  background: #fff;
}
</style>
