<template>
  <div class="execution-result-frame full-height">
    <div v-if="!documentUrl" class="full-height column items-center justify-center text-grey-6">
      <q-icon name="article" size="52px" /><div class="q-mt-sm">{{ t('calcWorkspace.runToPreview') }}</div>
    </div>
    <iframe v-else ref="iframe" :src="iframeUrl" title="Calculation result" @load="postRuntimeInfo" />
  </div>
</template>

<script setup lang="ts">
/** Render cached calculation HTML for the report-run page and apply partial content patches. */
import type { CalcExecution } from 'src/api/calc/types'
import { HtmlUpdateType } from 'src/api/calc/types'
import { useConfig } from 'src/config'
import { useUserInfoStore } from 'src/stores/user'
import { t } from 'src/i18n/helpers'

const props = defineProps<{ execution: CalcExecution | null }>()
const iframe = ref<HTMLIFrameElement | null>(null)
const userStore = useUserInfoStore()
const documentUrl = computed(() => props.execution?.htmlPath || '')
const iframeUrl = ref('')

/** Build an absolute public result URL from a backend-relative path. */
function absoluteResultUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`
  return new URL(normalized, useConfig().baseUrl).toString()
}

watch(() => props.execution, (execution) => {
  if (!execution?.htmlPath || execution.updateType === HtmlUpdateType.None) return
  const fullUrl = absoluteResultUrl(execution.htmlPath)
  if (execution.updateType === HtmlUpdateType.Partial && execution.htmlContentPatch && iframe.value?.contentWindow) {
    iframe.value.contentWindow.postMessage({ type: 'uzoncalc:update-content', contentHtml: execution.htmlContentPatch, documentUrl: fullUrl, authToken: userStore.token }, '*')
    return
  }
  iframeUrl.value = fullUrl
}, { immediate: true })

/** Provide result-page runtime helpers after each full iframe load. */
function postRuntimeInfo(): void {
  if (!iframe.value?.contentWindow || !documentUrl.value) return
  iframe.value.contentWindow.postMessage({ type: 'uzoncalc:update-runtime', documentUrl: absoluteResultUrl(documentUrl.value), authToken: userStore.token }, '*')
}
</script>

<style scoped>.execution-result-frame { min-height: 420px; background: #fff; }.execution-result-frame iframe { width: 100%; height: 100%; border: 0; }</style>
