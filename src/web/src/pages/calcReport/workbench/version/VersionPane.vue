<template>
  <div class="version-pane column no-wrap">
    <div class="version-toolbar row items-center q-gutter-sm q-px-sm">
      <CommonBtn icon="publish" :label="t('calcWorkspace.publishVersion')" @click="openPublishDialog" />
      <CommonBtn icon="share" color="grey-8" :label="t('calcWorkspace.share')" @click="onOpenShareDialog" />
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
/** Version publication, latest selection, restore, review, and sharing. */
import type { QTableColumn } from 'quasar'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import type { CalcReport, CalcReportVersion, ReviewStatus } from 'src/api/calc/types'
import { listVersions, publishVersion, restoreWorkspaceVersion, reviewVersion, setLatestVersion } from 'src/api/calc/versions'
import { useUserInfoStore } from 'src/stores/user'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'
import { useVersionDialogs } from './useVersionDialogs'
import { useShareManagerDialog } from '../../shared/useShareManagerDialog'

const props = defineProps<{ reportOid: string; report: CalcReport | null }>()
const emit = defineEmits<{ changed: []; restored: [] }>()
const router = useRouter()
const userStore = useUserInfoStore()
const versions = ref<CalcReportVersion[]>([])
const isLoading = ref(false)
const { openPublishDialog: showPublishDialog, openReviewDialog: showReviewDialog } = useVersionDialogs()
const { openShareManagerDialog } = useShareManagerDialog()
const columns: QTableColumn<CalcReportVersion>[] = [
  { name: 'versionName', label: t('calcWorkspace.version'), field: 'versionName', align: 'left' },
  { name: 'description', label: t('calcWorkspace.description'), field: (row) => row.description || '-', align: 'left' },
  { name: 'reviewStatus', label: t('calcWorkspace.reviewStatus'), field: 'reviewStatus', align: 'left' },
  { name: 'createdAt', label: t('calcWorkspace.publishedAt'), field: 'createdAt', format: (value) => new Date(String(value)).toLocaleString(), align: 'left' },
  { name: 'actions', label: '', field: 'versionOid', align: 'right' }
]
/** Load all immutable versions for the report. */
async function loadVersions(): Promise<void> { isLoading.value = true; try { const response = await listVersions(props.reportOid); versions.value = response.data || [] } finally { isLoading.value = false } }
onMounted(loadVersions)
/** Publish the current saved workspace from a validated dialog. */
async function openPublishDialog(): Promise<void> {
  const isPublished = await showPublishDialog(versions.value, async (input) => {
    await publishVersion(props.reportOid, input.versionName, input.description || null)
  })
  if (!isPublished) return
  await loadVersions()
  emit('changed')
  notifySuccess(t('calcWorkspace.versionPublished'))
}
/** Move latest without modifying the workspace. */
async function onSetLatest(version: CalcReportVersion): Promise<void> { await setLatestVersion(props.reportOid, version.versionName); await loadVersions(); emit('changed') }
/** Restore a version into workspace after explicit confirmation. */
async function onRestore(version: CalcReportVersion): Promise<void> {
  if (!await confirmOperation(t('calcWorkspace.restoreWorkspace'), version.versionName)) return
  await restoreWorkspaceVersion(props.reportOid, version.versionName)
  emit('restored')
  await router.push(`/calc-report/${props.reportOid}/workspace`)
}
/** Open administrator review controls and refresh the confirmed result. */
async function openReviewDialog(version: CalcReportVersion): Promise<void> {
  const isReviewed = await showReviewDialog(version, async (input) => {
    await reviewVersion(props.reportOid, version.versionName, input.status, input.comment || null)
  })
  if (isReviewed) await loadVersions()
}
/** Open share-link management for the current report. */
async function onOpenShareDialog(): Promise<void> {
  await openShareManagerDialog(props.reportOid, props.report?.name || '')
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
</style>
