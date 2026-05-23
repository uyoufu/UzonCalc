/* eslint-disable @typescript-eslint/no-explicit-any */
import type { ExecutionResult } from 'src/api/calcExecution'
import type { ILowCodeField } from 'src/components/lowCode/types'

import logger from 'loglevel'

type VisibleFunction = (allValues: Record<string, any>) => boolean

// 编译后端传入的字符串可见性函数
function buildVisibleFunction(field: ILowCodeField): VisibleFunction | undefined {
  if (typeof field.visible !== 'string') return undefined

  try {
    // visible 来自可信计算脚本，字符串本身应为可直接消费的函数
    // eslint-disable-next-line @typescript-eslint/no-implied-eval
    const visibleFunction = new Function(`return (${field.visible})`)()
    if (typeof visibleFunction !== 'function') {
      logger.warn(`[calcReportViewer] field ${field.name} visible not a function`)
      return undefined
    }

    return visibleFunction as VisibleFunction
  } catch (error) {
    logger.warn(`[calcReportViewer] field ${field.name} visible compile failed`, error)
    return undefined
  }
}

// 将计算执行结果中的字段配置转换为前端表单可直接消费的结构
export function adaptCalcExecutionResult(result: ExecutionResult): ExecutionResult {
  for (const windowInfo of result.windows || []) {
    for (const field of windowInfo.fields || []) {
      if (typeof field.visible !== 'string') continue

      const visibleFunction = buildVisibleFunction(field)
      field.visible = visibleFunction || true
    }
  }

  return result
}
