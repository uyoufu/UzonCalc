<template>
  <aside class="report-categories column no-wrap">
    <div class="report-categories__header row items-center justify-between q-px-sm">
      <div class="text-subtitle2">{{ t('calcWorkspace.categories') }}</div>
      <q-btn flat round dense icon="add" @click="emit('create')">
        <q-tooltip>{{ t('calcWorkspace.newCategory') }}</q-tooltip>
      </q-btn>
    </div>
    <q-separator />
    <q-list dense class="col scroll">
      <q-item clickable :active="modelValue === null" @click="emit('update:modelValue', null)">
        <q-item-section avatar><q-icon name="all_inbox" /></q-item-section>
        <q-item-section>{{ t('calcWorkspace.allReports') }}</q-item-section>
      </q-item>
      <draggable :model-value="categories" item-key="categoryOid" @update:model-value="onReorder">
        <template #item="{ element: category }">
          <q-item clickable :active="modelValue === category.categoryOid"
            @click="emit('update:modelValue', category.categoryOid)">
            <q-item-section avatar><q-icon name="folder" /></q-item-section>
            <q-item-section>
              <q-item-label>{{ category.name }}</q-item-label>
              <q-item-label v-if="category.description" caption lines="1">{{ category.description }}</q-item-label>
            </q-item-section>
            <q-item-section side>{{ category.reportCount }}</q-item-section>
            <ContextMenu :items="categoryMenuItems" :value="category" />
          </q-item>
        </template>
      </draggable>
    </q-list>
  </aside>
</template>

<script setup lang="ts">
/** Category navigation and ordering for the report library. */
import draggable from 'vuedraggable'
import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type { CalcReportCategory } from 'src/api/calc/types'
import { t } from 'src/i18n/helpers'

defineProps<{ categories: CalcReportCategory[]; modelValue: string | null }>()
const emit = defineEmits<{
  'update:modelValue': [value: string | null]
  create: []
  edit: [category: CalcReportCategory]
  delete: [category: CalcReportCategory]
  reorder: [categories: CalcReportCategory[]]
}>()

const categoryMenuItems: IContextMenuItem<CalcReportCategory>[] = [
  { name: 'edit', label: t('global.edit'), icon: 'edit', color: 'grey-9', onClick: (category) => emit('edit', category) },
  { name: 'delete', label: t('global.delete'), icon: 'delete', color: 'negative', onClick: (category) => emit('delete', category) }
]

/** Emit a stable order after drag-and-drop. */
function onReorder(value: CalcReportCategory[]): void {
  emit('reorder', value.map((category, sortOrder) => ({ ...category, sortOrder })))
}
</script>

<style scoped>
.report-categories { width: 240px; min-width: 240px; border-right: 1px solid #e4e7ec; background: #fff; }
.report-categories__header { min-height: 44px; }
</style>
