<template>
  <div class="execution-pane column no-wrap">
    <div class="execution-toolbar row items-center q-gutter-sm q-px-sm">
      <q-select v-model="sourceType" dense outlined emit-value map-options :options="sourceOptions"
        :label="t('calcWorkspace.executionSource')" class="execution-toolbar__source" />
      <q-select v-if="sourceType === 'version'" v-model="versionName" dense outlined emit-value map-options
        :options="versionOptions" :label="t('calcWorkspace.version')" class="execution-toolbar__version" />
      <q-toggle v-model="isSilent" :label="t('calcWorkspace.silentRun')" />
      <CommonBtn v-if="!execution || execution.isCompleted" icon="play_arrow" :label="t('calcWorkspace.startRun')"
        :loading="isExecuting" @click="onStart" />
      <CommonBtn v-else icon="skip_next" :label="t('calcWorkspace.continueRun')" :loading="isExecuting"
        @click="onContinue" />
      <q-btn v-if="execution && !execution.isCompleted" flat round dense icon="stop" color="negative"
        @click="onTerminate"><q-tooltip>{{ t('calcWorkspace.terminate') }}</q-tooltip></q-btn>
      <q-space />
      <CommonBtn v-if="execution?.isCompleted" icon="save_as" color="grey-8" :label="t('calcWorkspace.saveInstance')"
        @click="onOpenSaveInstanceDialog" />
    </div>
    <q-separator />
    <q-banner v-if="buildMessage" dense class="bg-blue-grey-1 text-blue-grey-10">
      <template #avatar><q-spinner v-if="isWaitingForBuild" color="primary" /><q-icon v-else name="error"
          color="negative" /></template>
      {{ buildMessage }}
    </q-banner>
    <div class="row no-wrap col execution-body">
      <section class="execution-input column no-wrap">
        <div v-if="execution" class="execution-provenance q-pa-sm text-caption">
          <div>{{ execution.sourceType }}<span v-if="execution.resolvedVersion"> · {{ execution.resolvedVersion
              }}</span>
          </div>
          <div class="ellipsis text-grey-7">{{ execution.backendMode }} · {{ execution.bundleHash }}</div>
        </div>
        <q-separator />
        <q-scroll-area class="col">
          <div v-if="execution?.windows.length" class="q-pa-sm q-gutter-md">
            <section v-for="windowInfo in execution.windows" :key="windowInfo.title">
              <div class="text-subtitle2 q-mb-xs">{{ windowInfo.title }}</div>
              <LowCodeForm :fields="windowInfo.fields" sync-value one-column :disable-default-btns="['ok', 'cancel']" />
              <div v-if="windowInfo.caption" class="text-caption text-grey-7">{{ windowInfo.caption }}</div>
            </section>
          </div>
          <div v-else class="q-pa-md text-grey-6">{{ t('calcWorkspace.noInputs') }}</div>
        </q-scroll-area>
      </section>
      <q-separator vertical />
      <section class="col">
        <ExecutionResultFrame :execution="execution" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
/** Run and continue managed calculations while showing immutable provenance. */
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import LowCodeForm from 'src/components/lowCode/LowCodeForm.vue'
import ExecutionResultFrame from './ExecutionResultFrame.vue'
import { useSaveInstanceDialog } from './useSaveInstanceDialog'
import type { CalcExecution, CalcReport, CalcReportVersion, ExecutionSourceType } from 'src/api/calc/types'
import { continueExecution, startExecution, terminateExecution, type ExecutionDefaults } from 'src/api/calc/executions'
import { listVersions } from 'src/api/calc/versions'
import { adaptExecutionFields } from './adaptExecutionFields'
import { getWorkspaceBuild } from 'src/api/calc/workspace'
import { CalcErrorCode } from 'src/api/calc/types'
import { getApiFailure } from '../../shared/apiFailure'
import { notifyError } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'

const props = defineProps<{ reportOid: string; report: CalcReport | null }>()
const route = useRoute()
const versions = ref<CalcReportVersion[]>([])
const sourceType = ref<ExecutionSourceType>((route.query.source as ExecutionSourceType) || (props.report?.latestVersionName ? 'latest' : 'workspace'))
const versionName = ref<string | null>(null)
const isSilent = ref(false)
const isExecuting = ref(false)
const isWaitingForBuild = ref(false)
const buildMessage = ref('')
let buildPollTimer: ReturnType<typeof setTimeout> | null = null
const execution = ref<CalcExecution | null>(null)
const { openSaveInstanceDialog } = useSaveInstanceDialog()
const sourceOptions = computed(() => [
  { label: t('calcWorkspace.sourceWorkspace'), value: 'workspace' },
  { label: t('calcWorkspace.sourceLatest'), value: 'latest', disable: !props.report?.latestVersionName },
  { label: t('calcWorkspace.sourceVersion'), value: 'version', disable: versions.value.length === 0 }
])
const versionOptions = computed(() => versions.value.map((version) => ({ label: version.versionName, value: version.versionName })))

