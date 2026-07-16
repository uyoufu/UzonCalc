<template>
  <div class="version-pane column no-wrap">
    <div class="version-toolbar row items-center q-gutter-sm q-px-sm">
      <CommonBtn icon="publish" :label="t('calcWorkspace.publishVersion')" @click="openPublishDialog" />
      <CommonBtn icon="share" color="grey-8" :label="t('calcWorkspace.share')" @click="isShareDialogOpen = true" />
      <q-space /><q-btn flat round dense icon="refresh" @click="loadVersions"><q-tooltip>{{ t('calcWorkspace.refresh') }}</q-tooltip></q-btn>
    </div>
    <q-separator />
    <q-table flat dense class="col" row-key="versionOid" :rows="versions" :columns="columns" :loading="isLoading">
      <template #body-cell-versionName="slotProps"><q-td :props="slotProps"><span class="text-weight-medium">{{ slotProps.row.versionName }}</span><q-chip v-if="slotProps.row.isLatest" dense square color="primary" text-color="white" class="q-ml-sm">latest</q-chip></q-td></template>
      <template #body-cell-reviewStatus="slotProps"><q-td :props="slotProps"><q-chip dense square :color="reviewColor(slotProps.row.reviewStatus)" text-color="white">{{ reviewLabel(slotProps.row.reviewStatus) }}</q-chip></q-td></template>
      <template #body-cell-actions="slotProps">
        <q-td :props="slotProps" class="q-gutter-xs">
          <q-btn flat round dense icon="bookmark" :disable="slotProps.row.isLatest" @click="onSetLatest(slotProps.row)"><q-tooltip>{{ t('calcWorkspace.setLatest') }}</q-tooltip></q-btn>
          <q-btn flat round dense icon="restore" @click="onRestore(slotProps.row)"><q-tooltip>{{ t('calcWorkspace.restoreWorkspace') }}</q-tooltip></q-btn>
          <q-btn v-if="userStore.isAdmin" flat round dense icon="fact_check" @click="openReviewDialog(slotProps.row)"><q-tooltip>{{ t('calcWorkspace.review') }}</q-tooltip></q-btn>
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="isPublishDialogOpen">
      <q-card class="version-dialog"><q-card-section class="text-subtitle1">{{ t('calcWorkspace.publishVersion') }}</q-card-section>
        <q-card-section class="q-gutter-md"><q-input v-model="publishForm.versionName" dense outlined :label="t('calcWorkspace.version')" hint="MAJOR.MINOR.PATCH" /><q-input v-model="publishForm.description" dense outlined type="textarea" :label="t('calcWorkspace.description')" /></q-card-section>
        <q-card-actions align="right"><CancelBtn v-close-popup /><OkBtn :disable="!isValidVersion" @click="onPublish" /></q-card-actions>
      </q-card>
    </q-dialog>
    <q-dialog v-model="isReviewDialogOpen">
      <q-card class="version-dialog"><q-card-section class="text-subtitle1">{{ t('calcWorkspace.review') }} · {{ reviewingVersion?.versionName }}</q-card-section>
        <q-card-section class="q-gutter-md"><q-select v-model="reviewForm.status" dense outlined emit-value map-options :options="reviewOptions" :label="t('calcWorkspace.reviewStatus')" /><q-input v-model="reviewForm.comment" dense outlined type="textarea" :label="t('calcWorkspace.reviewComment')" /></q-card-section>
        <q-card-actions align="right"><CancelBtn v-close-popup /><OkBtn @click="onReview" /></q-card-actions>
      </q-card>
    </q-dialog>
    <ShareManagerDialog v-model="isShareDialogOpen" :report-oid="reportOid" :report-name="report?.name || ''" />
  </div>
</template>

<script setup lang="ts">
/** Version publication, latest selection, restore, review, and sharing. */
import type { QTableColumn } from 'quasar'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import CancelBtn from 'src/components/quasarWrapper/buttons/CancelBtn.vue'
import OkBtn from 'src/components/quasarWrapper/buttons/OkBtn.vue'
import ShareManagerDialog from '../../shared/ShareManagerDialog.vue'
import type { CalcReport, CalcReportVersion, ReviewStatus } from 'src/api/calc/types'
import { listVersions, publishVersion, restoreWorkspaceVersion, reviewVersion, setLatestVersion } from 'src/api/calc/versions'
import { useUserInfoStore } from 'src/stores/user'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'

