<template>
  <q-table class="report-table col" flat dense row-key="reportOid" :rows="reports" :columns="columns"
    :loading="loading" :pagination="pagination" :rows-number="total" @request="onRequest">
    <template #top>
      <div class="row items-center full-width q-gutter-sm">
        <CommonBtn icon="add" :label="t('global.new')" :tooltip="t('calcWorkspace.newReport')" @click="emit('create')" />
        <CommonBtn icon="upload_file" color="grey-8" :label="t('global.import')" :tooltip="t('calcWorkspace.importUzc')" @click="emit('import')" />
        <q-space />
        <q-input :model-value="query" dense outlined debounce="350" :placeholder="t('calcWorkspace.searchReports')"
          @update:model-value="emit('update:query', String($event || ''))">
          <template #prepend><q-icon name="search" /></template>
        </q-input>
      </div>
    </template>
    <template #body-cell-name="slotProps">
      <q-td :props="slotProps">
        <button class="report-link" type="button" @click="emit('open', slotProps.row)">{{ slotProps.row.name }}</button>
        <ContextMenu :items="contextMenuItems" :value="slotProps.row" />
      </q-td>
    </template>
    <template #body-cell-state="slotProps">
      <q-td :props="slotProps" class="q-gutter-xs">
        <q-chip dense square :color="publishColor(slotProps.row.publishState)" text-color="white">
          {{ publishLabel(slotProps.row.publishState) }}
        </q-chip>
        <q-chip dense square :color="buildColor(slotProps.row.buildStatus)" text-color="white">
          {{ buildLabel(slotProps.row.buildStatus) }}
        </q-chip>
      </q-td>
    </template>
    <template #body-cell-favorite="slotProps">
      <q-td :props="slotProps">
        <q-btn flat round dense :icon="slotProps.row.isFavorite ? 'star' : 'star_border'"
          :color="slotProps.row.isFavorite ? 'warning' : 'grey-6'" @click="emit('favorite', slotProps.row)" />
      </q-td>
    </template>
  </q-table>
</template>

<script setup lang="ts">
/** Dense report table with server-side pagination and row actions. */
import type { QTableColumn, QTableProps } from 'quasar'
import type { BuildStatus, CalcReport, PublishState } from 'src/api/calc/types'
import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import { t } from 'src/i18n/helpers'

const props = defineProps<{
  reports: CalcReport[]
  loading: boolean
  total: number
  page: number
  rowsPerPage: number
  query: string
  contextMenuItems: IContextMenuItem<CalcReport>[]
}>()
const emit = defineEmits<{
  request: [page: number, rowsPerPage: number]
  'update:query': [value: string]
  create: []
  import: []
  open: [report: CalcReport]
  favorite: [report: CalcReport]
}>()

const pagination = computed(() => ({ page: props.page, rowsPerPage: props.rowsPerPage, rowsNumber: props.total }))
const columns: QTableColumn<CalcReport>[] = [
  { name: 'name', label: t('calcWorkspace.reportName'), field: 'name', align: 'left' },
  { name: 'description', label: t('calcWorkspace.description'), field: (row) => row.description || '-', align: 'left' },
  { name: 'latestVersionName', label: t('calcWorkspace.latestVersion'), field: (row) => row.latestVersionName || '-', align: 'left' },
  { name: 'state', label: t('calcWorkspace.state'), field: 'publishState', align: 'left' },
  { name: 'updatedAt', label: t('global.lastModified'), field: 'updatedAt', format: (value) => new Date(String(value)).toLocaleString(), align: 'left' },
  { name: 'favorite', label: '', field: 'isFavorite', align: 'center' }
]

/** Forward Quasar pagination requests. */
function onRequest(request: Parameters<NonNullable<QTableProps['onRequest']>>[0]): void {
  emit('request', request.pagination.page, request.pagination.rowsPerPage)
}
/** Map publish state to a restrained status color. */
function publishColor(state: PublishState): string {
  return ({ published: 'positive', unpublished: 'grey-7', unpublished_changes: 'warning', workspace_version_mismatch: 'deep-orange' })[state]
}
/** Map build state to a restrained status color. */
function buildColor(state: BuildStatus): string {
  return ({ not_requested: 'grey-6', pending: 'blue-grey', building: 'info', ready: 'positive', failed: 'negative' })[state]
}
/** Return the translated publish-state label. */
function publishLabel(state: PublishState): string {
  const labels: Record<PublishState, string> = {
    unpublished: t('calcWorkspace.publishStates.unpublished'),
    published: t('calcWorkspace.publishStates.published'),
    unpublished_changes: t('calcWorkspace.publishStates.unpublished_changes'),
    workspace_version_mismatch: t('calcWorkspace.publishStates.workspace_version_mismatch')
  }
  return labels[state]
}
/** Return the translated build-state label. */
function buildLabel(state: BuildStatus): string {
  const labels: Record<BuildStatus, string> = {
    not_requested: t('calcWorkspace.buildStates.not_requested'),
    pending: t('calcWorkspace.buildStates.pending'),
    building: t('calcWorkspace.buildStates.building'),
    ready: t('calcWorkspace.buildStates.ready'),
    failed: t('calcWorkspace.buildStates.failed')
  }
  return labels[state]
}
</script>

<style scoped>
.report-table { min-width: 0; height: 100%; }
.report-link { border: 0; padding: 0; color: #1565c0; background: transparent; cursor: pointer; font: inherit; }
.report-link:hover { text-decoration: underline; }
</style>
