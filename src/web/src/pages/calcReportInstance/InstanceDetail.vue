<template>
  <div class="instance-detail column no-wrap full-height">
    <header class="instance-detail__header row items-center q-gutter-sm q-px-md">
      <CommonBtn flat dense icon="arrow_back" :tooltip="t('global.back')" @click="router.push('/calc-report-instance/list')" />
      <div>
        <div class="text-subtitle1">{{ instance?.name }}</div>
        <div class="text-caption text-grey-7">{{ instance?.reportName }} · {{ instance?.sourceVersion || ExecutionSourceType.Workspace }}</div>
      </div>
      <q-space />
    </header>
    <q-separator />
    <ExecutionPane v-if="instance" class="col" :report-oid="instance.reportOid" :initial-source="initialSource"
      :instance-oid="instance.instanceOid"
      :initial-execution="initialExecution" :auto-restore-history="false" :show-save-instance-button="false"
      @execution-changed="onExecutionChanged" />
  </div>
</template>

<script setup lang="ts">
/** Edit stored instance parameters through the shared execution pane. */
defineOptions({ name: 'CalcReportInstanceDetail' })
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import ExecutionPane from '../calcExecution/components/ExecutionPane.vue'
import { ExecutionSourceType, ExecutionStatus, ExecutorType, SandboxBackendMode, HtmlUpdateType, type CalcExecution, type CalcInstance } from 'src/api/calc/types'
import { getInstance } from 'src/api/calc/instances'
import { useConfig } from 'src/config'
import { t } from 'src/i18n/helpers'

const route = useRoute()
const router = useRouter()
const instance = ref<CalcInstance | null>(null)
const initialSource = computed(() => instance.value?.sourceVersion ? ExecutionSourceType.Version : ExecutionSourceType.Workspace)
const initialExecution = computed<CalcExecution | null>(() => {
  if (!instance.value) return null
  return {
    executionId: instance.value.executionId || `instance:${instance.value.instanceOid}`,
    reportOid: instance.value.reportOid,
    sourceType: initialSource.value,
    resolvedVersion: instance.value.sourceVersion,
    sourceArtifactHash: '',
    executionArtifactHash: '',
    bundleHash: instance.value.bundleHash,
    runtimeFingerprint: '',
    executorType: ExecutorType.Local,
    backendMode: SandboxBackendMode.InProcess,
    status: ExecutionStatus.Succeeded,
    isCompleted: true,
    windows: instance.value.inputWindows,
    htmlPath: new URL(instance.value.resultPath, `${useConfig().baseUrl}${useConfig().api}/`).toString(),
    updateType: HtmlUpdateType.Full,
    htmlContentPatch: null,
    createdAt: instance.value.createdAt,
    completedAt: instance.value.updatedAt
  }
})

/** Load saved instance metadata before mounting the execution pane. */
async function loadInstance(): Promise<void> {
  instance.value = (await getInstance(String(route.params.instanceOid))).data
}
onMounted(loadInstance)

/** Refresh instance metadata after its retained execution completes. */
async function onExecutionChanged(nextExecution: CalcExecution): Promise<void> {
  if (nextExecution.isCompleted) await loadInstance()
}
</script>

<style scoped>
.instance-detail { min-height: 620px; background: #fff; }
.instance-detail__header { min-height: 58px; }
</style>
