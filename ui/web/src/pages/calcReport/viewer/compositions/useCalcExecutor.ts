/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  resumeCalcExecution,
  startCalcExecution,
  startFileExecution,
  type ExecutionResult
} from 'src/api/calcExecution'
import { notifyError, notifySuccess } from 'src/utils/dialog'
import { tCalcReportPageViewer } from 'src/i18n/helpers'

export function useCalcExecutor(
  reportOidRef: Ref<string, null>,
  filePathRef: Ref<string>,
  isSilentRef: Ref<boolean>,
  executeResult: Ref<ExecutionResult>
) {
  const isExecuting = ref(false)
  // #region 获取输入参数值
  function getInputValues() {
    const defaults: Record<string, Record<string, any>> = {}
    for (const ui of executeResult.value.windows) {
      const fieldValues: Record<string, any> = {}
      for (const field of ui.fields) {
        fieldValues[field.name] = field.value
      }
      defaults[ui.title] = fieldValues
    }

    return defaults
  }
  // #endregion

  const canStartExecution = computed(() => {
    return !executeResult.value.executionId
  })

  async function onStartExecution(defaults?: Record<string, Record<string, any>>) {
    if (!filePathRef.value && !reportOidRef.value) {
      notifyError(tCalcReportPageViewer('missingReportOidOrPath'))
      return
    }

    if (isExecuting.value) return
    isExecuting.value = true

    let result: ExecutionResult
    try {
      if (!defaults) defaults = getInputValues()

      // 判断是通过 reportId 还是文件路径执行
      if (reportOidRef.value) {
        // 通过 reportId 执行
        const response = await startCalcExecution({
          reportOid: reportOidRef.value,
          isSilent: isSilentRef.value,
          defaults: defaults
        })
        result = response.data
      } else if (filePathRef.value) {
        const response = await startFileExecution(filePathRef.value, defaults)
        result = response.data
      } else {
        notifyError(tCalcReportPageViewer('missingReportOidOrPath'))
        isExecuting.value = false
        return
      }
    } catch {
      isExecuting.value = false
      return
    }

    // 保存结果
    executeResult.value = result

    isExecuting.value = false
    if (result.isCompleted) {
      notifySuccess(tCalcReportPageViewer('calculationCompleted'))
    }
  }

  const canResumeExecution = computed(() => {
    return executeResult.value.executionId && !executeResult.value.isCompleted
  })
  async function onResumeExecution() {
    if (!executeResult.value.executionId) {
      notifyError(tCalcReportPageViewer('missingExecutionId'))
      return
    }

    if (isExecuting.value) return
    isExecuting.value = true

    try {
      const defaults = getInputValues()
      const response = await resumeCalcExecution(executeResult.value.executionId, defaults)
      const result = response.data

      // 合并结果
      const existUIs = executeResult.value.windows || []
      result.windows = existUIs.concat(result.windows || [])
      executeResult.value = result

      if (result.isCompleted) {
        notifySuccess(tCalcReportPageViewer('calculationCompleted'))
      }
    } catch {
      notifyError(tCalcReportPageViewer('resumeExecutionFailed'))
    } finally {
      isExecuting.value = false
    }
  }

  const canRestartExecution = computed(() => {
    return executeResult.value.executionId
  })
  async function onRestartExecution() {
    const defaults = getInputValues()
    // 相当于重新执行即可
    await onStartExecution(defaults)
  }

  return {
    isExecuting,
    canStartExecution,
    canResumeExecution,
    canRestartExecution,
    onStartExecution,
    onResumeExecution,
    onRestartExecution
  }
}
