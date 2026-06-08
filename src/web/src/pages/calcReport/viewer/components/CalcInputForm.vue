<script lang="ts" setup>
import { t, tCalcReportPageViewer } from 'src/i18n/helpers'
import AsyncTooltip from 'src/components/asyncTooltip/AsyncTooltip.vue'
import LowCodeForm from 'src/components/lowCode/LowCodeForm.vue'
import { getCalcReport } from 'src/api/calcReport'
import {
  saveCalcReportInstance,
  updateCalcReportInstanceResult,
  type ICalcReportInstanceInfo
} from 'src/api/calcReportInstance'
import {
  getCalcReportInstanceCategories,
  getOrCreateDefaultInstanceCategory
} from 'src/api/calcReportInstanceCategory'
import { useUserInfoStore } from 'src/stores/user'
import { sha256 } from 'src/utils/encrypt'
import { notifyError, notifySuccess } from 'src/utils/dialog'
import { useRouter } from 'vue-router'
import {
  HtmlUpdateType,
  type ExecutionResult,
  type ICalcWindow
} from 'src/api/calcExecution'
import type { ICategoryInfo } from 'src/components/categoryList/types'
import type { ILowCodeField, IPopupDialogParams } from 'src/components/lowCode/types'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import type { PropType } from 'vue'

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
  },

  instanceInfo: {
    type: Object as PropType<ICalcReportInstanceInfo | null>,
    required: false,
    default: null
  }
})

const emit = defineEmits<{
  reportResultChanged: [payload: { updateType: HtmlUpdateType; contentHtml?: string | null; fullHtmlUrl: string }]
}>()

// #region 报告信息
const { isSilent } = toRefs(props)
const currentReportOid = ref<string>(props.reportOid || '')
watch(() => props.reportOid, () => {
  currentReportOid.value = props.reportOid || ''
})

const currentFilePath = ref(props.filePath)

const calcReportNameRef = ref('')
const currentInstance = ref<ICalcReportInstanceInfo | null>(props.instanceInfo)

onMounted(async () => {
  if (currentInstance.value) return
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
  htmlPath: '',
  updateType: HtmlUpdateType.Full,
  windows: [],
  isCompleted: false
})

function applyInstanceInfo(instanceInfo: ICalcReportInstanceInfo) {
  currentInstance.value = instanceInfo
  currentReportOid.value = instanceInfo.reportOid
  calcReportNameRef.value = instanceInfo.name
  executeResult.value = {
    executionId: '',
    html: '',
    htmlPath: instanceInfo.resultPath || '',
    updateType: HtmlUpdateType.Full,
    windows: [],
    isCompleted: true
  }
}

watch(() => props.instanceInfo, (instanceInfo) => {
  if (!instanceInfo) return
  applyInstanceInfo(instanceInfo)
}, { immediate: true })

import { useConfig } from 'src/config/index'
const config = useConfig()
const userInfoStore = useUserInfoStore()
const { username: userId } = storeToRefs(userInfoStore)
const lastReportedResultKey = ref('')

function buildFullHtmlUrl(htmlPath: string) {
  if (!htmlPath) return ''

  const htmlUrl = new URL(htmlPath, `${config.baseUrl}/`)
  const scrollTargetId = currentInstance.value?.oid || currentReportOid.value || (currentFilePath.value ? sha256(currentFilePath.value) : '')
  const scrollKey = [userId.value, scrollTargetId].filter(Boolean).join('_')
  if (scrollKey) htmlUrl.searchParams.set('scrollKey', scrollKey)

  return htmlUrl.toString()
}

