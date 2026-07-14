/* eslint-disable @typescript-eslint/no-explicit-any */
import type { ExecutionResult } from 'src/api/calcExecution'
import type { ILowCodeField } from 'src/components/lowCode/types'

import logger from 'loglevel'

type VisibleFunction = (allValues: Record<string, any>) => boolean
type FieldRuntimeFunction = (...args: any[]) => any

// 编译指定字段属性中的函数字符串
function compileFieldRuntimeFunction(
  field: ILowCodeField,
  functionName: 'visible' | 'onChanged',
  functionText: string
): FieldRuntimeFunction | undefined {
  try {
    // 字段函数来自可信计算脚本，字符串本身应为可直接消费的函数
    // eslint-disable-next-line @typescript-eslint/no-implied-eval
    const fieldFunction = new Function(`return (${functionText})`)()
    if (typeof fieldFunction !== 'function') {
      logger.warn(`[calcReportViewer] field ${field.name} ${functionName} not a function`)
      return undefined
    }

    return fieldFunction as FieldRuntimeFunction
  } catch (error) {
    logger.warn(`[calcReportViewer] field ${field.name} ${functionName} compile failed`, error)
    return undefined
  }
}

// 统一处理后端传入的字段运行时函数字符串
function buildFieldRuntimeFunction(field: ILowCodeField): void {
  if (typeof field.visible === 'string') {
    // visible 编译失败时默认显示字段，避免输入项被意外隐藏
    const visibleFunction = compileFieldRuntimeFunction(field, 'visible', field.visible) as
      | VisibleFunction
      | undefined
    field.visible = visibleFunction || true
  }

  if (typeof field.onChanged === 'string') {
    // onChanged 编译失败时移除变更回调，避免运行时触发无效字符串
    const onChangedFunction = compileFieldRuntimeFunction(field, 'onChanged', field.onChanged) as
      | ILowCodeField['onChanged']
      | undefined
    field.onChanged = onChangedFunction
  }
}

// 将计算执行结果中的字段配置转换为前端表单可直接消费的结构
export function adaptCalcExecutionResult(result: ExecutionResult): ExecutionResult {
  for (const windowInfo of result.windows || []) {
    for (const field of windowInfo.fields || []) {
      buildFieldRuntimeFunction(field)
    }
  }

  return result
}