const props = defineProps<{ reportOid: string; report: CalcReport | null }>()
const emit = defineEmits<{ changed: []; restored: [] }>()
const router = useRouter()
const userStore = useUserInfoStore()
const versions = ref<CalcReportVersion[]>([])
const isLoading = ref(false)
const isPublishDialogOpen = ref(false)
const isReviewDialogOpen = ref(false)
const isShareDialogOpen = ref(false)
const reviewingVersion = ref<CalcReportVersion | null>(null)
const publishForm = reactive({ versionName: '', description: '' })
const reviewForm = reactive<{ status: ReviewStatus; comment: string }>({ status: 'approved', comment: '' })
const isValidVersion = computed(() => /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(publishForm.versionName) && !versions.value.some((version) => version.versionName === publishForm.versionName))
const columns: QTableColumn<CalcReportVersion>[] = [
  { name: 'versionName', label: t('calcWorkspace.version'), field: 'versionName', align: 'left' },
  { name: 'description', label: t('calcWorkspace.description'), field: (row) => row.description || '-', align: 'left' },
  { name: 'reviewStatus', label: t('calcWorkspace.reviewStatus'), field: 'reviewStatus', align: 'left' },
  { name: 'createdAt', label: t('calcWorkspace.publishedAt'), field: 'createdAt', format: (value) => new Date(String(value)).toLocaleString(), align: 'left' },
  { name: 'actions', label: '', field: 'versionOid', align: 'right' }
]
const reviewOptions = computed(() => [
  { label: t('calcWorkspace.reviewStates.pending'), value: 'pending' },
  { label: t('calcWorkspace.reviewStates.approved'), value: 'approved' },
  { label: t('calcWorkspace.reviewStates.rejected'), value: 'rejected' }
])

/** Load all immutable versions for the report. */
async function loadVersions(): Promise<void> { isLoading.value = true; try { const response = await listVersions(props.reportOid); versions.value = response.data || [] } finally { isLoading.value = false } }
onMounted(loadVersions)
/** Suggest the next patch version and open publication. */
function openPublishDialog(): void {
  const latest = versions.value[0]?.versionName?.split('.').map(Number)
  publishForm.versionName = latest?.length === 3 ? `${latest[0]}.${latest[1]}.${(latest[2] || 0) + 1}` : '1.0.0'
  publishForm.description = ''
  isPublishDialogOpen.value = true
}
/** Publish the current saved workspace. */
async function onPublish(): Promise<void> { await publishVersion(props.reportOid, publishForm.versionName, publishForm.description || null); isPublishDialogOpen.value = false; await loadVersions(); emit('changed'); notifySuccess(t('calcWorkspace.versionPublished')) }
/** Move latest without modifying the workspace. */
async function onSetLatest(version: CalcReportVersion): Promise<void> { await setLatestVersion(props.reportOid, version.versionName); await loadVersions(); emit('changed') }
/** Restore a version into workspace after explicit confirmation. */
async function onRestore(version: CalcReportVersion): Promise<void> {
  if (!await confirmOperation(t('calcWorkspace.restoreWorkspace'), version.versionName)) return
  await restoreWorkspaceVersion(props.reportOid, version.versionName)
  emit('restored')
  await router.push(`/calc-report/${props.reportOid}/workspace`)
}
/** Open administrator review controls for one version. */
function openReviewDialog(version: CalcReportVersion): void { reviewingVersion.value = version; reviewForm.status = version.reviewStatus; reviewForm.comment = version.reviewComment || ''; isReviewDialogOpen.value = true }
/** Submit an administrator review outcome. */
async function onReview(): Promise<void> { if (!reviewingVersion.value) return; await reviewVersion(props.reportOid, reviewingVersion.value.versionName, reviewForm.status, reviewForm.comment || null); isReviewDialogOpen.value = false; await loadVersions() }
/** Map review status to a semantic color. */
function reviewColor(status: ReviewStatus): string { return ({ pending: 'grey-7', approved: 'positive', rejected: 'negative' })[status] }
/** Return the translated review-state label. */
function reviewLabel(status: ReviewStatus): string { return ({ pending: t('calcWorkspace.reviewStates.pending'), approved: t('calcWorkspace.reviewStates.approved'), rejected: t('calcWorkspace.reviewStates.rejected') })[status] }
</script>

<style scoped>.version-pane { height: 100%; min-height: 620px; background: #fff; }.version-toolbar { min-height: 48px; }.version-dialog { width: min(520px, 92vw); max-width: 520px; }</style>
