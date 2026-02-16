<script lang="ts" setup>
import AsyncTooltip from 'src/components/asyncTooltip/AsyncTooltip.vue'

const calcCategoryOid = defineModel('calcCategoryOid', { type: String, default: '' })
const calcReportOid = defineModel('calcReportOid', { type: String, default: '' })

import type { ICalcEditorOptions } from './types'
const props = defineProps({
  // 保存时是否另存为，默认为 false, 为 true 时会在保存时弹出另存为对话框
  // 且保存后的值不会更新到当前编辑器中
  editorOptions: {
    type: Object as () => ICalcEditorOptions,
    default: () => ({})
  }
})
const { editorOptions } = toRefs(props)

// #region 注入透传逻辑
import { startExecutingSignalKey } from './keys'
// 执行触发信号，每次触发会增加这个数字，监听这个数字的组件可以在这个数字变化时执行对应逻辑
const startExecutingSignal = ref(0)
const isExecuting = ref(false)
provide(startExecutingSignalKey, startExecutingSignal)
import { isCalcReportExecutingKey } from '../viewer/keys'
provide(isCalcReportExecutingKey, isExecuting)
// #endregion

// #region 代码编辑器
import { useMonacoEditor } from './compositions/useMonacoEditor'
const { monacoEditorElementRef, monacoEditorRef } = useMonacoEditor()

import { useReportSourceCode } from './compositions/useReportSourceCode'
useReportSourceCode(calcReportOid, monacoEditorRef)
// #endregion

// 保存
import { useCalcReportSaver } from './compositions/useCalcReportSaver'
const { calcReportName, onSaveCalcReport } =
  useCalcReportSaver(calcCategoryOid, calcReportOid, monacoEditorRef, editorOptions)

// 分类
import { useCategorySelector } from './compositions/useCategorySelector'
const { calcCategoryName, categoryOptions, fullCategoryOptions, onFilterReportCategory } = useCategorySelector(calcCategoryOid)

// 执行
import { useCalcRunner } from './compositions/useCalcRunner'
const { onStartExecuting } = useCalcRunner(startExecutingSignal, isExecuting, onSaveCalcReport)

// 命名格式检查
import { useCalcReportNameChecker } from './compositions/useCalcReportNameChecker'
useCalcReportNameChecker(calcReportName)

// #region 左右分割
const splitterModel = ref(50)
const defaultLimits: [number, number] = [30, 70]
const splitterLimits: Ref<[number, number]> = ref([30, 70])
// #endregion

// #region 功能菜单回调
import { useMenuCommands } from './compositions/useMenuCommands'
useMenuCommands(monacoEditorRef)
// #endregion

// #region 折叠
import { useCollapse } from './compositions/useCollapse'
const { isCollapsed, CollapseRight } = useCollapse(splitterModel, splitterLimits, defaultLimits)
// #endregion

// #region 预览
import CodePreviewer from './components/CodePreviewer.vue'
// #endregion

// #region MARK: 菜单栏
import CascadeMenu from 'src/components/cascadeMenu/CascadeMenu.vue'
import { useMenubar } from './menubar/useMenubar'
const { insertMenuItems } = useMenubar(monacoEditorRef)
// #endregion
</script>

<template>
  <div class="full-height full-width column no-wrap card-like">
    <q-bar class="bg-grey-4 text-accent rounded-borders">
      <div class="cursor-pointer non-selectable">
        <span class="text-primary">Insert</span>
        <CascadeMenu :items="insertMenuItems" />
      </div>

      <q-space />

      <div class="q-mr-xs text-primary">{{ calcCategoryName }} /
        <q-menu v-if="fullCategoryOptions.length > 1" anchor="top right" self="top right">
          <q-select dense outlined v-model="calcCategoryOid" :options="categoryOptions" emit-value map-options use-input
            options-dense @filter="onFilterReportCategory" />
        </q-menu>
      </div>

      <q-input standout="bg-secondary" class="text-white dense-input" v-model="calcReportName" placeholder="请输入报告名称"
        dense>
      </q-input>
      <q-btn dense flat icon="save" @click="onSaveCalcReport">
        <AsyncTooltip tooltip="保存" />
      </q-btn>
      <q-btn v-if="!editorOptions.disableRun" dense flat icon="play_arrow" color="primary" @click="onStartExecuting"
        :loading="isExecuting" />
      <q-space />
    </q-bar>

    <q-splitter v-model="splitterModel" :limits="splitterLimits" before-class="overflow-hidden q-pt-sm"
      after-class="overflow-hidden relative-position" class="col">
      <template v-slot:before>
        <div class="full-height full-width" ref="monacoEditorElementRef"></div>
        <CollapseRight v-model="isCollapsed" />
      </template>

      <template v-slot:after>
        <CodePreviewer :report-oid="calcReportOid" />
      </template>
    </q-splitter>
  </div>
</template>

<style lang="scss" scoped></style>
