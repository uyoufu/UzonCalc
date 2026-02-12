<template>
  <q-splitter v-model="splitterModel" :limits="splitterLimits" before-class="overflow-hidden" :disable="isCollapsed"
    after-class="overflow-hidden relative-position" class="full-height card-like">
    <template v-slot:before>
      <CategoryList v-model="activatedCategory" :header="listHeader" :getCategories="onGetCategories"
        :createCategory="onCreateCategory" :updateCategory="onUpdateCategory" :deleteCategoryById="onDeleteCategoryById"
        :refresh-signal="calcListUpdateSignal" />
    </template>

    <template v-slot:after>
      <CalcListView :category="activatedCategory" />
      <CollapseLeft v-model="isCollapsed" />
    </template>
  </q-splitter>
</template>

<script lang="ts" setup>

defineOptions({
  name: 'calcReportList'
})

import { ref, watch } from 'vue'

// #region MARK: 分类列表

import CategoryList from 'src/components/categoryList/CategoryList.vue'
import { useCalcCategory } from './compositions/useCalcCategory'

const { listHeader, onGetCategories, onCreateCategory, onUpdateCategory, onDeleteCategoryById } = useCalcCategory()
// #endregion

import type { ICategoryInfo } from 'src/components/categoryList/types'
const activatedCategory = ref<ICategoryInfo>({
  name: '',
  oid: '',
  order: 0,
})

const splitterModel = ref(25)
const splitterLimits = ref([20, 80])

// #region 列表视图
import CalcListView from './components/CalcListView.vue'
// #endregion

// #region 向左折叠
import CollapseLeft from 'src/components/collapseIcon/CollapseLeft.vue'
const isCollapsed = ref(false)
const lastSplitterModel = ref(splitterModel.value)
watch(isCollapsed, (newVal) => {
  if (newVal) {
    // 折叠
    lastSplitterModel.value = splitterModel.value
    splitterLimits.value = [0, 100]
    splitterModel.value = 0
  } else {
    // 展开
    splitterLimits.value = [20, 80]
    splitterModel.value = lastSplitterModel.value
  }
})

// 当窗体大小变化时，根据大小进行折叠状态调整
import { useWindowSize } from '@vueuse/core'
const { width } = useWindowSize()
watch(width, (newWidth) => {
  if (newWidth < 600) {
    // 窗体较小，自动折叠
    isCollapsed.value = true
  } else {
    // 窗体较大，恢复上次状态
    isCollapsed.value = false
  }
}, { immediate: true })
// #endregion

// #region MARK: 列表更新
import { useCalcListStore } from './compositions/useCalcListStore'
const { calcListUpdateSignal } = useCalcListStore()
// #endregion
</script>

<style lang="scss" scoped></style>
