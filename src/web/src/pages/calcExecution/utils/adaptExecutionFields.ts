/** Convert trusted report-execution field callbacks into runtime functions. */

import type { CalcExecution } from 'src/api/calc/types'
import type { ILowCodeField } from 'src/components/lowCode/types'
import logger from 'loglevel'

type RuntimeFieldFunction = (...args: unknown[]) => unknown

/** Compile one trusted function string returned by a calculation script. */
function compileRuntimeFunction(field: ILowCodeField, property: 'visible' | 'onChanged', source: string): RuntimeFieldFunction | undefined {
  try {
    // Calculation scripts are trusted author content; malformed callbacks degrade safely.
    // eslint-disable-next-line @typescript-eslint/no-implied-eval
    const callback = new Function(`return (${source})`)() as unknown
    return typeof callback === 'function' ? callback as RuntimeFieldFunction : undefined
  } catch (error) {
    logger.warn(`[execution] ${field.name}.${property} compile failed`, error)
    return undefined
  }
}

/** Adapt all dynamic field callbacks in one execution response. */
export function adaptExecutionFields(execution: CalcExecution): CalcExecution {
  execution.windows.forEach((windowInfo) => windowInfo.fields.forEach((field) => {
    if (typeof field.visible === 'string') field.visible = compileRuntimeFunction(field, 'visible', field.visible) as ILowCodeField['visible'] || true
    if (typeof field.onChanged === 'string') field.onChanged = compileRuntimeFunction(field, 'onChanged', field.onChanged) as ILowCodeField['onChanged']
  }))
  return execution
}
