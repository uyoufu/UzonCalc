<template>
  <div v-if="$q.screen.lt.md" class="workbench-unsupported column items-center justify-center full-height text-grey-7">
    <q-icon name="desktop_windows" size="56px" />
    <div class="text-subtitle1 q-mt-md">{{ t('calcWorkspace.desktopRequired') }}</div>
  </div>
  <div v-else class="report-workbench column no-wrap full-height">
    <header class="workbench-header row items-center q-px-md">
      <q-btn flat round dense icon="arrow_back" @click="router.push('/calc-report/list')"><q-tooltip>{{
        t('calcWorkspace.backToReports') }}</q-tooltip></q-btn>
      <div class="q-ml-sm">
        <div class="text-subtitle1">{{ report?.name || t('calcWorkspace.newReport') }}</div>
        <div class="text-caption text-grey-7">{{ reportOid }}</div>
      </div>
      <q-space />
      <template v-if="report">
        <q-chip dense square :color="publishColor" text-color="white">{{
          t(`calcWorkspace.publishStates.${report.publishState}`) }}</q-chip>
        <q-chip dense square :color="buildColor" text-color="white">{{
          t(`calcWorkspace.buildStates.${report.buildStatus}`) }}</q-chip>
      </template>
    </header>
    <q-tabs v-if="!isNew" :model-value="activeTab" dense align="left" indicator-color="primary" class="workbench-tabs">
      <q-route-tab name="workspace" icon="code" :label="t('calcWorkspace.workspace')"
        :to="`/calc-report/${reportOid}/workspace`" />
      <q-route-tab name="run" icon="play_circle" :label="t('calcWorkspace.run')"
        :to="`/calc-report/${reportOid}/run`" />
      <q-route-tab name="versions" icon="history" :label="t('calcWorkspace.versionsAndShares')"
        :to="`/calc-report/${reportOid}/versions`" />
    </q-tabs>
    <q-separator />
    <section class="col workbench-content">
      <WorkspacePane v-if="activeTab === 'workspace'" :report-oid="reportOid" :report="report" :is-new="isNew"
        @saved="onWorkspaceSaved" />
      <ExecutionPane v-else-if="activeTab === 'run'" :report-oid="reportOid" :report="report" />
      <VersionPane v-else :report-oid="reportOid" :report="report" @changed="loadReport" @restored="loadReport" />
    </section>
  </div>
</template>

<script setup lang="ts">
/** Shared report-workbench shell for workspace, execution, and lifecycle tabs. */
defineOptions({ name: 'CalcReportWorkbench' })
import WorkspacePane from './workspace/WorkspacePane.vue'
import ExecutionPane from './execution/ExecutionPane.vue'
import VersionPane from './version/VersionPane.vue'
import type { CalcReport } from 'src/api/calc/types'
import { getCalcReport } from 'src/api/calc/reports'
import { objectId } from 'src/utils/objectId'
import { t } from 'src/i18n/helpers'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const newReportOid = ref(objectId())
const isNew = computed(() => route.name === 'CalcReportNew')
const reportOid = computed(() => isNew.value ? newReportOid.value : String(route.params.reportOid || ''))
const report = ref<CalcReport | null>(null)
const activeTab = computed<'workspace' | 'run' | 'versions'>(() => route.name === 'CalcReportRun' ? 'run' : route.name === 'CalcReportVersions' ? 'versions' : 'workspace')
const publishColor = computed(() => ({ published: 'positive', unpublished: 'grey-7', unpublished_changes: 'warning', workspace_version_mismatch: 'deep-orange' })[report.value?.publishState || 'unpublished'])
const buildColor = computed(() => ({ not_requested: 'grey-6', pending: 'blue-grey', building: 'info', ready: 'positive', failed: 'negative' })[report.value?.buildStatus || 'not_requested'])

/** Load report metadata for the shared workbench header. */
async function loadReport(): Promise<void> { if (isNew.value || !reportOid.value) { report.value = null; return }; const response = await getCalcReport(reportOid.value); report.value = response.data }
watch(reportOid, loadReport, { immediate: true })
/** Refresh metadata after the first or a subsequent workspace save. */
async function onWorkspaceSaved(): Promise<void> { await nextTick(); if (!isNew.value) await loadReport() }
</script>

<style scoped>
.report-workbench {
  min-height: 680px;
  background: #fff;
  overflow: hidden;
}

.workbench-header {
  min-height: 58px;
}

.workbench-tabs {
  min-height: 38px;
}

.workbench-content {
  min-height: 0;
  overflow: hidden;
}

.workbench-unsupported {
  min-height: 520px;
  background: #fff;
}
</style>
