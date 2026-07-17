<template>
  <ExecutionPane class="calc-report-run" :report-oid="reportOid" :initial-source="initialSource" show-back-button />
</template>

<script setup lang="ts">
/** Route wrapper for the standalone calculation-report execution pane. */
defineOptions({ name: 'CalcReportRun' })
import ExecutionPane from './components/ExecutionPane.vue'
import { ExecutionSourceType } from 'src/api/calc/types'

const route = useRoute()
const reportOid = computed(() => String(route.params.reportOid || ''))
const initialSource = computed(() => {
  const requestedSource = Array.isArray(route.query.source) ? route.query.source[0] : route.query.source
  if (requestedSource === ExecutionSourceType.Latest) return ExecutionSourceType.Latest
  if (requestedSource === ExecutionSourceType.Version) return ExecutionSourceType.Version
  return ExecutionSourceType.Workspace
})
</script>

<style scoped>
.calc-report-run {
  min-height: 620px;
}
</style>
