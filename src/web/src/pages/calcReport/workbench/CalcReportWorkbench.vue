<template>
  <div v-if="$q.screen.lt.md" class="workbench-unsupported column items-center justify-center full-height text-grey-7">
    <q-icon name="desktop_windows" size="56px" />
    <div class="text-subtitle1 q-mt-md">{{ t('calcWorkspace.desktopRequired') }}</div>
  </div>
  <WorkspacePane v-else class="report-workbench" :report-oid="reportOid" :report="report" :is-new="isNew"
    @saved="onWorkspaceSaved" />
</template>

<script setup lang="ts">
/** Route page for creating and editing one calculation-report workspace. */
defineOptions({ name: 'CalcReportWorkbench' })
import WorkspacePane from './workspace/WorkspacePane.vue'
import type { CalcReport } from 'src/api/calc/types'
import { getCalcReport } from 'src/api/calc/reports'
import { objectId } from 'src/utils/objectId'
import { t } from 'src/i18n/helpers'

const route = useRoute()
const $q = useQuasar()
const newReportOid = ref(objectId())
const isNew = computed(() => route.name === 'CalcReportNew')
const reportOid = computed(() => isNew.value ? newReportOid.value : String(route.params.reportOid || ''))
const report = ref<CalcReport | null>(null)

/** Load report metadata required by the existing-workspace toolbar. */
async function loadReport(): Promise<void> { if (isNew.value || !reportOid.value) { report.value = null; return }; const response = await getCalcReport(reportOid.value); report.value = response.data }
watch([reportOid, isNew], loadReport, { immediate: true })
/** Refresh metadata after the first or a subsequent workspace save. */
async function onWorkspaceSaved(): Promise<void> { if (!isNew.value) await loadReport() }
</script>

<style scoped>
.report-workbench {
  min-height: 680px;
  height: 100%;
  overflow: hidden;
}

.workbench-unsupported {
  min-height: 520px;
  background: #fff;
}
</style>
