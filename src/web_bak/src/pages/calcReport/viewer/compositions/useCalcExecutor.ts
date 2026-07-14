/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  resumeCalcExecution,
  startCalcExecution,
  startFileExecution,
  type ExecutionResult
} from 'src/api/calcExecution'
import { notifyError, notifySuccess } from 'src/utils/dialog'
import { tCalcReportPageViewer } from 'src/i18n/helpers'
import { isCalcReportExecutingKey } from '../keys'
import { adaptCalcExecutionResult } from '../utils/calcExecutionResultAdapter'

export function useCalcExecutor(
  reportOidRef: Ref<string, null>,
  filePathRef: Ref<string>,
  isSilentRef: Ref<boolean>,
  executeResult: Ref<ExecutionResult>
) {
  // 可以通过外部注入的方式控制执行状态，避免重复执行
  const isExecuting = inject(isCalcReportExecutingKey, ref(false))

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
      const lastHtmlPath = executeResult.value.htmlPath || undefined

      // 判断是通过 reportId 还是文件路径执行
      if (reportOidRef.value) {
        // 通过 reportId 执行
        const response = await startCalcExecution({
          reportOid: reportOidRef.value,
          isSilent: isSilentRef.value,
          defaults: defaults,
          lastHtmlPath
        })
        result = response.data
      } else if (filePathRef.value) {
        const response = await startFileExecution(filePathRef.value, defaults, lastHtmlPath)
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

    // 保存前适配后端传入的字段可见性配置
    executeResult.value = adaptCalcExecutionResult(result)

    isExecuting.value = false
    if (result.isCompleted) {
      notifySuccess(tCalcReportPageViewer('calculationCompleted'))
    }
    return result
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
      const lastHtmlPath = executeResult.value.htmlPath || undefined
      const response = await resumeCalcExecution(executeResult.value.executionId, defaults, lastHtmlPath)
      const result = adaptCalcExecutionResult(response.data)

      // 合并结果
      const existUIs = executeResult.value.windows || []
      result.windows = existUIs.concat(result.windows || [])
      executeResult.value = result

      if (result.isCompleted) {
        notifySuccess(tCalcReportPageViewer('calculationCompleted'))
      }
      return result
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
    return await onStartExecution(defaults)
  }

  return {
    isExecuting,
    canStartExecution,
    canResumeExecution,
    canRestartExecution,
    getInputValues,
    onStartExecution,
    onResumeExecution,
    onRestartExecution
  }
}
