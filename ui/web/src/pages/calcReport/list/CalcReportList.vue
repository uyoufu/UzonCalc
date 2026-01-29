<template>
  <q-splitter v-model="splitterModel" :limits="splitterLimits" before-class="overflow-hidden" :disable="isCollapsed"
    after-class="overflow-hidden relative-position" class="full-height card-like">
    <template v-slot:before>
      <CategoryList :header="listHeader" :getCategories="onGetCategories" :createCategory="onCreateCategory"
        :updateCategory="onUpdateCategory" :deleteCategoryById="onDeleteCategoryById" />
    </template>

    <template v-slot:after>
      <CalcListView />
      <CollapseLeft v-model="isCollapsed" />
    </template>
  </q-splitter>
</template>

<script lang="ts" setup>

import { t } from 'src/i18n/helpers'
import { ref } from 'vue'

// #region 分类列表

import CategoryList from 'src/components/categoryList/CategoryList.vue'
import type { ICategoryInfo, IFlatHeader } from 'src/components/categoryList/types'
import { getCalcReportCategories, createCalcReportCategory, updateCalcReportCategory, deleteCalcReportCategory } from 'src/api/calcReportCategory'

const listHeader: IFlatHeader = {
  label: t("calcReportPage.calcReport"),
  icon: 'article',
}

async function onGetCategories(): Promise<ICategoryInfo[]> {
  const result = await getCalcReportCategories()
  if (result.ok && result.data) {
    return result.data
  }
  return []
}

async function onCreateCategory(data: ICategoryInfo): Promise<ICategoryInfo> {
  const result = await createCalcReportCategory({
    name: data.name,
    order: data.order,
    description: data.description || null
  })
  if (result.ok && result.data) {
    return result.data
  }
  throw new Error(result.message)
}

async function onUpdateCategory(data: ICategoryInfo): Promise<ICategoryInfo> {
  if (!data.id) {
    throw new Error('Category id is required')
  }
  const result = await updateCalcReportCategory(data.oid, {
    name: data.name,
    order: data.order,
    description: data.description
  })
  if (result.ok && result.data) {
    return result.data
  }
  throw new Error(result.message)
}

async function onDeleteCategoryById(categoryOid: string): Promise<void> {
  const result = await deleteCalcReportCategory(categoryOid)
  if (!result.ok) {
    throw new Error(result.message)
  }
}
// #endregion

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
</script>

<style lang="scss" scoped></style>