// 更新结果 HTML 地址
watch([() => executeResult.value.htmlPath, currentReportOid, currentFilePath, userId, currentInstance], () => {
  const nextFullHtmlUrl = buildFullHtmlUrl(executeResult.value.htmlPath)
  fullHtmlUrl.value = nextFullHtmlUrl

  if (!executeResult.value.htmlPath) {
    if (lastReportedResultKey.value === 'empty-result') return

    // 空结果也通过事件通知父组件清理 iframe
    lastReportedResultKey.value = 'empty-result'
    emit('reportResultChanged', {
      updateType: HtmlUpdateType.Full,
      fullHtmlUrl: ''
    })
    return
  }

  const contentPatch = executeResult.value.htmlContentPatch
  const resultKey = [
    executeResult.value.htmlPath,
    executeResult.value.updateType,
    contentPatch || '',
    nextFullHtmlUrl
  ].join('|')
  if (lastReportedResultKey.value === resultKey) return

  // iframe 更新统一由结果变更事件驱动，v-model 只保留最新地址
  lastReportedResultKey.value = resultKey
  emit('reportResultChanged', {
    updateType: executeResult.value.updateType,
    contentHtml: contentPatch,
    fullHtmlUrl: nextFullHtmlUrl
  })
}, { immediate: true })
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
  getInputValues,
  onStartExecution,
  onResumeExecution,
  onRestartExecution } = useCalcExecutor(currentReportOid, currentFilePath, isSilent, executeResult)

const router = useRouter()
const hasUnsavedCompletedResult = ref(false)
const canSaveInstance = computed(() => {
  return hasUnsavedCompletedResult.value && executeResult.value.isCompleted && !!executeResult.value.htmlPath && !!currentReportOid.value
})

function getCurrentDefaults() {
  const values = getInputValues()
  if (Object.keys(values).length > 0) return values
  return currentInstance.value?.defaults || {}
}

function markSaveableIfCompleted(result?: ExecutionResult) {
  const targetResult = result || executeResult.value
  if (targetResult.isCompleted && targetResult.htmlPath) {
    hasUnsavedCompletedResult.value = true
  }
}

async function onStartExecutionAndSaveable() {
  const defaults = Object.keys(getInputValues()).length > 0
    ? getInputValues()
    : currentInstance.value?.defaults
  const result = await onStartExecution(defaults)
  markSaveableIfCompleted(result)
}

async function onResumeExecutionAndSaveable() {
  const result = await onResumeExecution()
  markSaveableIfCompleted(result)
}

async function onRestartExecutionAndSaveable() {
  const result = await onRestartExecution()
  markSaveableIfCompleted(result)
}

async function getInstanceCategories() {
  const { data } = await getCalcReportInstanceCategories()
  if (data && data.length > 0) return data

  const defaultCategory = await getOrCreateDefaultInstanceCategory(
    t('calcReportInstancePage.defaultCategoryName')
  )
  return defaultCategory.data ? [defaultCategory.data] : []
}

function buildSaveInstanceFields(categories: ICategoryInfo[]): ILowCodeField[] {
  return [
    {
      name: 'name',
      label: t('calcReportInstancePage.list.instanceName'),
      value: currentInstance.value?.name || calcReportNameRef.value,
      type: LowCodeFieldType.text,
      required: true
    },
    {
      name: 'categoryId',
      label: tCalcReportPageViewer('instanceCategory'),
      value: currentInstance.value?.categoryId || categories[0]?.id,
      type: LowCodeFieldType.selectOne,
      options: categories,
      optionLabel: 'name',
      optionValue: 'id',
      emitValue: true,
      mapOptions: true,
      required: true
    },
    {
      name: 'description',
      label: t('calcReportInstancePage.list.instanceDescription'),
      value: currentInstance.value?.description || '',
      type: LowCodeFieldType.textarea
    }
  ]
}

