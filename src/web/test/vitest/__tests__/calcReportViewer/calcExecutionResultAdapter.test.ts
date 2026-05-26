import { describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import type { ExecutionResult } from 'src/api/calcExecution'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import { adaptCalcExecutionResult } from 'src/pages/calcReport/viewer/utils/calcExecutionResultAdapter'

describe('adaptCalcExecutionResult', () => {
  it('converts string visible to field visibility function', () => {
    const result: ExecutionResult = {
      executionId: 'execution-id',
      html: '',
      htmlPath: '',
      isCompleted: false,
      windows: [
        {
          title: 'input',
          fields: [
            {
              name: 'enabled',
              label: '是否启用',
              type: LowCodeFieldType.boolean,
              value: true
            },
            {
              name: 'amount',
              label: '金额',
              type: LowCodeFieldType.number,
              visible: '(values) => values.enabled === true'
            }
          ]
        }
      ]
    }

    const adaptedResult = adaptCalcExecutionResult(result)
    const visible = adaptedResult.windows[0]?.fields[1]?.visible

    expect(typeof visible).toBe('function')
    expect(typeof visible === 'function' && visible({ enabled: true })).toBe(true)
    expect(typeof visible === 'function' && visible({ enabled: false })).toBe(false)
  })

  it('keeps compiled string visible function result unchanged', () => {
    const result: ExecutionResult = {
      executionId: 'execution-id',
      html: '',
      htmlPath: '',
      isCompleted: false,
      windows: [
        {
          title: 'input',
          fields: [
            {
              name: 'amount',
              label: '金额',
              type: LowCodeFieldType.number,
              visible: '() => "visible-result"'
            }
          ]
        }
      ]
    }

    const adaptedResult = adaptCalcExecutionResult(result)
    const visible = adaptedResult.windows[0]?.fields[0]?.visible

    expect(typeof visible === 'function' && visible({})).toBe('visible-result')
  })

  it('uses visible true when string visible cannot be compiled', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    const result: ExecutionResult = {
      executionId: 'execution-id',
      html: '',
      htmlPath: '',
      isCompleted: false,
      windows: [
        {
          title: 'input',
          fields: [
            {
              name: 'amount',
              label: '金额',
              type: LowCodeFieldType.number,
              visible: 'values.enabled === true'
            }
          ]
        }
      ]
    }

    const adaptedResult = adaptCalcExecutionResult(result)

    expect(adaptedResult.windows[0]?.fields[0]?.visible).toBe(true)
    warnSpy.mockRestore()
  })

  it('converts string onChanged to field change function', async () => {
    const result: ExecutionResult = {
      executionId: 'execution-id',
      html: '',
      htmlPath: '',
      isCompleted: false,
      windows: [
        {
          title: 'input',
          fields: [
            {
              name: 'amount',
              label: '金额',
              type: LowCodeFieldType.number,
              onChanged: '(value, oldValue, allValues, allFields) => { allValues.total = value + oldValue + allFields.length }'
            }
          ]
        }
      ]
    }

    const adaptedResult = adaptCalcExecutionResult(result)
    const field = adaptedResult.windows[0]?.fields[0]
    const allValues: Record<string, number> = { amount: 2, total: 0 }

    expect(typeof field?.onChanged).toBe('function')
    if (typeof field?.onChanged === 'function') {
      await field.onChanged(3, 2, allValues, adaptedResult.windows[0]?.fields || [])
    }
    expect(allValues.total).toBe(6)
  })

  it('removes onChanged when string onChanged cannot be compiled', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    const result: ExecutionResult = {
      executionId: 'execution-id',
      html: '',
      htmlPath: '',
      isCompleted: false,
      windows: [
        {
          title: 'input',
          fields: [
            {
              name: 'amount',
              label: '金额',
              type: LowCodeFieldType.number,
              onChanged: 'allValues.total = value'
            }
          ]
        }
      ]
    }

    const adaptedResult = adaptCalcExecutionResult(result)

    expect(adaptedResult.windows[0]?.fields[0]?.onChanged).toBeUndefined()
    warnSpy.mockRestore()
  })

  it('converts visible and onChanged on the same field in one adaptation', async () => {
    const result: ExecutionResult = {
      executionId: 'execution-id',
      html: '',
      htmlPath: '',
      isCompleted: false,
      windows: [
        {
          title: 'input',
          fields: [
            {
              name: 'amount',
              label: '金额',
              type: LowCodeFieldType.number,
              visible: '(values) => values.enabled === true',
              onChanged: '(value, oldValue, allValues) => { allValues.total = value - oldValue }'
            }
          ]
        }
      ]
    }

    const adaptedResult = adaptCalcExecutionResult(result)
    const field = adaptedResult.windows[0]?.fields[0]
    const allValues: Record<string, number | boolean> = { enabled: true, total: 0 }

    expect(typeof field?.visible).toBe('function')
    expect(typeof field?.visible === 'function' && field.visible(allValues)).toBe(true)
    expect(typeof field?.onChanged).toBe('function')
    if (typeof field?.onChanged === 'function') {
      await field.onChanged(7, 3, allValues, adaptedResult.windows[0]?.fields || [])
    }
    expect(allValues.total).toBe(4)
  })

  it('handles field runtime function building without external function name', () => {
    const adapterSource = readFileSync(
      new URL('../../../../src/pages/calcReport/viewer/utils/calcExecutionResultAdapter.ts', import.meta.url),
      'utf-8'
    )

    expect(adapterSource).toContain('function buildFieldRuntimeFunction(field: ILowCodeField)')
    expect(adapterSource).not.toContain('buildFieldRuntimeFunction(field,')
  })
})
