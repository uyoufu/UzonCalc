<template>
  <q-splitter v-model="splitterModel" :limits="splitterLimits" before-class="overflow-hidden" :disable="isCollapsed"
    after-class="overflow-hidden relative-position" class="full-height card-like">
    <template v-slot:before>
      <CategoryList v-model="activatedCategory" :header="listHeader" :getCategories="onGetCategories"
        :createCategory="onCreateCategory" :updateCategory="onUpdateCategory" :deleteCategoryById="onDeleteCategoryById"
        :refresh-signal="instanceListUpdateSignal" />
    </template>

    <template v-slot:after>
      <InstanceListView :category="activatedCategory" />
      <CollapseLeft v-model="isCollapsed" />
    </template>
  </q-splitter>
</template>

<script lang="ts" setup>
defineOptions({
  name: 'calcReportInstanceList'
})

import { ref, watch } from 'vue'
import { useWindowSize } from '@vueuse/core'
import CategoryList from 'src/components/categoryList/CategoryList.vue'
import CollapseLeft from 'src/components/collapseIcon/CollapseLeft.vue'
import type { ICategoryInfo } from 'src/components/categoryList/types'
import InstanceListView from './components/InstanceListView.vue'
import { useInstanceCategory } from './compositions/useInstanceCategory'
import { useInstanceListStore } from './compositions/useInstanceListStore'

const { listHeader, onGetCategories, onCreateCategory, onUpdateCategory, onDeleteCategoryById } = useInstanceCategory()

const activatedCategory = ref<ICategoryInfo>({
  name: '',
  oid: '',
  order: 0
})

const splitterModel = ref(25)
const splitterLimits = ref([20, 80])
const isCollapsed = ref(false)
const lastSplitterModel = ref(splitterModel.value)

watch(isCollapsed, (newVal) => {
  if (newVal) {
    lastSplitterModel.value = splitterModel.value
    splitterLimits.value = [0, 100]
    splitterModel.value = 0
  } else {
    splitterLimits.value = [20, 80]
    splitterModel.value = lastSplitterModel.value
  }
})

const { width } = useWindowSize()
watch(width, (newWidth) => {
  if (newWidth < 600) {
    isCollapsed.value = true
  } else {
    isCollapsed.value = false
  }
}, { immediate: true })

const { instanceListUpdateSignal } = useInstanceListStore()
</script>

<style lang="scss" scoped></style>
