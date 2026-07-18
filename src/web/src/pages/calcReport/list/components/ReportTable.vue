<template>
  <q-table class="report-table col" flat dense row-key="reportOid" :rows="reports" :columns="columns" :loading="loading"
    v-model:pagination="pagination" :filter="filter" binary-state-sort @request="emit('request', $event)">
    <template #top>
      <div class="row items-center full-width q-gutter-sm">
        <CommonBtn icon="add" :label="t('global.new')" :tooltip="t('calcWorkspace.newReport')"
          @click="emit('create')" />
        <q-fab square color="grey-8" icon="add" direction="down" padding="xs" :label="t('global.import')"
          vertical-actions-align="left">
          <q-fab-action square padding="xs" color="primary" icon="upload_file" :label="t('calcWorkspace.importFile')"
            @click="emit('import', 'file')" />
          <q-fab-action square padding="xs" color="secondary" icon="link" :label="t('calcWorkspace.importLink')"
            @click="emit('import', 'link')" />
        </q-fab>
        <q-space />
        <SearchInput v-model="filter" />
      </div>
    </template>
    <template #body-cell-name="slotProps">
      <q-td :props="slotProps">
        <ClickableText :text="slotProps.row.name" @click="emit('open', slotProps.row)" />
      </q-td>
      <ContextMenu :items="contextMenuItems" :value="slotProps.row" />
    </template>
    <template #body-cell-state="slotProps">
      <q-td :props="slotProps" class="q-gutter-xs">
        <q-chip dense square :color="publishColor(slotProps.row.publishState)" text-color="white">
          {{ publishLabel(slotProps.row.publishState) }}
        </q-chip>
        <q-chip dense square :color="buildColor(slotProps.row.buildStatus)" text-color="white">
          {{ buildLabel(slotProps.row.buildStatus) }}
        </q-chip>
        <q-chip v-if="slotProps.row.syncState !== ReportSyncState.NotApplicable" dense square
          :color="syncColor(slotProps.row.syncState)" text-color="white">{{ syncLabel(slotProps.row.syncState)
          }}</q-chip>
      </q-td>
    </template>
    <template #body-cell-favorite="slotProps">
      <q-td :props="slotProps">
        <CommonBtn flat dense :icon="slotProps.row.isFavorite ? 'star' : 'star_border'"
          :color="slotProps.row.isFavorite ? 'warning' : 'grey-6'" @click="emit('favorite', slotProps.row)" />
      </q-td>
    </template>
  </q-table>
</template>

<script setup lang="ts">
/** Dense report table with server-side pagination and row actions. */
import type { QTableColumn, QTableProps } from 'quasar'
import { BuildStatus, PublishState, ReportSyncState, type CalcReport } from 'src/api/calc/types'
import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import SearchInput from 'src/components/searchInput/SearchInput.vue'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type { IQTablePagination } from 'src/compositions/types'
import { t } from 'src/i18n/helpers'

defineProps<{
  reports: CalcReport[]
  loading: boolean
  contextMenuItems: IContextMenuItem<CalcReport>[]
}>()
const pagination = defineModel<IQTablePagination>('pagination', { required: true })
const filter = defineModel<string>('filter', { required: true })
const emit = defineEmits<{
  request: [request: Parameters<NonNullable<QTableProps['onRequest']>>[0]]
  create: []
  import: [kind: 'file' | 'link']
  open: [report: CalcReport]
  favorite: [report: CalcReport]
}>()

const columns: ComputedRef<QTableColumn<CalcReport>[]> = computed(() => [
  { name: 'name', label: t('calcWorkspace.reportName'), field: 'name', align: 'left', sortable: true },
  { name: 'description', label: t('calcWorkspace.description'), field: (row) => row.description || '-', align: 'left' },
  { name: 'latestVersionName', label: t('calcWorkspace.latestVersion'), field: (row) => row.latestVersionName || '-', align: 'left' },
  { name: 'originType', label: t('calcWorkspace.origin'), field: (row) => t(`calcWorkspace.origins.${row.originType}`), align: 'left' },
  { name: 'state', label: t('calcWorkspace.state'), field: 'publishState', align: 'left' },
  { name: 'updatedAt', label: t('global.lastModified'), field: 'updatedAt', format: (value) => new Date(String(value)).toLocaleString(), align: 'left', sortable: true },
  { name: 'favorite', label: '', field: 'isFavorite', align: 'center' }
])
/** Map publish state to a restrained status color. */
function publishColor(state: PublishState): string {
  return ({
    [PublishState.Published]: 'positive',
    [PublishState.Unpublished]: 'grey-7',
    [PublishState.UnpublishedChanges]: 'warning',
    [PublishState.WorkspaceVersionMismatch]: 'deep-orange'
  } satisfies Record<PublishState, string>)[state]
}
/** Map synchronization state to a restrained semantic color. */
function syncColor(state: ReportSyncState): string {
  return ({
    [ReportSyncState.NotApplicable]: 'grey-6',
    [ReportSyncState.Current]: 'positive',
    [ReportSyncState.UpdateAvailable]: 'warning',
    [ReportSyncState.SourceUnavailable]: 'negative',
    [ReportSyncState.AccessRevoked]: 'negative'
  } satisfies Record<ReportSyncState, string>)[state]
}
/** Return the localized synchronization-state label. */
function syncLabel(state: ReportSyncState): string { return t(`calcWorkspace.syncStates.${state}`) }
/** Map build state to a restrained status color. */
function buildColor(state: BuildStatus): string {
  return ({
    [BuildStatus.NotRequested]: 'grey-6',
    [BuildStatus.Pending]: 'blue-grey',
    [BuildStatus.Building]: 'info',
    [BuildStatus.Ready]: 'positive',
    [BuildStatus.Failed]: 'negative'
  } satisfies Record<BuildStatus, string>)[state]
}
/** Return the translated publish-state label. */
function publishLabel(state: PublishState): string {
  const labels: Record<PublishState, string> = {
    [PublishState.Unpublished]: t('calcWorkspace.publishStates.unpublished'),
    [PublishState.Published]: t('calcWorkspace.publishStates.published'),
    [PublishState.UnpublishedChanges]: t('calcWorkspace.publishStates.unpublished_changes'),
    [PublishState.WorkspaceVersionMismatch]: t('calcWorkspace.publishStates.workspace_version_mismatch')
  }
  return labels[state]
}
/** Return the translated build-state label. */
function buildLabel(state: BuildStatus): string {
  const labels: Record<BuildStatus, string> = {
    [BuildStatus.NotRequested]: t('calcWorkspace.buildStates.not_requested'),
    [BuildStatus.Pending]: t('calcWorkspace.buildStates.pending'),
    [BuildStatus.Building]: t('calcWorkspace.buildStates.building'),
    [BuildStatus.Ready]: t('calcWorkspace.buildStates.ready'),
    [BuildStatus.Failed]: t('calcWorkspace.buildStates.failed')
  }
  return labels[state]
}
</script>

<style scoped>
.report-table {
  min-width: 0;
  height: 100%;
}

.report-link {
  border: 0;
  padding: 0;
  color: #1565c0;
  background: transparent;
  cursor: pointer;
  font: inherit;
}

.report-link:hover {
  text-decoration: underline;
}
</style>
