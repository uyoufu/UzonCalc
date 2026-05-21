<template>
  <q-btn class="q-pr-sm q-py-none" :dense="dense" :color="color" :size="size" :icon="icon" :label="label"
    v-bind="$attrs">
    <template v-for="(slot, slotName) in $slots">
      <slot :name="slotName"></slot>
    </template>
    <AsyncTooltip :tooltip="tooltip" />
  </q-btn>
</template>

<script lang="ts" setup>
import AsyncTooltip from 'src/components/asyncTooltip/AsyncTooltip.vue'
import { tButton } from 'src/i18n/helpers'

defineProps({
  color: {
    type: String,
    default: 'secondary'
  },
  icon: {
    type: String,
    default: 'download'
  },
  label: {
    type: String,
    default: tButton('export')
  },
  tooltip: {
    type: String,
    default: tButton('exportData')
  },
  size: {
    type: String,
    default: 'md'
  },
  dense: {
    type: Boolean,
    default: true
  }
})

</script>

<style lang="scss" scoped></style>
