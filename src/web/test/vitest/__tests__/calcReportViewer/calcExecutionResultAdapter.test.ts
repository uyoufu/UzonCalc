import { describe, expect, it, vi } from 'vitest'
import type { ExecutionResult } from 'src/api/calcExecution'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import { adaptCalcExecutionResult } from 'src/pages/calcReport/viewer/utils/calcExecutionResultAdapter'

describe('adaptCalcExecutionResult', () => {
  it('converts string visible to field visibility function', () => {
    const result: ExecutionResult = {
      executionId: 'execution-id',
      html: '',
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
})
