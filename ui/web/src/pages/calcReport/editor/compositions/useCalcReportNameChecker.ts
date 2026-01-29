import { notifyError } from "src/utils/dialog"
import _ from "lodash"

/**
   * 检查计算报告名称是否符合 Python 变量名命名规则
   * @returns 是否符合要求
   */
export function checkCalcReportName (calcReportName: string) {
  // Python 变量名要求：字母或下划线开头，后接字母、数字或下划线
  const pythonIdentifierRegex = /^[a-zA-Z_][a-zA-Z0-9_]*$/
  if (!pythonIdentifierRegex.test(calcReportName)) {
    notifyError('calcReportPage.pleaseInputCalcReportName')
    return false
  }
  return true
}

export function useCalcReportNameChecker (calcReportNameRef: Ref<string>) {
  const debouncedCheck = _.debounce(checkCalcReportName, 500)
  watch(calcReportNameRef, () => {
    // 进行防抖处理
    debouncedCheck(calcReportNameRef.value)
  })
}
