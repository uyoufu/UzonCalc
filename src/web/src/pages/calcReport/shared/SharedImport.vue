<template>
  <div class="shared-import column items-center q-pa-xl">
    <section class="shared-import__content">
      <div class="text-h6">{{ preview?.reportName || t('calcWorkspace.sharedReport') }}</div>
      <div class="text-body2 text-grey-7 q-mt-xs">{{ preview?.reportDescription }}</div>
      <q-separator class="q-my-lg" />
      <dl v-if="preview" class="shared-import__summary">
        <dt>{{ t('calcWorkspace.version') }}</dt><dd>{{ preview.versionName }}</dd>
        <dt>{{ t('calcWorkspace.dependencies') }}</dt><dd>{{ preview.dependencyCount }}</dd>
        <dt>{{ t('calcWorkspace.files') }}</dt><dd>{{ preview.totalFileCount }}</dd>
        <dt>{{ t('calcWorkspace.totalSize') }}</dt><dd>{{ formatBytes(preview.totalSize) }}</dd>
      </dl>
      <div class="q-gutter-md q-mt-lg">
        <q-select v-model="categoryOid" dense outlined emit-value map-options :options="categoryOptions" :label="t('calcWorkspace.categoryName')" />
        <q-input v-model="name" dense outlined :label="t('calcWorkspace.importName')" />
      </div>
      <div class="row justify-end q-mt-lg"><CommonBtn icon="download" :label="t('calcWorkspace.importSharedReport')" :loading="isImporting" :disable="!categoryOid" @click="onImport" /></div>
    </section>
  </div>
</template>

<script setup lang="ts">
/** Preview and import an authenticated approved report share. */
defineOptions({ name: 'CalcReportSharedImport' })
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import type { CalcReportCategory, SharePreview } from 'src/api/calc/types'
import { previewShare, importShare } from 'src/api/calc/shares'
import { listReportCategories } from 'src/api/calc/categories'
import { t } from 'src/i18n/helpers'

const route = useRoute(); const router = useRouter(); const token = computed(() => String(route.params.token || ''))
const preview = ref<SharePreview | null>(null); const categories = ref<CalcReportCategory[]>([]); const categoryOid = ref(''); const name = ref(''); const isImporting = ref(false)
const categoryOptions = computed(() => categories.value.map((category) => ({ label: category.name, value: category.categoryOid })))
/** Load share footprint and receiver categories without consuming the token. */
async function initialize(): Promise<void> { const [previewResponse, categoryResponse] = await Promise.all([previewShare(token.value), listReportCategories()]); preview.value = previewResponse.data; categories.value = categoryResponse.data || []; categoryOid.value = categories.value[0]?.categoryOid || ''; name.value = preview.value.reportName }
onMounted(initialize)
/** Consume the share and navigate to the receiver-owned workspace. */
async function onImport(): Promise<void> { isImporting.value = true; try { const response = await importShare(token.value, categoryOid.value, name.value || null); await router.replace(`/calc-report/${response.data.reportOid}/workspace`) } finally { isImporting.value = false } }
/** Format the preview's total byte size. */
function formatBytes(size: number): string { return size < 1048576 ? `${(size / 1024).toFixed(1)} KB` : `${(size / 1048576).toFixed(1)} MB` }
</script>

<style scoped>.shared-import { min-height: 620px; background: #fff; }.shared-import__content { width: min(620px, 100%); }.shared-import__summary { display: grid; grid-template-columns: 160px 1fr; gap: 8px 16px; }.shared-import__summary dt { color: #667085; }.shared-import__summary dd { margin: 0; }</style>
