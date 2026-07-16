<template>
  <div v-if="$q.screen.lt.md" class="version-unsupported column items-center justify-center full-height text-grey-7">
    <q-icon name="desktop_windows" size="56px" />
    <div class="text-subtitle1 q-mt-md">{{ t('calcWorkspace.desktopRequired') }}</div>
  </div>
  <div v-else class="version-pane column no-wrap">
    <div class="version-toolbar row items-center q-gutter-sm q-px-sm">
      <q-btn flat round dense icon="arrow_back" @click="onBackToReports"><q-tooltip>{{
        t('calcWorkspace.backToReports') }}</q-tooltip></q-btn>
      <CommonBtn icon="publish" :label="t('calcWorkspace.publishVersion')" @click="openPublishDialog" />
      <q-space /><q-btn flat round dense icon="refresh" @click="loadVersions"><q-tooltip>{{ t('calcWorkspace.refresh')
          }}</q-tooltip></q-btn>
    </div>
    <q-separator />
    <q-table flat dense class="col" row-key="versionOid" :rows="versions" :columns="columns" :loading="isLoading">
      <template #body-cell-versionName="slotProps"><q-td :props="slotProps"><span class="text-weight-medium">{{
        slotProps.row.versionName }}</span><q-chip v-if="slotProps.row.isLatest" dense square color="primary"
            text-color="white" class="q-ml-sm">latest</q-chip></q-td></template>
      <template #body-cell-reviewStatus="slotProps"><q-td :props="slotProps"><q-chip dense square
            :color="reviewColor(slotProps.row.reviewStatus)" text-color="white">{{
              reviewLabel(slotProps.row.reviewStatus) }}</q-chip></q-td></template>
      <template #body-cell-actions="slotProps">
        <q-td :props="slotProps" class="q-gutter-xs">
          <q-btn flat round dense icon="bookmark" :disable="slotProps.row.isLatest"
            @click="onSetLatest(slotProps.row)"><q-tooltip>{{ t('calcWorkspace.setLatest') }}</q-tooltip></q-btn>
          <q-btn flat round dense icon="restore" @click="onRestore(slotProps.row)"><q-tooltip>{{
            t('calcWorkspace.restoreWorkspace') }}</q-tooltip></q-btn>
          <q-btn v-if="userStore.isAdmin" flat round dense icon="fact_check"
            @click="openReviewDialog(slotProps.row)"><q-tooltip>{{ t('calcWorkspace.review') }}</q-tooltip></q-btn>
        </q-td>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
/** Version publication, latest selection, restore, and review route page. */
defineOptions({ name: 'CalcReportVersions' })
import type { QTableColumn } from 'quasar'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import type { CalcReportVersion, ReviewStatus } from 'src/api/calc/types'
import { listVersions, publishVersion, restoreWorkspaceVersion, reviewVersion, setLatestVersion } from 'src/api/calc/versions'
import { useUserInfoStore } from 'src/stores/user'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'
import { useVersionDialogs } from './useVersionDialogs'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const reportOid = computed(() => String(route.params.reportOid || ''))
const userStore = useUserInfoStore()
const versions = ref<CalcReportVersion[]>([])
const isLoading = ref(false)
const { openPublishDialog: showPublishDialog, openReviewDialog: showReviewDialog } = useVersionDialogs()
const columns: QTableColumn<CalcReportVersion>[] = [
  { name: 'versionName', label: t('calcWorkspace.version'), field: 'versionName', align: 'left' },
  { name: 'description', label: t('calcWorkspace.description'), field: (row) => row.description || '-', align: 'left' },
  { name: 'reviewStatus', label: t('calcWorkspace.reviewStatus'), field: 'reviewStatus', align: 'left' },
  { name: 'createdAt', label: t('calcWorkspace.publishedAt'), field: 'createdAt', format: (value) => new Date(String(value)).toLocaleString(), align: 'left' },
  { name: 'actions', label: '', field: 'versionOid', align: 'right' }
]
/** Load all immutable versions for the report. */
async function loadVersions(): Promise<void> { isLoading.value = true; try { const response = await listVersions(reportOid.value); versions.value = response.data || [] } finally { isLoading.value = false } }
watch(reportOid, loadVersions, { immediate: true })
/** Return to the calculation-report list. */
async function onBackToReports(): Promise<void> { await router.push('/calc-report/list') }
/** Publish the current saved workspace from a validated dialog. */
async function openPublishDialog(): Promise<void> {
  const isPublished = await showPublishDialog(versions.value, async (input) => {
    await publishVersion(reportOid.value, input.versionName, input.description || null)
  })
  if (!isPublished) return
  await loadVersions()
  notifySuccess(t('calcWorkspace.versionPublished'))
}
/** Move latest without modifying the workspace. */
async function onSetLatest(version: CalcReportVersion): Promise<void> { await setLatestVersion(reportOid.value, version.versionName); await loadVersions() }
/** Restore a version into workspace after explicit confirmation. */
async function onRestore(version: CalcReportVersion): Promise<void> {
  if (!await confirmOperation(t('calcWorkspace.restoreWorkspace'), version.versionName)) return
  await restoreWorkspaceVersion(reportOid.value, version.versionName)
  await router.push(`/calc-report/${reportOid.value}/workspace`)
}
/** Open administrator review controls and refresh the confirmed result. */
async function openReviewDialog(version: CalcReportVersion): Promise<void> {
  const isReviewed = await showReviewDialog(version, async (input) => {
    await reviewVersion(reportOid.value, version.versionName, input.status, input.comment || null)
  })
  if (isReviewed) await loadVersions()
}
/** Map review status to a semantic color. */
function reviewColor(status: ReviewStatus): string { return ({ pending: 'grey-7', approved: 'positive', rejected: 'negative' })[status] }
/** Return the translated review-state label. */
function reviewLabel(status: ReviewStatus): string { return ({ pending: t('calcWorkspace.reviewStates.pending'), approved: t('calcWorkspace.reviewStates.approved'), rejected: t('calcWorkspace.reviewStates.rejected') })[status] }
</script>

<style
  scoped>
  .version-pane {
    height: 100%;
    min-height: 620px;
    background: #fff;
  }

  .version-toolbar {
    min-height: 48px;
  }

  .version-unsupported {
    min-height: 520px;
    background: #fff;
  }
</style>
