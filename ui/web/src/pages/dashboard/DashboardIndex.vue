<script lang="ts" setup>
import CalcReportEditor from 'src/pages/calcReport/editor/CalcReportEditor.vue'
import { getOrCreateDefaultCategory } from 'src/api/calcReportCategory'

import { objectId } from 'src/utils/objectId';
import { t } from 'src/i18n/helpers'
// 获取默认的计算报告分类
const calcReportOid = ref('')
const calcCategoryOid = ref('')
onMounted(async () => {
  // 获取默认分类
  const category = await getOrCreateDefaultCategory(t('dashboardPage.noCategory'))
  calcCategoryOid.value = category.data.oid

  // 随机报告 id
  calcReportOid.value = objectId()
})
</script>

<template>
  <CalcReportEditor v-model:calc-category-oid="calcCategoryOid" v-model:calc-report-oid="calcReportOid"
    :enable-save-as="true" />
</template>

<style lang="scss" scoped></style>
