<script lang="ts" setup>
import { tCalcReportPageViewer } from 'src/i18n/helpers'
import AsyncTooltip from 'src/components/asyncTooltip/AsyncTooltip.vue'
import LowCodeForm from 'src/components/lowCode/LowCodeForm.vue'
import { getCalcReport } from 'src/api/calcReport'
import {
  type ExecutionResult,
  type ICalcWindow
} from 'src/api/calcExecution'

// #region v-models
const fullHtmlUrl = defineModel({
  type: String,
  required: false,
  default: ''
})

const hashUis = defineModel("hashUis", {
  type: Boolean,
  required: false,
})
// #endregion

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
  },

  // 是否禁用头部显示
  disableHeader: {
    type: Boolean,
    required: false,
    default: false
  },

  // 禁用底部按钮
  disableButtons: {
    type: Boolean,
    required: false,
    default: false
  }
})

// #region 报告信息
const { isSilent } = toRefs(props)
const currentReportOid = ref<string>(props.reportOid)
watch(() => props.reportOid, () => {
  currentReportOid.value = props.reportOid
})

const currentFilePath = ref(props.filePath)

const calcReportNameRef = ref('')

onMounted(async () => {
  // 如果存在 currentReportOid, 则获取参数
  if (currentReportOid.value) {
    const { data: reportInfo } = await getCalcReport(currentReportOid.value)
    calcReportNameRef.value = reportInfo.name
  } else if (currentFilePath.value) {
    calcReportNameRef.value = currentFilePath.value.split(/[\\/]/).pop() || currentFilePath.value
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
// 更新结果 HTML 地址
watch(() => executeResult.value.html, () => {
  if (executeResult.value.html)
    fullHtmlUrl.value = config.baseUrl + '/' + executeResult.value.html
  else fullHtmlUrl.value = ''
})
// 最终显示的 UI
const inputUIs = computed<ICalcWindow[]>(() => {
  return executeResult.value.windows || []
})
// 更新 hashUis
watch(inputUIs, () => {
  hashUis.value = inputUIs.value.length > 0
})
// #endregion

// #region 计算逻辑
import { useCalcExecutor } from '../compositions/useCalcExecutor'
const {
  isExecuting,
  canStartExecution,
  canResumeExecution,
  canRestartExecution,
  onStartExecution,
  onResumeExecution,
  onRestartExecution } = useCalcExecutor(currentReportOid, currentFilePath, isSilent, executeResult)
// #endregion

// #region 本机文件
import { useLocalFileSelector } from '../compositions/useLocalFileSelector'
const { onOpenLocalFile } = useLocalFileSelector(currentReportOid, currentFilePath, calcReportNameRef, executeResult)

import { useDevLocalFilePathInput } from '../compositions/useDevLocalFilePathInput'
const {
  isDev,
  devFilePath,
  onApplyDevFilePath
} = useDevLocalFilePathInput(currentReportOid, currentFilePath, calcReportNameRef, executeResult)

// 文件变化后，立即执行
watch(currentFilePath, async () => {
  if (currentFilePath.value)
    await onStartExecution()
})
// #endregion

// #region 暴露调用的方法
defineExpose({
  onStartExecution,
  onResumeExecution,
  onRestartExecution
})
// #endregion
</script>

<template>
  <div class="full-height column no-wrap">
    <q-item v-if="!disableHeader">
      <div class="row items-center col">
        <span class="text-bold q-mr-sm">
          {{ tCalcReportPageViewer('name') }}:
        </span>
        <span>{{ calcReportNameRef }}</span>
      </div>

      <q-input v-if="isDev" v-model="devFilePath" dense outlined clearable style="transform: scale(0.8);"
        :placeholder="tCalcReportPageViewer('devLocalFilePathPlaceholder')" @keyup.enter="onApplyDevFilePath">
        <template #append>
          <q-btn dense flat round icon="check" color="primary" @click="onApplyDevFilePath">
            <AsyncTooltip :tooltip="tCalcReportPageViewer('applyDevLocalFilePath')" />
          </q-btn>
        </template>
      </q-input>

      <div>
        <div class="row items-center q-gutter-sm">
          <q-btn v-if="!reportOid" dense icon="file_open" flat color="primary" rounded :loading="isExecuting"
            @click="onOpenLocalFile">
            <AsyncTooltip :tooltip="tCalcReportPageViewer('openLocalFile')" />
          </q-btn>

          <q-btn v-if="canStartExecution" dense icon="play_arrow" color="secondary" size="sm" round
            @click="onStartExecution()" :loading="isExecuting">
            <AsyncTooltip :tooltip="tCalcReportPageViewer('executeCalculation')" />
          </q-btn>
        </div>
      </div>
    </q-item>

    <q-separator v-if="!disableHeader" />

    <q-list class="col hover-scroll" separator>
      <template v-if="hashUis">
        <q-expansion-item dense v-for="ui in inputUIs" :key="ui.title" :label="ui.title" default-opened
          header-class="text-primary">
          <LowCodeForm :fields="ui.fields" :disable-default-btns="['ok', 'cancel']" sync-value />
        </q-expansion-item>
      </template>

      <div v-if="inputUIs.length === 0" class="full-height text-grey-6 column items-center justify-center">
        <q-icon name="keyboard" size="xl" />
        <div>{{ tCalcReportPageViewer('uiDisplayArea') }}</div>
      </div>

      <div v-if="!disableButtons" class="row justify-end q-mr-md q-gutter-sm q-mt-xs">
        <q-btn v-if="canRestartExecution" dense icon="replay" color="negative" size="sm" round
          @click="onRestartExecution" :loading="isExecuting">
          <AsyncTooltip :tooltip="tCalcReportPageViewer('restart')" />
        </q-btn>
        <q-btn v-if="canResumeExecution" dense icon="skip_next" color="primary" size="sm" round
          @click="onResumeExecution" :loading="isExecuting">
          <AsyncTooltip :tooltip="tCalcReportPageViewer('resumeCalculation')" />
        </q-btn>
      </div>
    </q-list>
  </div>
</template>

<style lang="scss" scoped></style>
