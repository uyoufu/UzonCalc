<template>
  <q-item clickable :active="isActive" @click="emit('select', category)">
    <q-item-section avatar class="category-drag-handle cursor-grab"><q-icon
        :name="category.isPinned ? 'drive_folder_upload' : 'folder'" /></q-item-section>
    <q-item-section>
      <q-item-label>{{ category.name }}</q-item-label>
      <q-item-label v-if="category.description" caption lines="1">{{ category.description }}</q-item-label>
    </q-item-section>
    <q-item-section side>{{ category.reportCount }}</q-item-section>
    <ContextMenu :items="menuItems" :value="category" />
  </q-item>
</template>

<script setup lang="ts">
/** Render one draggable report-category navigation row. */
import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type { CalcReportCategory } from 'src/api/calc/types'

defineProps<{ category: CalcReportCategory; isActive: boolean; menuItems: IContextMenuItem<CalcReportCategory>[] }>()
const emit = defineEmits<{ select: [category: CalcReportCategory] }>()
</script>
