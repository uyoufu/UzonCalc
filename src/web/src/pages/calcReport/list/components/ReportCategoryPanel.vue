<template>
  <aside class="report-categories column no-wrap">
    <div class="report-categories__header row items-center justify-between q-px-sm">
      <div class="text-subtitle2">{{ t('calcWorkspace.categories') }}</div>
      <div class="row items-center q-gutter-xs">
        <CommonBtn flat dense :icon="isShowingHidden ? 'visibility_off' : 'visibility'"
          :tooltip="t(isShowingHidden ? 'calcWorkspace.hideHiddenCategories' : 'calcWorkspace.showHiddenCategories')"
          @click="isShowingHidden = !isShowingHidden" :cache-tip="false" />
        <CommonBtn flat dense icon="add" :tooltip="t('calcWorkspace.newCategory')" @click="emit('create')" />
      </div>
    </div>
    <q-separator />
    <q-list dense class="col scroll">
      <q-item clickable :active="modelValue === FixedReportCategoryFilter.Favorites"
        @click="onFixedCategoryClick(FixedReportCategoryFilter.Favorites)">
        <q-item-section avatar><q-icon name="star" color="warning" /></q-item-section>
        <q-item-section>{{ t('calcWorkspace.myFavorites') }}</q-item-section>
      </q-item>
      <q-item clickable :active="modelValue === FixedReportCategoryFilter.Shared"
        @click="onFixedCategoryClick(FixedReportCategoryFilter.Shared)">
        <q-item-section avatar><q-icon name="group" color="primary" /></q-item-section>
        <q-item-section>{{ t('calcWorkspace.sharedReports') }}</q-item-section>
      </q-item>
      <q-item clickable :active="modelValue === null" @click="onFixedCategoryClick(null)">
        <q-item-section avatar><q-icon name="all_inbox" /></q-item-section>
        <q-item-section>{{ t('calcWorkspace.allReports') }}</q-item-section>
      </q-item>
      <q-separator spaced />
      <VueDraggable v-model="pinnedCategories" :group="categoryDragGroup" :animation="150"
        handle=".category-drag-handle" @end="onCategoryDragEnd">
        <CategoryRow v-for="category in pinnedCategories" :key="category.categoryOid" :category="category"
          :is-active="modelValue === category.categoryOid" :menu-items="categoryMenuItems"
          @select="onPersistedCategoryClick" />
      </VueDraggable>
      <VueDraggable v-model="automaticCategories" :group="categoryDragGroup" :animation="150"
        handle=".category-drag-handle" @end="onCategoryDragEnd">
        <CategoryRow v-for="category in automaticCategories" :key="category.categoryOid" :category="category"
          :is-active="modelValue === category.categoryOid" :menu-items="categoryMenuItems"
          @select="onPersistedCategoryClick" />
      </VueDraggable>
    </q-list>
  </aside>
</template>

<script setup lang="ts">
/** Fixed navigation, pinned ordering, hiding, and LFU categories. */
import { VueDraggable } from 'vue-draggable-plus'
import CategoryRow from './ReportCategoryRow.vue'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type { CalcReportCategory } from 'src/api/calc/types'
import { t } from 'src/i18n/helpers'
import { FixedReportCategoryFilter, type ReportCategorySelection } from './reportCategoryFilter'

const props = defineProps<{ categories: CalcReportCategory[]; modelValue: ReportCategorySelection }>()
const emit = defineEmits<{
  'update:modelValue': [value: ReportCategorySelection]
  create: []
  edit: [category: CalcReportCategory]
  delete: [category: CalcReportCategory]
  organize: [categories: CalcReportCategory[]]
  access: [category: CalcReportCategory]
}>()

const isShowingHidden = ref(false)
const pinnedCategories = ref<CalcReportCategory[]>([])
const automaticCategories = ref<CalcReportCategory[]>([])
const categoryDragGroup = { name: 'report-categories', pull: true, put: true }

/** Synchronize local drag lists from server-owned category state. */
function synchronizeCategoryGroups(): void {
  const visible = props.categories.filter((category) => isShowingHidden.value || !category.isHidden)
  pinnedCategories.value = visible.filter((category) => category.isPinned)
  automaticCategories.value = visible.filter((category) => !category.isPinned)
}
watch(() => props.categories, synchronizeCategoryGroups, { immediate: true, deep: true })
watch(isShowingHidden, synchronizeCategoryGroups)

const categoryMenuItems: IContextMenuItem<CalcReportCategory>[] = [
  { name: 'pin', label: t('calcWorkspace.pinCategory'), icon: 'drive_folder_upload', color: 'primary', vif: (category) => !category.isPinned, onClick: (category) => emit('organize', [{ ...category, isPinned: true }, ...props.categories.filter((value) => value.categoryOid !== category.categoryOid)]) },
  { name: 'unpin', label: t('calcWorkspace.unpinCategory'), icon: 'folder_open', color: 'grey-8', vif: (category) => category.isPinned, onClick: (category) => emit('organize', props.categories.map((value) => value.categoryOid === category.categoryOid ? { ...value, isPinned: false } : value)) },
  { name: 'hide', label: t('calcWorkspace.hideCategory'), icon: 'visibility_off', color: 'grey-8', vif: (category) => !category.isHidden, onClick: (category) => emit('organize', props.categories.map((value) => value.categoryOid === category.categoryOid ? { ...value, isHidden: true } : value)) },
  { name: 'show', label: t('calcWorkspace.showCategory'), icon: 'visibility', color: 'grey-8', vif: (category) => category.isHidden, onClick: (category) => emit('organize', props.categories.map((value) => value.categoryOid === category.categoryOid ? { ...value, isHidden: false } : value)) },
  { name: 'edit', label: t('global.edit'), icon: 'edit', color: 'grey-9', onClick: (category) => emit('edit', category) },
  { name: 'delete', label: t('global.delete'), icon: 'delete', color: 'negative', onClick: (category) => emit('delete', category) }
]

/** Select one fixed filter without recording LFU usage. */
function onFixedCategoryClick(category: ReportCategorySelection): void {
  emit('update:modelValue', category)
}

/** Select a persisted category and record its LFU access. */
function onPersistedCategoryClick(category: CalcReportCategory): void {
  emit('update:modelValue', category.categoryOid)
  emit('access', category)
}

/** Convert cross-group drag state into pinned/manual ordering semantics. */
function onCategoryDragEnd(): void {
  const pinned = pinnedCategories.value.map((category, manualOrder) => ({ ...category, isPinned: true, manualOrder }))
  const automatic = automaticCategories.value.map((category) => ({ ...category, isPinned: false }))
  emit('organize', [...pinned, ...automatic])
}
</script>

<style scoped>
.report-categories {
  width: 248px;
  min-width: 248px;
  border-right: 1px solid #e4e7ec;
  background: #fff;
}

.report-categories__header {
  min-height: 44px;
}
</style>
