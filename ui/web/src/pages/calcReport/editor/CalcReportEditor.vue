<script lang="ts" setup>
import AsyncTooltip from 'src/components/asyncTooltip/AsyncTooltip.vue'
import CodeEditor from './components/CodeEditor.vue'

// 报告 id
const calcReportId = defineModel({
  type: String,
  default: '',
})

import { useCalcReportSaver } from './compositions/useCalcReportSaver'
const { calcReportName, onSaveCalcReport } = useCalcReportSaver(calcReportId)

// 命名格式检查
import { useCalcReportNameChecker } from './compositions/useCalcReportNameChecker'
useCalcReportNameChecker(calcReportName)

// #region 左右分割
const splitterModel = ref(50)
const defaultLimits: [number, number] = [30, 70]
const splitterLimits: Ref<[number, number]> = ref([30, 70])
// #endregion

// #region 折叠
import { useCollapse } from './compositions/useCollapse'
const { isCollapsed, CollapseRight } = useCollapse(splitterModel, splitterLimits, defaultLimits)
// #endregion

// #region 预览
import CalcPreview from './components/CalcPreview.vue'
// #endregion
</script>

<template>
  <div class="full-height full-width column no-wrap">
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

      <q-input standout="bg-secondary" class="text-white dense-input" v-model="calcReportName" placeholder="请输入报告名称"
        dense></q-input>
      <q-btn dense flat icon="save" @click="onSaveCalcReport">
        <AsyncTooltip tooltip="保存" />
      </q-btn>

      <q-space />

      <q-btn dense flat icon="play_arrow" color="primary" />
      <q-btn dense flat icon="pause" />
    </q-bar>

    <q-splitter v-model="splitterModel" :limits="splitterLimits" before-class="overflow-hidden"
      after-class="overflow-hidden relative-position" class="col">
      <template v-slot:before>
        <CodeEditor />

        <CollapseRight v-model="isCollapsed" />
      </template>

      <template v-slot:after>
        <CalcPreview />
      </template>
    </q-splitter>
  </div>
</template>

<style lang="scss" scoped></style>
