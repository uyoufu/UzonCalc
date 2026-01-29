import { t } from 'src/i18n/helpers'
import { checkCalcReportName } from './useCalcReportNameChecker'
import { notifySuccess } from 'src/utils/dialog'

/**
 * 不可多次调用该函数，避免重复 onMounted
 * @param calcReportId
 * @returns
 */
export function useCalcReportSaver (calcReportId: Ref<string>) {
  const calcReportName = ref(t('calcReportPage.defaultCalcReportName'))

  onMounted(() => {
    if (!calcReportId.value) {
      return
    }

    // 请求计算报告数据

  })

  function onSaveCalcReport () {
    // 保存前检查名称是否合法
    if (!checkCalcReportName(calcReportName.value)) {
      return
    }

    // 保存内容

    notifySuccess('保存成功')
  }

  return {
    calcReportName,
    onSaveCalcReport
  }
}
