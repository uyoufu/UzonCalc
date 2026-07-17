<template>
  <div class="execution-pane column no-wrap">
    <div class="execution-toolbar row items-center q-gutter-sm q-px-sm">
      <CommonBtn v-if="showBackButton" flat dense icon="arrow_back" :tooltip="t('calcWorkspace.backToReports')"
        @click="onBackToReports" />
      <q-select v-if="!workspaceOnly" v-model="sourceType" dense options-dense outlined emit-value map-options
        :options="sourceOptions" :label="t('calcWorkspace.executionSource')" class="execution-toolbar__source" />
      <q-select v-if="!workspaceOnly && sourceType === ExecutionSourceType.Version" v-model="versionName" dense
        options-dense outlined emit-value map-options :options="versionOptions" :label="t('calcWorkspace.version')"
        class="execution-toolbar__version" />
      <div v-if="workspaceOnly" class="text-caption text-grey-7 row items-center q-gutter-xs">
        <q-icon name="source" />
        <span>{{ t('calcWorkspace.sourceWorkspace') }}</span>
      </div>
      <q-toggle v-model="isSilent" :label="t('calcWorkspace.silentRun')" />
      <CommonBtn v-if="!execution || execution.isCompleted || isExecutionOutdated" icon="play_arrow"
        :label="t('calcWorkspace.startRun')" :loading="isExecuting" @click="onStart" />
      <CommonBtn v-else icon="skip_next" :label="t('calcWorkspace.continueRun')" :loading="isExecuting"
        @click="onContinue" />
      <CommonBtn v-if="execution && !execution.isCompleted" flat dense icon="stop" color="negative"
        :tooltip="t('calcWorkspace.terminate')" @click="onTerminate" />
      <q-space />
      <CommonBtn v-if="execution?.isCompleted" icon="save_as" color="grey-8"
        :label="t('calcWorkspace.saveInstance')" @click="onOpenSaveInstanceDialog" />
    </div>
    <q-separator />
    <q-banner v-if="isExecutionOutdated" dense class="bg-orange-1 text-orange-10">
      <template #avatar><q-icon name="history_toggle_off" color="warning" /></template>
      {{ t('calcWorkspace.executionOutdated') }}
    </q-banner>
    <q-banner v-if="buildMessage" dense class="bg-blue-grey-1 text-blue-grey-10">
      <template #avatar><q-spinner v-if="isWaitingForBuild" color="primary" /><q-icon v-else name="error"
          color="negative" /></template>
      {{ buildMessage }}
    </q-banner>
    <div class="row no-wrap col execution-body">
      <section class="execution-input column no-wrap">
        <div v-if="execution" class="execution-provenance q-pa-sm text-caption">
          <div>{{ execution.sourceType }}<span v-if="execution.resolvedVersion"> · {{ execution.resolvedVersion }}</span></div>
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
      <q-separator vertical class="execution-divider" />
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
import { useSaveInstanceDialog } from '../compositions/useSaveInstanceDialog'
import {
  BuildStatus,
  CalcErrorCode,
  ExecutionSourceType,
  ExecutionStatus,
  type CalcExecution,
  type CalcReport,
  type CalcReportVersion
} from 'src/api/calc/types'
import { continueExecution, startExecution, terminateExecution, type ExecutionDefaults } from 'src/api/calc/executions'
import { createInstance } from 'src/api/calc/instances'
import { listVersions } from 'src/api/calc/versions'
import { adaptExecutionFields } from '../utils/adaptExecutionFields'
import { isWorkspaceExecutionOutdated } from '../utils/executionSourceState'
import { getWorkspaceBuild } from 'src/api/calc/workspace'
import { getCalcReport } from 'src/api/calc/reports'
import { getApiFailure } from '../../calcReport/shared/apiFailure'
import { confirmOperation, notifyError, notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'

const props = withDefaults(defineProps<{
  reportOid: string
  workspaceOnly?: boolean
  initialSource?: ExecutionSourceType
  refreshToken?: number
  showBackButton?: boolean
}>(), {
  workspaceOnly: false,
  initialSource: ExecutionSourceType.Workspace,
  refreshToken: 0,
  showBackButton: false
})

const router = useRouter()
const report = ref<CalcReport | null>(null)
const versions = ref<CalcReportVersion[]>([])
const sourceType = ref<ExecutionSourceType>(props.workspaceOnly ? ExecutionSourceType.Workspace : props.initialSource)
const versionName = ref<string | null>(null)
const isSilent = ref(true)
const isExecuting = ref(false)
const isWaitingForBuild = ref(false)
const buildMessage = ref('')
let buildPollTimer: ReturnType<typeof setTimeout> | null = null
let initializedReportOid = ''
const execution = ref<CalcExecution | null>(null)
const { openSaveInstanceDialog } = useSaveInstanceDialog()
const sourceOptions = computed(() => [
  { label: t('calcWorkspace.sourceWorkspace'), value: ExecutionSourceType.Workspace },
  { label: t('calcWorkspace.sourceLatest'), value: ExecutionSourceType.Latest, disable: !report.value?.latestVersionName },
  { label: t('calcWorkspace.sourceVersion'), value: ExecutionSourceType.Version, disable: versions.value.length === 0 }
])
const versionOptions = computed(() => versions.value.map((version) => ({ label: version.versionName, value: version.versionName })))
const isExecutionOutdated = computed(() => isWorkspaceExecutionOutdated(execution.value, report.value))

/** Load report context while preserving an existing execution result. */
async function refreshExecutionContext(): Promise<void> {
  try {
    const [reportResponse, versionResponse] = await Promise.all([
      getCalcReport(props.reportOid),
      listVersions(props.reportOid)
    ])
    report.value = reportResponse.data
    versions.value = versionResponse.data || []
    versionName.value = versions.value.find((version) => version.isLatest)?.versionName || versions.value[0]?.versionName || null
    if (props.workspaceOnly) {
      sourceType.value = ExecutionSourceType.Workspace
    } else if (initializedReportOid !== props.reportOid) {
      sourceType.value = resolveInitialSource(props.initialSource)
    } else if (sourceType.value === ExecutionSourceType.Latest && !report.value.latestVersionName) {
      sourceType.value = ExecutionSourceType.Workspace
    } else if (sourceType.value === ExecutionSourceType.Version && versions.value.length === 0) {
      sourceType.value = ExecutionSourceType.Workspace
    }
    initializedReportOid = props.reportOid
  } catch (error) {
    notifyError(getApiFailure(error).message)
  }
}

/** Resolve a valid initial source from current report capabilities. */
function resolveInitialSource(requestedSource: ExecutionSourceType): ExecutionSourceType {
  if (requestedSource === ExecutionSourceType.Latest && report.value?.latestVersionName) return requestedSource
  if (requestedSource === ExecutionSourceType.Version && versions.value.length > 0) return requestedSource
  if (requestedSource === ExecutionSourceType.Workspace) return requestedSource
  return report.value?.latestVersionName ? ExecutionSourceType.Latest : ExecutionSourceType.Workspace
}

watch(() => [props.reportOid, props.refreshToken] as const, refreshExecutionContext, { immediate: true })

/** Return to the calculation-report list. */
async function onBackToReports(): Promise<void> {
  await router.push('/calc-report/list')
}

/** Collect current values from all returned input windows. */
function collectDefaults(): ExecutionDefaults {
  const defaults: ExecutionDefaults = {}
  execution.value?.windows.forEach((windowInfo) => {
    defaults[windowInfo.title] = Object.fromEntries(windowInfo.fields.map((field) => [field.name, field.value]))
  })
  return defaults
}

/** Start a new managed execution from the selected immutable source. */
async function onStart(): Promise<void> {
  isExecuting.value = true
  try {
    if (isExecutionOutdated.value && execution.value && !execution.value.isCompleted) {
      await terminateExecution(execution.value.executionId)
    }
    const source = sourceType.value === ExecutionSourceType.Version
      ? { type: sourceType.value, versionName: versionName.value || undefined }
      : { type: sourceType.value }
    const response = await startExecution({
      reportOid: props.reportOid,
      source,
      isSilent: isSilent.value,
      defaults: execution.value ? collectDefaults() : {},
      lastHtmlPath: execution.value?.htmlPath
    })
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
  } finally {
    isExecuting.value = false
  }
}

/** Schedule one build-state poll without overlapping requests. */
function scheduleBuildPoll(): void {
  if (buildPollTimer) clearTimeout(buildPollTimer)
  buildPollTimer = setTimeout(() => { void pollWorkspaceBuild() }, 1500)
}

/** Poll the configured runtime build until it is ready or failed. */
async function pollWorkspaceBuild(): Promise<void> {
  const response = await getWorkspaceBuild(props.reportOid)
  if (response.data.buildStatus === BuildStatus.Ready) {
    isWaitingForBuild.value = false
    buildMessage.value = t('calcWorkspace.buildReady')
    return
  }
  if (response.data.buildStatus === BuildStatus.Failed) {
    isWaitingForBuild.value = false
    buildMessage.value = `${t('calcWorkspace.buildFailed')}: ${JSON.stringify(response.data.diagnostics || {})}`
    return
  }
  scheduleBuildPoll()
}

/** Continue the original interactive process with current field values. */
async function onContinue(): Promise<void> {
  if (!execution.value || isExecutionOutdated.value) return
  isExecuting.value = true
  try {
    const response = await continueExecution(execution.value.executionId, collectDefaults(), execution.value.htmlPath)
    execution.value = adaptExecutionFields(response.data)
  } finally {
    isExecuting.value = false
  }
}

/** Terminate the active execution idempotently. */
async function onTerminate(): Promise<void> {
  if (!execution.value) return
  await terminateExecution(execution.value.executionId)
  execution.value.status = ExecutionStatus.Cancelled
}

/** Open instance metadata for the completed execution. */
async function onOpenSaveInstanceDialog(): Promise<void> {
  if (!execution.value) return
  const input = await openSaveInstanceDialog(report.value?.name || t('calcWorkspace.instanceName'))
  if (!input) return
  await createInstance({ executionId: execution.value.executionId, ...input })
  notifySuccess(t('calcWorkspace.instanceSaved'))
}

/** Confirm termination before a tab closes an unfinished execution. */
async function requestClose(): Promise<boolean> {
  if (!execution.value || execution.value.isCompleted) return true
  const confirmed = await confirmOperation(
    t('calcWorkspace.terminateRun'),
    t('calcWorkspace.closeRunningTabConfirm')
  )
  if (!confirmed) return false
  await onTerminate()
  return true
}

defineExpose({ requestClose })
onUnmounted(() => { if (buildPollTimer) clearTimeout(buildPollTimer) })
</script>

<style scoped>
.execution-pane {
  height: 100%;
  min-height: 0;
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

@media (max-width: 900px) {
  .execution-pane {
    overflow: auto;
  }

  .execution-toolbar {
    flex-wrap: wrap;
  }

  .execution-toolbar__source,
  .execution-toolbar__version {
    width: min(100%, 240px);
  }

  .execution-body {
    flex: none;
    flex-direction: column;
  }

  .execution-input {
    width: 100%;
    min-width: 0;
    min-height: 360px;
  }

  .execution-divider {
    display: none;
  }

  .execution-body>section:last-child {
    min-height: 520px;
  }
}
</style>
