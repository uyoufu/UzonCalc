<script lang="ts" setup>
import CalcReportExecutor from 'src/pages/calcReport/viewer/CalcReportExecutor.vue'

defineProps({
  // 报告的 oid
  reportOid: {
    type: String,
    required: false,
    default: null
  },

  // 指定的文件路径
  filePath: {
    type: String,
    required: false,
    default: ''
  },

  // 是否静默执行
  isSilent: {
    type: Boolean,
    required: false,
    default: true
  }
})

const calcReportExecutorRef: Ref<typeof CalcReportExecutor | null> = ref(null)

import { startExecutingSignalKey } from '../keys'
const startExecutingSignal = inject(startExecutingSignalKey, ref(0))
watch(startExecutingSignal, () => {
  // 重新执行当前预览报告
  calcReportExecutorRef.value?.onStartExecution()
})
</script>

<template>
  <CalcReportExecutor ref="calcReportExecutorRef" :report-oid="reportOid" :file-path="filePath"
    :is-silent="isSilent" is-vertical-layout auto-collapse-input-uis disable-header disable-buttons
    wrapper-class="full-height" />
</template>

<style lang="scss" scoped></style>
