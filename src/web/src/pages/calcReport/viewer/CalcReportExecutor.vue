<template>
  <div :class="wrapperClass || undefined">
    <q-splitter v-model="splitterModel" :limits="splitterLimits" class="full-height col no-wrap"
      :horizontal="isVerticalLayout">
      <template #before>
        <CalcInputForm ref="calcInputFormRef" v-model="fullHtmlUrl" v-model:hashUis="hashUis"
          :report-oid="reportOid" :file-path="filePath" :is-silent="isSilent" :instance-info="instanceInfo"
          :disable-header="disableHeader" :disable-buttons="disableButtons" @html-content-patch="onHtmlContentPatch">
        </CalcInputForm>
      </template>

      <template #after>
        <div class="full-height overflow-hidden">
          <div v-if="!iframeSrc" class="full-height text-grey-6 column justify-center">
            <div class="text-center">
              <q-icon name="article" size="xl" />
              <div>{{ tCalcReportPageViewer('pleaseStartExecution') }}</div>
            </div>
          </div>
          <iframe v-else ref="reportIframeRef" :src="iframeSrc" class="full-height full-width" frameborder="0"></iframe>
        </div>
      </template>
    </q-splitter>
  </div>
</template>

<script lang="ts" setup>
import { tCalcReportPageViewer } from 'src/i18n/helpers'
import CalcInputForm from './components/CalcInputForm.vue'
import type { ICalcReportInstanceInfo } from 'src/api/calcReportInstance'
import type { PropType } from 'vue'

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

  instanceInfo: {
    type: Object as PropType<ICalcReportInstanceInfo | null>,
    required: false,
    default: null
  },

  // 是否使用竖向排版
  isVerticalLayout: {
    type: Boolean,
    required: false,
    default: false
  },

  // 是否跟随输入 UI 自动折叠参数区
  autoCollapseInputUis: {
    type: Boolean,
    required: false,
    default: false
  },

  // 是否禁用表单头部显示
  disableHeader: {
    type: Boolean,
    required: false,
    default: false
  },

  // 是否禁用表单底部按钮
  disableButtons: {
    type: Boolean,
    required: false,
    default: false
  },

  // 外层样式类
  wrapperClass: {
    type: String,
    required: false,
    default: 'full-height column card-like'
  }
})

const fullHtmlUrl = ref('')
const iframeSrc = ref('')
const hashUis = ref(false)
const splitterModel = ref(props.autoCollapseInputUis ? 0 : 30)
const splitterLimits: Ref<[number, number] | undefined> = ref(props.autoCollapseInputUis ? [0, 0] : undefined)
const lastSplitterValue = ref(30)
const calcInputFormRef: Ref<typeof CalcInputForm | null> = ref(null)
const reportIframeRef = ref<HTMLIFrameElement | null>(null)
const patchedFullHtmlUrl = ref('')

watch(hashUis, (newValue) => {
  if (!props.autoCollapseInputUis) return

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

watch(fullHtmlUrl, (newValue) => {
  if (!newValue) {
    iframeSrc.value = ''
    patchedFullHtmlUrl.value = ''
    return
  }

  // 已通过 postMessage 更新的结果不再切换 iframe src，避免预览区闪白
  if (newValue === patchedFullHtmlUrl.value) return

  iframeSrc.value = newValue
})

// 接收正文补丁时复用 iframe，只在无法发送消息时退回完整地址刷新
function onHtmlContentPatch(payload: { contentHtml: string; fullHtmlUrl: string }) {
  const iframeWindow = reportIframeRef.value?.contentWindow
  if (!iframeWindow) {
    iframeSrc.value = payload.fullHtmlUrl
    return
  }

  patchedFullHtmlUrl.value = payload.fullHtmlUrl
  iframeWindow.postMessage({
    type: 'uzoncalc:update-content',
    contentHtml: payload.contentHtml
  }, '*')
}

// 向外暴露执行入口，供编辑器工具栏触发预览执行
function onStartExecution() {
  return calcInputFormRef.value?.onStartExecution()
}

defineExpose({
  onStartExecution
})
</script>

<style lang="scss" scoped></style>