onMounted(async () => {
  const response = await listVersions(props.reportOid)
  versions.value = response.data || []
  versionName.value = versions.value.find((version) => version.isLatest)?.versionName || versions.value[0]?.versionName || null
})

/** Collect current values from all returned input windows. */
function collectDefaults(): ExecutionDefaults {
  const defaults: ExecutionDefaults = {}
  execution.value?.windows.forEach((windowInfo) => {
    defaults[windowInfo.title] = Object.fromEntries(windowInfo.fields.map((field) => [field.name, field.value]))
  })
  return defaults
}
/** Start a new managed execution. */
async function onStart(): Promise<void> {
  isExecuting.value = true
  try {
    const source = sourceType.value === 'version' ? { type: sourceType.value, versionName: versionName.value || undefined } : { type: sourceType.value }
    const response = await startExecution({ reportOid: props.reportOid, source, isSilent: isSilent.value, defaults: execution.value ? collectDefaults() : {}, lastHtmlPath: execution.value?.htmlPath })
    execution.value = adaptExecutionFields(response.data)
    buildMessage.value = ''
  } catch (error) {
    const failure = getApiFailure(error)
    if (failure.errorCode === CalcErrorCode.ExecutionArtifactNotReady) {
      buildMessage.value = t('calcWorkspace.buildWaiting')
      isWaitingForBuild.value = true
      scheduleBuildPoll()
    } else if (failure.errorCode === CalcErrorCode.ExecutionArtifactBuildFailed) {
      buildMessage.value = `${t('calcWorkspace.buildFailed')}: ${JSON.stringify(failure.data || {})}`
    } else {
      notifyError(failure.message)
    }
  } finally { isExecuting.value = false }
}
/** Schedule one build-state poll without overlapping requests. */
function scheduleBuildPoll(): void {
  if (buildPollTimer) clearTimeout(buildPollTimer)
  buildPollTimer = setTimeout(() => { void pollWorkspaceBuild() }, 1500)
}
/** Poll the configured runtime build until it is ready or failed. */
async function pollWorkspaceBuild(): Promise<void> {
  const response = await getWorkspaceBuild(props.reportOid)
  if (response.data.buildStatus === 'ready') {
    isWaitingForBuild.value = false
    buildMessage.value = t('calcWorkspace.buildReady')
    return
  }
  if (response.data.buildStatus === 'failed') {
    isWaitingForBuild.value = false
    buildMessage.value = `${t('calcWorkspace.buildFailed')}: ${JSON.stringify(response.data.diagnostics || {})}`
    return
  }
  scheduleBuildPoll()
}
/** Continue the original interactive process with current field values. */
async function onContinue(): Promise<void> {
  if (!execution.value) return
  isExecuting.value = true
  try { const response = await continueExecution(execution.value.executionId, collectDefaults(), execution.value.htmlPath); execution.value = adaptExecutionFields(response.data) } finally { isExecuting.value = false }
}
/** Terminate the active execution idempotently. */
async function onTerminate(): Promise<void> { if (execution.value) { await terminateExecution(execution.value.executionId); execution.value.status = 'cancelled' } }
/** Open instance metadata for the completed execution. */
async function onOpenSaveInstanceDialog(): Promise<void> {
  if (!execution.value) return
  await openSaveInstanceDialog(execution.value.executionId, props.report?.name || t('calcWorkspace.instanceName'))
}
onUnmounted(() => { if (buildPollTimer) clearTimeout(buildPollTimer) })
</script>

<style scoped>
.execution-pane {
  height: 100%;
  min-height: 620px;
  background: #fff;
}

.execution-toolbar {
  min-height: 48px;
}

.execution-toolbar__source {
  width: 180px;
}

.execution-toolbar__version {
  width: 150px;
}

.execution-body {
  min-height: 0;
}

.execution-input {
  width: 330px;
  min-width: 330px;
}

.execution-provenance {
  min-height: 54px;
}
</style>