async function onSaveCalcReportInstance() {
  if (!executeResult.value.htmlPath || !executeResult.value.isCompleted) {
    notifyError(tCalcReportPageViewer('resultNotReady'))
    return
  }

  const categories = await getInstanceCategories()
  if (categories.length === 0) return

  let name = currentInstance.value?.name || calcReportNameRef.value
  let description = currentInstance.value?.description || ''
  let categoryId = currentInstance.value?.categoryId || categories[0]!.id

  if (!currentInstance.value) {
    const popupParams: IPopupDialogParams = {
      title: tCalcReportPageViewer('saveInstance'),
      fields: buildSaveInstanceFields(categories),
      oneColumn: true
    }
    const result = await showDialog<{ name: string; description: string; categoryId: number }>(popupParams)
    if (!result.ok) return

    name = result.data.name
    description = result.data.description
    categoryId = result.data.categoryId
  }

  const payload = {
    name,
    description,
    categoryId: categoryId as number,
    reportOid: currentReportOid.value,
    defaults: getCurrentDefaults(),
    resultPath: executeResult.value.htmlPath
  }

  const response = currentInstance.value
    ? await updateCalcReportInstanceResult(currentInstance.value.oid, payload)
    : await saveCalcReportInstance(payload)

  currentInstance.value = response.data
  calcReportNameRef.value = response.data.name
  executeResult.value.htmlPath = response.data.resultPath || executeResult.value.htmlPath
  hasUnsavedCompletedResult.value = false

  await router.replace({
    name: 'calcReportViewer',
    query: {
      instanceOid: response.data.oid,
      tagName: response.data.name,
      __cacheKey: response.data.oid
    }
  })

  notifySuccess(tCalcReportPageViewer('saveInstanceSuccess'))
}
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
    await onStartExecutionAndSaveable()
})
// #endregion

// #region 暴露调用的方法
defineExpose({
  onStartExecution: onStartExecutionAndSaveable,
  onResumeExecution: onResumeExecutionAndSaveable,
  onRestartExecution: onRestartExecutionAndSaveable
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

      <q-input v-if="isDev && !reportOid" v-model="devFilePath" dense outlined clearable style="zoom: 0.8;"
        :placeholder="tCalcReportPageViewer('devLocalFilePathPlaceholder')" @keyup.enter="onApplyDevFilePath">
        <template #append>
          <q-btn dense flat round icon="check" color="primary" @click="onApplyDevFilePath">
            <AsyncTooltip :tooltip="tCalcReportPageViewer('applyDevLocalFilePath')" />
          </q-btn>
        </template>

        <AsyncTooltip :tooltip="devFilePath" />
      </q-input>

      <div>
        <div class="row items-center q-gutter-sm">
          <q-btn v-if="!reportOid" dense icon="file_open" flat color="primary" rounded :loading="isExecuting"
            @click="onOpenLocalFile">
            <AsyncTooltip :tooltip="tCalcReportPageViewer('openLocalFile')" />
          </q-btn>

          <q-btn v-if="canStartExecution" dense icon="play_arrow" color="secondary" size="sm" round
            @click="onStartExecutionAndSaveable" :loading="isExecuting">
            <AsyncTooltip :tooltip="tCalcReportPageViewer('executeCalculation')" />
          </q-btn>

          <q-btn v-if="canSaveInstance" dense icon="save" color="primary" size="sm" round
            @click="onSaveCalcReportInstance" :loading="isExecuting">
            <AsyncTooltip
              :tooltip="currentInstance ? tCalcReportPageViewer('saveCurrentInstance') : tCalcReportPageViewer('saveAsInstance')" />
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
          @click="onRestartExecutionAndSaveable" :loading="isExecuting">
          <AsyncTooltip :tooltip="tCalcReportPageViewer('restart')" />
        </q-btn>
        <q-btn v-if="canResumeExecution" dense icon="skip_next" color="primary" size="sm" round
          @click="onResumeExecutionAndSaveable" :loading="isExecuting">
          <AsyncTooltip :tooltip="tCalcReportPageViewer('resumeCalculation')" />
        </q-btn>
      </div>
    </q-list>
  </div>
</template>

<style lang="scss" scoped></style>
