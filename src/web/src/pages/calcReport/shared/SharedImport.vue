<template>
  <div class="shared-page row no-wrap full-height">
    <section class="shared-page__details column q-pa-lg">
      <div class="text-h6">{{ preview?.reportName || t('calcWorkspace.sharedReport') }}</div>
      <div class="text-body2 text-grey-7 q-mt-xs">{{ preview?.reportDescription }}</div>
      <q-separator class="q-my-md" />

      <dl v-if="preview" class="shared-page__summary">
        <dt>{{ t('calcWorkspace.version') }}</dt>
        <dd>{{ preview.versionName }}</dd>
        <dt>{{ t('calcWorkspace.dependencies') }}</dt>
        <dd>{{ preview.dependencyCount }}</dd>
        <dt>{{ t('calcWorkspace.archiveSize') }}</dt>
        <dd>{{ formatBytes(preview.totalSize) }}</dd>
        <dt>{{ t('calcWorkspace.permissions') }}</dt>
        <dd>{{ permissionLabel }}</dd>
        <dt v-if="preview.note">{{ t('calcWorkspace.shareNote') }}</dt>
        <dd v-if="preview.note">{{ preview.note }}</dd>
      </dl>

      <template v-if="userStore.token">
        <q-select v-model="categoryOid" dense options-dense outlined emit-value map-options class="q-mt-md"
          :label="t('calcWorkspace.categoryName')" :options="categoryOptions" />
        <q-input v-model="name" dense outlined class="q-mt-sm" :label="t('calcWorkspace.reportName')" />
        <q-toggle v-model="shouldSync" class="q-mt-sm" :label="t('calcWorkspace.keepSynchronized')" />
      </template>

      <div class="row q-gutter-sm q-mt-md">
        <CommonBtn v-if="userStore.token" class="col" icon="move_to_inbox" :label="t('global.import')"
          :loading="isImporting" :disable="!preview || !categoryOid || !name" @click="onImport" />
        <CommonBtn class="col" icon="download" :label="t('calcWorkspace.download')" color="secondary"
          :loading="isDownloading" :disable="!preview" @click="onDownload" />
      </div>
    </section>

    <section class="shared-page__result col">
      <iframe v-if="resultUrl" :src="resultUrl" :title="t('calcWorkspace.recentResult')" />
      <div v-else class="fit flex flex-center text-grey-6">
        <q-spinner v-if="isLoading" size="36px" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
/** Preview, download, and optionally import one local or remote report share. */
import type { CalcReportCategory, SharePreview } from 'src/api/calc/types'
import {
  downloadRemoteShare,
  downloadShare,
  importRemoteShare,
  importShare,
  previewRemoteShare,
  previewShare,
  resolveBackendShareSource,
  resolveShareResultUrl
} from 'src/api/calc/shares'
import { listReportCategories } from 'src/api/calc/categories'
import { useConfig } from 'src/config'
import { useUserInfoStore } from 'src/stores/user'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'

const route = useRoute()
const router = useRouter()
const userStore = useUserInfoStore()
const preview = ref<SharePreview | null>(null)
const categories = ref<CalcReportCategory[]>([])
const categoryOid = ref('')
const name = ref('')
const shouldSync = ref(false)
const isImporting = ref(false)
const isDownloading = ref(false)
const isLoading = ref(true)
const shareToken = ref('')
const backendSource = ref('')
const isLocalBackend = ref(false)

const categoryOptions = computed(() => categories.value.map((category) => ({
  label: category.name,
  value: category.categoryOid
})))
const permissionLabel = computed(() => {
  if (!preview.value) return ''
  return [preview.value.canEdit ? t('calcWorkspace.canEdit') : '', preview.value.canShare ? t('calcWorkspace.canShare') : '']
    .filter(Boolean)
    .join(' · ') || t('calcWorkspace.runOnly')
})
const resultUrl = computed(() => {
  const path = preview.value?.recentExecution?.htmlPath
  if (!path) return ''
  return resolveShareResultUrl(path, isLocalBackend.value, userStore.token)
})

