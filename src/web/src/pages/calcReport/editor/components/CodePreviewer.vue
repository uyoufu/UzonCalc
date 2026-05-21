<script lang="ts" setup>
import { tCalcReportPageViewer } from 'src/i18n/helpers'
import CalcInputForm from 'src/pages/calcReport/viewer/components/CalcInputForm.vue'

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

const splitterModel = ref(0)
const fullHtmlUrl = ref('')

const calcInputFormRef: Ref<typeof CalcInputForm | null> = ref(null)

import { startExecutingSignalKey } from '../keys'
const startExecutingSignal = inject(startExecutingSignalKey, ref(0))
watch(startExecutingSignal, () => {
  // 重新执行
  calcInputFormRef.value?.onStartExecution()
})

// #region 自动隐藏 UI 区
const hashUis = ref(false)
const splitterLimits: Ref<[number, number]> = ref([0, 0])
const lastSplitterValue = ref(30)
watch(hashUis, (newValue) => {
  if (newValue) {
    splitterModel.value = lastSplitterValue.value
    splitterLimits.value = [20, 80]
  }
  else {
    lastSplitterValue.value = splitterModel.value
    splitterModel.value = 0
    splitterLimits.value = [0, 0]
  }
})
// #endregion
</script>

<template>
  <q-splitter v-model="splitterModel" :limits="splitterLimits" class="full-height col no-wrap" horizontal>
    <template #before>
      <CalcInputForm ref="calcInputFormRef" v-model="fullHtmlUrl" v-model:hashUis="hashUis" :report-oid="reportOid"
        :file-path="filePath" :is-silent="isSilent" disable-header disable-buttons />
    </template>

    <template #after>
      <div class="full-height overflow-hidden">
        <div v-if="!fullHtmlUrl" class="full-height text-grey-6 column justify-center">
          <div class="text-center">
            <q-icon name="article" size="xl" />
            <div class="q-mt-md">{{ tCalcReportPageViewer('pleaseStartExecution') }}</div>
          </div>
        </div>
        <template v-else>
          <iframe :src="fullHtmlUrl" class="full-height full-width" frameborder="0"></iframe>
        </template>
      </div>
    </template>
  </q-splitter>
</template>

<style lang="scss" scoped></style>
