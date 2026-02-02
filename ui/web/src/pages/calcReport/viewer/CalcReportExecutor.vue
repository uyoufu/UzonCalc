<template>
  <div class="full-height column card-like">
    <q-splitter v-model="splitterModel" class="full-height col no-wrap">
      <template #before>
        <q-list bordered class="full-height hover-scroll" separator>
          <q-item>
            <q-item-section>{{ tCalcReportPageViewer('name', { name: calcReportFileName }) }}</q-item-section>
            <q-item-section side>
              <q-btn dense icon="file_open" flat color="primary" rounded :loading="isExecuting">
                <AsyncTooltip :tooltip="tCalcReportPageViewer('openLocalFile')" />
              </q-btn>
            </q-item-section>
          </q-item>

          <q-separator />

          <q-expansion-item dense v-for="ui in inputUIs" :key="ui.title" :label="ui.title" default-opened
            header-class="text-primary">
            <LowCodeForm :fields="ui.fields" :disable-default-btns="['ok', 'cancel']" sync-value />
          </q-expansion-item>

          <div class="row justify-end q-mr-md q-gutter-sm q-mt-xs">
            <q-btn v-if="canRestartExecution" dense icon="replay" color="negative" round @click="onRestartExecution"
              :loading="isExecuting">
              <AsyncTooltip :tooltip="tCalcReportPageViewer('restart')" />
            </q-btn>
            <q-btn v-if="canStartExecution" dense icon="play_arrow" color="secondary" round @click="onStartExecution()"
              :loading="isExecuting">
              <AsyncTooltip :tooltip="tCalcReportPageViewer('executeCalculation')" />
            </q-btn>
            <q-btn v-if="canResumeExecution" dense icon="skip_next" color="primary" round @click="onResumeExecution"
              :loading="isExecuting">
              <AsyncTooltip :tooltip="tCalcReportPageViewer('resumeCalculation')" />
            </q-btn>
          </div>
        </q-list>
      </template>

      <template #after>
        <div class="full-height iframe-container hover-scroll">
          <div v-if="!fullHtmlUrl" class="full-height text-grey-6 column justify-center">
            <div class="text-center">
              <q-icon name="article" size="xl" />
              <div class="q-mt-md">{{ tCalcReportPageViewer('waitingForResult') }}</div>
            </div>
          </div>
          <template v-else>
            <iframe :src="fullHtmlUrl" class="full-height full-width q-pt-md" frameborder="0"></iframe>
          </template>
        </div>
      </template>
    </q-splitter>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { tCalcReportPageViewer } from 'src/i18n/helpers'
import AsyncTooltip from 'src/components/asyncTooltip/AsyncTooltip.vue'
import LowCodeForm from 'src/components/lowCode/LowCodeForm.vue'
import { getCalcReport } from 'src/api/calcReport'
import {
  type ExecutionResult,
  type ICalcWindow
} from 'src/api/calcExecution'

const props = defineProps({
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

const splitterModel = ref(30)

// #region 报告信息
const { reportOid, filePath, isSilent } = toRefs(props)

const calcReportFileName = ref('')

onMounted(async () => {
  // 如果存在 reportOid, 则获取参数
  if (reportOid.value) {
    const { data: reportInfo } = await getCalcReport(reportOid.value)
    calcReportFileName.value = reportInfo.name
  }
})
// #endregion

// #region 执行结果状态
const executeResult = ref<ExecutionResult>({
  executionId: '',
  html: '',
  windows: [],
  isCompleted: false
})

import { useConfig } from 'src/config/index'
const config = useConfig()
// 结果 HTML 地址
const fullHtmlUrl = computed(() => {
  if (!executeResult.value.html) return ''
  return config.baseUrl + '/' + executeResult.value.html
})
// 最终显示的 UI
const inputUIs = computed<ICalcWindow[]>(() => {
  return executeResult.value.windows || []
})
// #endregion

// #region 计算逻辑
import { useCalcExecutor } from './compositions/useCalcExecutor'
const {
  isExecuting,
  canStartExecution,
  canResumeExecution,
  canRestartExecution,
  onStartExecution,
  onResumeExecution,
  onRestartExecution } = useCalcExecutor(reportOid, filePath, isSilent, executeResult)
// #endregion
</script>

<style lang="scss" scoped></style>