/** Decode the frontend source parameter and classify its backend. */
function resolveShareSource(): void {
  const source = String(route.query.source || '')
  if (!source) throw new Error('Share source is missing')
  const frontendUrl = new URL('/calc-report/shared/import', window.location.origin)
  frontendUrl.searchParams.set('source', source)
  backendSource.value = resolveBackendShareSource(frontendUrl.toString())
  const backendUrl = new URL(backendSource.value)
  const config = useConfig()
  const localApi = new URL(`${config.baseUrl}${config.api}/`, window.location.origin)
  isLocalBackend.value = backendUrl.origin === localApi.origin && backendUrl.pathname.startsWith(localApi.pathname)
  const match = backendUrl.pathname.match(/\/shared\/([^/]+)\/(?:preview|import|archive|result)$/)
  if (!match?.[1]) throw new Error('Share source is invalid')
  shareToken.value = match[1]
}

/** Load the share preview and receiver-owned categories when authenticated. */
async function initialize(): Promise<void> {
  try {
    resolveShareSource()
    const previewResponse = isLocalBackend.value
      ? await previewShare(shareToken.value)
      : await previewRemoteShare(backendSource.value)
    preview.value = previewResponse.data
    name.value = preview.value.reportName
    if (userStore.token) {
      categories.value = (await listReportCategories()).data || []
      categoryOid.value = categories.value[0]?.categoryOid || ''
    }
  } finally {
    isLoading.value = false
  }
}
onMounted(initialize)

/** Confirm opaque-source risk when needed and import the selected share. */
async function onImport(): Promise<void> {
  if (!preview.value || !categoryOid.value || !userStore.token) return
  if (!preview.value.canEdit
    && !await confirmOperation(t('calcWorkspace.executionRiskTitle'), t('calcWorkspace.executionRiskMessage'))) return
  isImporting.value = true
  try {
    const response = isLocalBackend.value
      ? await importShare(shareToken.value, categoryOid.value, name.value, shouldSync.value)
      : await importRemoteShare(backendSource.value, categoryOid.value, name.value, shouldSync.value)
    notifySuccess(t('calcWorkspace.importSucceeded'))
    await router.push(`/calc-report/${response.data.reportOid}/run`)
  } finally {
    isImporting.value = false
  }
}

/** Download the shared archive without requiring an import destination. */
async function onDownload(): Promise<void> {
  if (!preview.value) return
  isDownloading.value = true
  try {
    const response = isLocalBackend.value
      ? await downloadShare(shareToken.value)
      : await downloadRemoteShare(backendSource.value)
    downloadArchiveBlob(response.data, `${sanitizeFilename(preview.value.reportName)}.png`)
  } finally {
    isDownloading.value = false
  }
}

/** Trigger one browser download and release its temporary object URL. */
function downloadArchiveBlob(blob: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(objectUrl)
}

/** Replace path and control characters that are unsafe in download filenames. */
function sanitizeFilename(value: string): string {
  return value.replace(/[<>:"/\\|?*\u0000-\u001F]/g, '_').trim() || 'shared-report'
}

/** Format an archive footprint for compact display. */
function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KiB`
  return `${(value / 1024 / 1024).toFixed(1)} MiB`
}
</script>

<style scoped>
.shared-page {
  min-height: 620px;
  background: #fff;
  overflow: hidden;
}

.shared-page__details {
  width: 340px;
  min-width: 340px;
  border-right: 1px solid #e4e7ec;
}

.shared-page__summary {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px 18px;
  margin: 0;
}

.shared-page__summary dt {
  color: #66736d;
}

.shared-page__summary dd {
  margin: 0;
  text-align: right;
}

.shared-page__result iframe {
  width: 100%;
  height: 100%;
  border: 0;
  background: white;
}

@media (max-width: 760px) {
  .shared-page {
    flex-direction: column;
    overflow: auto;
  }

  .shared-page__details {
    width: 100%;
    min-width: 0;
    border-right: 0;
    border-bottom: 1px solid #e4e7ec;
  }

  .shared-page__result {
    min-height: 520px;
  }
}
</style>
