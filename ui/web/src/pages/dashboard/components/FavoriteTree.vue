<template>
  <div class="q-pa-md q-gutter-sm">
    <q-input ref="filterRef" filled v-model="filter" label="Filter">
      <template v-slot:append>
        <q-icon v-if="filter !== ''" name="clear" class="cursor-pointer" @click="resetFilter" />
      </template>
    </q-input>

    <q-tree :nodes="simple" node-key="label" :filter="filter" default-expand-all />
  </div>
</template>

<script lang="ts" setup>

</script>

<style lang="scss" scoped></style>
