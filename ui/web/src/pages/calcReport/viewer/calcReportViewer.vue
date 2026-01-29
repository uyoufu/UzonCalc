<template>
  <q-bar>
    <q-space />
    calcReportViewer
    <q-space />
  </q-bar>
  <q-splitter v-model="splitterModel" class="full-height">
    <template #before>
      <InputForm />
    </template>

    <template #after>
      <ResultViewer />
    </template>
  </q-splitter>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import InputForm from './components/InputForm.vue'
import ResultViewer from './components/ResultViewer.vue'

defineOptions({
  name: 'calcReportViewer'
})

const splitterModel = ref(30)
</script>

<style lang="scss" scoped></style>
