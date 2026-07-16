<template>
  <div class="execution-history full-height">
    <q-table flat dense class="full-height" row-key="executionId" :rows="executions" :columns="columns" :loading="isLoading" :pagination="pagination" :rows-number="total" @request="onRequest">
      <template #top><div class="text-subtitle1">{{ t('calcWorkspace.executionHistory') }}</div><q-space /><q-btn flat round dense icon="refresh" @click="loadExecutions" /></template>
      <template #body-cell-status="slotProps"><q-td :props="slotProps"><q-chip dense square :color="statusColor(slotProps.row.status)" text-color="white">{{ slotProps.row.status }}</q-chip></q-td></template>
      <template #body-cell-actions="slotProps"><q-td :props="slotProps"><q-btn flat round dense icon="info" @click="selectedExecution = slotProps.row" /><q-btn v-if="['pending', 'running'].includes(slotProps.row.status)" flat round dense icon="stop" color="negative" @click="onTerminate(slotProps.row)" /></q-td></template>
    </q-table>
    <q-dialog :model-value="Boolean(selectedExecution)" @update:model-value="selectedExecution = null"><q-card class="execution-dialog"><q-card-section class="row items-center"><div class="text-subtitle1">{{ selectedExecution?.executionId }}</div><q-space /><q-btn flat round dense icon="close" v-close-popup /></q-card-section><q-separator /><q-card-section v-if="selectedExecution" class="execution-details"><dl><template v-for="field in detailFields" :key="field"><dt>{{ field }}</dt><dd>{{ selectedExecution[field] }}</dd></template></dl></q-card-section></q-card></q-dialog>
  </div>
</template>

<script setup lang="ts">
/** Paginated managed-execution audit and termination page. */
defineOptions({ name: 'CalcExecutionHistory' })
import type { QTableColumn, QTableProps } from 'quasar'
import type { CalcExecution, ExecutionStatus } from 'src/api/calc/types'
import { listExecutions, terminateExecution } from 'src/api/calc/executions'
import { t } from 'src/i18n/helpers'

const executions = ref<CalcExecution[]>([]); const total = ref(0); const page = ref(1); const rowsPerPage = ref(20); const isLoading = ref(false); const selectedExecution = ref<CalcExecution | null>(null)
const pagination = computed(() => ({ page: page.value, rowsPerPage: rowsPerPage.value, rowsNumber: total.value }))
const detailFields: Array<keyof CalcExecution> = ['reportOid', 'sourceType', 'resolvedVersion', 'sourceArtifactHash', 'executionArtifactHash', 'bundleHash', 'runtimeFingerprint', 'executorType', 'backendMode', 'status', 'createdAt', 'completedAt']
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

<style scoped>.execution-history { min-height: 620px; background: #fff; }.execution-dialog { width: min(760px, 92vw); max-width: 760px; }.execution-details dl { display: grid; grid-template-columns: 180px 1fr; gap: 8px 16px; }.execution-details dt { color: #667085; }.execution-details dd { margin: 0; overflow-wrap: anywhere; }</style>
