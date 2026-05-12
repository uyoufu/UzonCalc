<script lang="ts" setup>

defineOptions({
  name: 'calcReportViewer'
})

import CalcReportExecutor from './CalcReportExecutor.vue'
import { useRoute } from 'vue-router'
import { getCalcReportInstance, type ICalcReportInstanceInfo } from 'src/api/calcReportInstance'

const route = useRoute()
const reportOidRef = ref<string>((route.query.reportOid as string) || '')
const instanceOidRef = ref<string>((route.query.instanceOid as string) || '')
const instanceInfoRef = ref<ICalcReportInstanceInfo | null>(null)
const noSilentRef = ref<boolean>(route.query.silent === 'false' || route.query.silent === '0')

onMounted(async () => {
  if (!instanceOidRef.value) return

  const { data } = await getCalcReportInstance(instanceOidRef.value)
  instanceInfoRef.value = data
  reportOidRef.value = data.reportOid
})
</script>

<template>
  <CalcReportExecutor v-if="!instanceOidRef || instanceInfoRef" :reportOid="reportOidRef" :is-silent="!noSilentRef"
    :instance-info="instanceInfoRef" />
</template>

<style lang="scss" scoped></style>
