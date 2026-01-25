<template>
  <q-splitter v-model="splitterModel" :limits="[20, 80]" before-class="overflow-hidden" after-class="overflow-hidden"
    class="full-height card-like">

    <template v-slot:before>
      <CategoryList :header="listHeader" :getCategories="onGetCategories" :createCategory="onCreateCategory"
        :updateCategory="onUpdateCategory" :deleteCategoryById="onDeleteCategoryById" />
    </template>

    <template v-slot:after>
      <CalcListView />
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
  const result = await updateCalcReportCategory(data.id, {
    name: data.name,
    order: data.order,
    description: data.description
  })
  if (result.ok && result.data) {
    return result.data
  }
  throw new Error(result.message)
}

async function onDeleteCategoryById(id: string): Promise<void> {
  const categoryId = parseInt(id, 10)
  const result = await deleteCalcReportCategory(categoryId)
  if (!result.ok) {
    throw new Error(result.message)
  }
}
// #endregion

const splitterModel = ref(33)

// #region 列表视图
import CalcListView from './components/CalcListView.vue'
// #endregion
</script>

<style lang="scss" scoped></style>
