<template>
  <div class="execution-history full-height">
    <q-table flat dense class="full-height" row-key="executionId" :rows="executions" :columns="columns"
      :loading="isLoading" :pagination="pagination" :rows-number="total" @request="onRequest">
      <template #top>
        <div class="text-subtitle1">{{ t('calcWorkspace.executionHistory') }}</div><q-space /><q-btn flat round dense
          icon="refresh" @click="loadExecutions" />
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
import type { QTableColumn, QTableProps } from 'quasar'
import type { CalcExecution, ExecutionStatus } from 'src/api/calc/types'
import { listExecutions, terminateExecution } from 'src/api/calc/executions'
import { t } from 'src/i18n/helpers'
import { useExecutionDetailDialog } from './compositions/useExecutionDetailDialog'

const executions = ref<CalcExecution[]>([]); const total = ref(0); const page = ref(1); const rowsPerPage = ref(20); const isLoading = ref(false)
const pagination = computed(() => ({ page: page.value, rowsPerPage: rowsPerPage.value, rowsNumber: total.value }))
const { openExecutionDetailDialog } = useExecutionDetailDialog()
const columns: QTableColumn<CalcExecution>[] = [
  { name: 'createdAt', label: t('calcWorkspace.startedAt'), field: 'createdAt', format: (value) => new Date(String(value)).toLocaleString(), align: 'left' },
  { name: 'reportOid', label: 'Report OID', field: 'reportOid', align: 'left' },
  { name: 'sourceType', label: t('calcWorkspace.executionSource'), field: (row) => row.resolvedVersion ? `${row.sourceType}:${row.resolvedVersion}` : row.sourceType, align: 'left' },
  { name: 'backendMode', label: t('calcWorkspace.backend'), field: 'backendMode', align: 'left' },
  { name: 'status', label: t('calcWorkspace.state'), field: 'status', align: 'left' },
  { name: 'actions', label: '', field: 'executionId', align: 'right' }
]
/** Load one execution-history page. */
async function loadExecutions(): Promise<void> { isLoading.value = true; try { const response = await listExecutions({ offset: (page.value - 1) * rowsPerPage.value, limit: rowsPerPage.value }); executions.value = response.data?.items || []; total.value = response.data?.total || 0 } finally { isLoading.value = false } }
onMounted(loadExecutions)
/** Apply server-side history pagination. */
async function onRequest(request: Parameters<NonNullable<QTableProps['onRequest']>>[0]): Promise<void> { page.value = request.pagination.page; rowsPerPage.value = request.pagination.rowsPerPage; await loadExecutions() }
/** Terminate one active execution and patch its local state. */
async function onTerminate(execution: CalcExecution): Promise<void> { await terminateExecution(execution.executionId); execution.status = 'cancelled' }
/** Map execution status to semantic color. */
function statusColor(status: ExecutionStatus): string { return ({ pending: 'grey-7', running: 'info', succeeded: 'positive', failed: 'negative', cancelled: 'warning', expired: 'deep-orange' })[status] }
</script>

<style scoped>
.execution-history {
  min-height: 620px;
  background: #fff;
}
</style>
