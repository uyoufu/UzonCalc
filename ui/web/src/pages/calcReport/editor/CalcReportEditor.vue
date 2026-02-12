<script lang="ts" setup>
import AsyncTooltip from 'src/components/asyncTooltip/AsyncTooltip.vue'

// 报告 id
const calcReportOId = defineModel({
  type: String,
  default: '',
})

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
// #endregion

// 保存
import { useCalcReportSaver } from './compositions/useCalcReportSaver'
const { calcCategoryName, calcReportName, onSaveCalcReport } = useCalcReportSaver(calcReportOId, monacoEditorRef)

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
</script>

<template>
  <div class="full-height full-width column no-wrap card-like">
    <q-bar class="bg-grey-4 text-accent rounded-borders">
      <div class="cursor-pointer non-selectable">
        File
        <q-menu>
          <q-list dense style="min-width: 100px">
            <q-item clickable v-close-popup>
              <q-item-section>Open...</q-item-section>
            </q-item>
            <q-item clickable v-close-popup>
              <q-item-section>New</q-item-section>
            </q-item>
            <q-separator />
            <q-item clickable>
              <q-item-section>Preferences</q-item-section>
              <q-item-section side>
                <q-icon name="keyboard_arrow_right" />
              </q-item-section>

              <q-menu anchor="top end" self="top start">
                <q-list dense>
                  <q-item v-for="n in 3" :key="n" clickable>
                    <q-item-section>Submenu Label</q-item-section>
                    <q-item-section side>
                      <q-icon name="keyboard_arrow_right" />
                    </q-item-section>
                    <q-menu auto-close anchor="top end" self="top start">
                      <q-list dense>
                        <q-item v-for="n in 3" :key="n" clickable>
                          <q-item-section>3rd level Label</q-item-section>
                        </q-item>
                      </q-list>
                    </q-menu>
                  </q-item>
                </q-list>
              </q-menu>
            </q-item>
            <q-separator />
            <q-item clickable v-close-popup>
              <q-item-section>Quit</q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </div>
      <div class="cursor-pointer non-selectable">
        Edit
        <q-menu>
          <q-list dense style="min-width: 100px">
            <q-item clickable v-close-popup>
              <q-item-section>Cut</q-item-section>
            </q-item>
            <q-item clickable v-close-popup>
              <q-item-section>Copy</q-item-section>
            </q-item>
            <q-item clickable v-close-popup>
              <q-item-section>Paste</q-item-section>
            </q-item>
            <q-separator />
            <q-item clickable v-close-popup>
              <q-item-section>Select All</q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </div>

      <q-space />
      <div v-if="calcCategoryName" class="q-mr-xs text-primary">{{ calcCategoryName }} /
      </div>
      <q-input standout="bg-secondary" class="text-white dense-input" v-model="calcReportName" placeholder="请输入报告名称"
        dense>
      </q-input>
      <q-btn dense flat icon="save" @click="onSaveCalcReport">
        <AsyncTooltip tooltip="保存" />
      </q-btn>
      <q-btn dense flat icon="play_arrow" color="primary" @click="onStartExecuting" :loading="isExecuting" />
      <q-space />
    </q-bar>

    <q-splitter v-model="splitterModel" :limits="splitterLimits" before-class="overflow-hidden q-pt-sm"
      after-class="overflow-hidden relative-position" class="col">
      <template v-slot:before>
        <div class="full-height full-width" ref="monacoEditorElementRef"></div>
        <CollapseRight v-model="isCollapsed" />
      </template>

      <template v-slot:after>
        <CodePreviewer :report-oid="calcReportOId" />
      </template>
    </q-splitter>
  </div>
</template>

<style lang="scss" scoped></style>
