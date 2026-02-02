<script lang="ts" setup>

defineOptions({
  name: 'calcReportViewer'
})

import CalcReportExecutor from './CalcReportExecutor.vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const reportOidRef = ref<string>(route.query.reportOid as string)
const noSilentRef = ref<boolean>(route.query.silent === 'false' || route.query.silent === '0')
</script>

<template>
  <CalcReportExecutor :reportOid="reportOidRef" :is-silent="!noSilentRef" />
</template>

<style lang="scss" scoped></style>
