<script lang="ts" setup>
defineOptions({
  name: 'dashboardIndex'
})

import CalcReportEditor from 'src/pages/calcReport/editor/CalcReportEditor.vue'
import { getOrCreateDefaultCategory } from 'src/api/calcReportCategory'

import { objectId } from 'src/utils/objectId';
import { t } from 'src/i18n/helpers'
import type { ICalcEditorOptions } from '../calcReport/editor/types'
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

const editorOptions: Ref<ICalcEditorOptions> = ref({
  enableSaveAs: true,
  disableRun: true
})
</script>

<template>
  <CalcReportEditor v-model:calc-category-oid="calcCategoryOid" v-model:calc-report-oid="calcReportOid"
    :editor-options="editorOptions" />
</template>

<style lang="scss" scoped></style>
