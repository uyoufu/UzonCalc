<script lang="ts" setup>
// 设置组件名，启用缓存
defineOptions({
  name: 'editCalcReport'
})

import CalcReportEditor from '../editor/CalcReportEditor.vue'
const calcCategoryOid = ref('')
const calcReportOid = ref('')
import { useRoute } from 'vue-router'
const route = useRoute()
onMounted(() => {
  calcCategoryOid.value = route.query.categoryOid as string
  calcReportOid.value = route.query.reportOid as string
})
</script>

<template>
  <CalcReportEditor v-model:calc-report-oid="calcReportOid" v-model:calc-category-oid="calcCategoryOid" />
</template>

<style lang="scss" scoped></style>
