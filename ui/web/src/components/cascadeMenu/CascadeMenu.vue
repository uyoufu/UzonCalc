<template>
  <q-menu v-bind="$attrs" class="hover-scroll">
    <CascadeMenuList :items="items" :min-width="minWidth" @item-click="emit('item-click', $event)" />
  </q-menu>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import CascadeMenuList from './CascadeMenuList.vue'
import type { ICascadeMenuActionItem, ICascadeMenuItem } from './types'

defineOptions({
  name: 'CascadeMenu',
  inheritAttrs: false
})

defineProps({
  items: {
    type: Array as PropType<ICascadeMenuItem[]>,
    required: true
  },
  minWidth: {
    type: String,
    default: '160px'
  }
})

const emit = defineEmits<{
  (event: 'item-click', item: ICascadeMenuActionItem): void
}>()
</script>

<style scoped lang="scss"></style>
