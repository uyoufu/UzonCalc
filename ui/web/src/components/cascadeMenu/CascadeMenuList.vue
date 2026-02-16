<template>
  <q-list dense :style="{ minWidth }">
    <template v-for="(item, index) in items" :key="item.name ?? `${level}-${index}`">
      <q-separator v-if="isSeparator(item)" :inset="item.inset" :spaced="item.spaced" />

      <q-item v-else clickable :disable="item.disable" v-close-popup="item.closeOnClick !== false && !hasChildren(item)"
        @click="onItemClick(item)">
        <q-item-section avatar v-if="item.icon">
          <q-icon :name="item.icon" />
        </q-item-section>

        <q-item-section>
          {{ item.label }}
        </q-item-section>

        <q-item-section side v-if="hasChildren(item)">
          <q-icon name="keyboard_arrow_right" />
        </q-item-section>

        <q-menu v-if="hasChildren(item)" anchor="top end" self="top start">
          <CascadeMenuList :items="item.children ?? []" :level="level + 1" :min-width="minWidth"
            @item-click="emit('item-click', $event)" />
        </q-menu>
      </q-item>
    </template>
  </q-list>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { ICascadeMenuActionItem, ICascadeMenuItem, ICascadeMenuSeparatorItem } from './types'

defineOptions({
  name: 'CascadeMenuList'
})

const props = defineProps({
  items: {
    type: Array as PropType<ICascadeMenuItem[]>,
    required: true
  },
  level: {
    type: Number,
    default: 0
  },
  minWidth: {
    type: String,
    default: '160px'
  }
})

const emit = defineEmits<{
  (event: 'item-click', item: ICascadeMenuActionItem): void
}>()

function isSeparator(item: ICascadeMenuItem): item is ICascadeMenuSeparatorItem {
  return item.type === 'separator'
}

function hasChildren(item: ICascadeMenuItem): item is ICascadeMenuActionItem {
  return !isSeparator(item) && Array.isArray(item.children) && item.children.length > 0
}

async function onItemClick(item: ICascadeMenuItem) {
  if (isSeparator(item)) return
  if (item.disable || hasChildren(item)) return

  const actionItem = item as ICascadeMenuActionItem

  if (typeof actionItem.onClick === 'function') {
    await actionItem.onClick(actionItem)
  }

  emit('item-click', actionItem)
}
</script>

<style scoped lang="scss"></style>
