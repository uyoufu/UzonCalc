<template>
  <div class="instance-detail column no-wrap full-height">
    <header class="instance-detail__header row items-center q-gutter-sm q-px-md">
      <q-btn flat round dense icon="arrow_back" @click="router.push('/calc-report-instance/list')" />
      <div><div class="text-subtitle1">{{ instance?.name }}</div><div class="text-caption text-grey-7">{{ instance?.reportName }} · {{ instance?.sourceVersion || 'workspace' }}</div></div>
      <q-space /><CommonBtn icon="refresh" :label="t('calcWorkspace.recalculate')" :loading="isExecuting" @click="onRecalculate" /><CommonBtn v-if="execution?.isCompleted" icon="save" color="grey-8" :label="t('calcWorkspace.updateInstanceResult')" @click="onUpdateResult" />
    </header>
    <q-separator />
    <div class="col">
      <ExecutionResultFrame v-if="execution" :execution="execution" />
      <iframe v-else-if="resultUrl" :src="resultUrl" title="Saved calculation result" />
    </div>
  </div>
</template>

<script setup lang="ts">
/** View a saved result and recalculate it from the closest supported source. */
defineOptions({ name: 'CalcReportInstanceDetail' })
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import ExecutionResultFrame from '../calcReport/workbench/execution/ExecutionResultFrame.vue'
import type { CalcExecution, CalcInstance } from 'src/api/calc/types'
import { getInstance, updateInstanceResult } from 'src/api/calc/instances'
import { startExecution } from 'src/api/calc/executions'
import { adaptExecutionFields } from '../calcReport/workbench/execution/adaptExecutionFields'
import { useConfig } from 'src/config'
import { notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'

const route = useRoute(); const router = useRouter()
const instance = ref<CalcInstance | null>(null)
const execution = ref<CalcExecution | null>(null)
const isExecuting = ref(false)
const resultUrl = computed(() => instance.value?.resultPath ? new URL(instance.value.resultPath.startsWith('/') ? instance.value.resultPath : `/${instance.value.resultPath}`, useConfig().baseUrl).toString() : '')
/** Load saved instance metadata. */
async function loadInstance(): Promise<void> { const response = await getInstance(String(route.params.instanceOid)); instance.value = response.data }
onMounted(loadInstance)
/** Recalculate with the stored defaults and the original root version when available. */
async function onRecalculate(): Promise<void> { if (!instance.value) return; isExecuting.value = true; try { const source = instance.value.sourceVersion ? { type: 'version' as const, versionName: instance.value.sourceVersion } : { type: 'workspace' as const }; const response = await startExecution({ reportOid: instance.value.reportOid, source, defaults: instance.value.defaults, isSilent: true }); execution.value = adaptExecutionFields(response.data) } finally { isExecuting.value = false } }
/** Replace the persisted result using optimistic instance revision. */
async function onUpdateResult(): Promise<void> { if (!instance.value || !execution.value) return; const response = await updateInstanceResult(instance.value.instanceOid, instance.value.revision, execution.value.executionId); instance.value = response.data; execution.value = null; notifySuccess(t('calcWorkspace.instanceUpdated')) }
</script>

<style scoped>.instance-detail { min-height: 620px; background: #fff; }.instance-detail__header { min-height: 58px; }.instance-detail iframe { width: 100%; height: 100%; border: 0; }</style>
