<template>
  <div class="version-pane column no-wrap">
    <div class="version-toolbar row items-center q-gutter-sm q-px-sm">
      <CommonBtn flat dense icon="arrow_back" :tooltip="t('calcWorkspace.backToReports')" @click="onBackToReports" />
      <q-space />
      <CommonBtn flat dense icon="refresh" :tooltip="t('calcWorkspace.refresh')" @click="loadVersions" />
    </div>
    <q-separator />
    <q-table flat dense class="col" row-key="versionOid" :rows="versions" :columns="columns" :loading="loading"
      v-model:pagination="pagination" :filter="filter" binary-state-sort>
      <template #body-cell-versionName="slotProps"><q-td :props="slotProps"><span class="text-weight-medium">{{
        slotProps.row.versionName }}</span><q-chip v-if="slotProps.row.isLatest" dense square color="primary"
            text-color="white" class="q-ml-sm">latest</q-chip></q-td></template>
      <template #body-cell-actions="slotProps">
        <q-td :props="slotProps" class="q-gutter-xs">
          <CommonBtn flat dense icon="bookmark" :disable="slotProps.row.isLatest"
            :tooltip="t('calcWorkspace.setLatest')" @click="onSetLatest(slotProps.row)" />
          <CommonBtn flat dense icon="restore" :tooltip="t('calcWorkspace.restoreWorkspace')"
            @click="onRestore(slotProps.row)" />
        </q-td>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
/** Version listing, latest selection, and workspace restore route page. */
defineOptions({ name: 'CalcReportVersions' })
import type { QTableColumn } from 'quasar'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import type { CalcReportVersion } from 'src/api/calc/types'
import { listVersions, restoreWorkspaceVersion, setLatestVersion } from 'src/api/calc/versions'
import { confirmOperation } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'
import { useQTable } from 'src/compositions/qTableUtils'
import { formatDate } from 'src/utils/format'

const route = useRoute()
const router = useRouter()
const reportOid = computed(() => String(route.params.reportOid || ''))
const columns: ComputedRef<QTableColumn<CalcReportVersion>[]> = computed(() => [
  { name: 'versionName', label: t('calcWorkspace.version'), field: 'versionName', align: 'left', sortable: true },
  { name: 'description', label: t('calcWorkspace.description'), field: (row) => row.description || '-', align: 'left' },
  { name: 'createdAt', label: t('calcWorkspace.publishedAt'), field: 'createdAt', format: (value) => formatDate(value), align: 'left', sortable: true },
  { name: 'actions', label: '', field: 'versionOid', align: 'right' }
])
const {
  rows: versions,
  pagination,
  filter,
  loading,
  updateExistOne
} = useQTable<CalcReportVersion>({ preventRequestWhenMounted: true })
/** Load all immutable versions for the report. */
async function loadVersions(): Promise<void> { loading.value = true; try { const response = await listVersions(reportOid.value); versions.value = response.data || [] } finally { loading.value = false } }
watch(reportOid, loadVersions, { immediate: true })
/** Return to the calculation-report list. */
async function onBackToReports(): Promise<void> { await router.push('/calc-report/list') }
/** Move latest without modifying the workspace. */
async function onSetLatest(version: CalcReportVersion): Promise<void> { const response = await setLatestVersion(reportOid.value, version.versionName); replaceLatestVersion(response.data); updateExistOne(response.data, 'versionOid') }
/** Restore a version into workspace after explicit confirmation. */
async function onRestore(version: CalcReportVersion): Promise<void> {
  if (!await confirmOperation(t('calcWorkspace.restoreWorkspace'), version.versionName)) return
  await restoreWorkspaceVersion(reportOid.value, version.versionName)
  await router.push(`/calc-report/${reportOid.value}/workspace`)
}
/** Mark the previous latest version as non-latest before applying a replacement. */
function replaceLatestVersion(latestVersion: CalcReportVersion): void {
  const previousLatest = versions.value.find((version) => version.isLatest && version.versionOid !== latestVersion.versionOid)
  if (previousLatest) updateExistOne({ ...previousLatest, isLatest: false }, 'versionOid')
}
</script>

<style scoped>
.version-pane {
  height: 100%;
  min-height: 620px;
  background: #fff;
}

.version-toolbar {
  min-height: 48px;
}
</style>
