import { describe, expect, it, vi } from 'vitest'
import { ExecutionSourceType, ExecutionStatus, ExecutorType, SandboxBackendMode, type CalcExecution } from 'src/api/calc/types'
import { adaptExecutionFields } from 'src/pages/calcExecution/utils/adaptExecutionFields'
import logger from 'loglevel'

/** Build a minimal execution response for field-adapter tests. */
function executionWithField(field: Record<string, unknown>): CalcExecution {
  return {
    executionId: 'execution', reportOid: 'report', sourceType: ExecutionSourceType.Workspace, resolvedVersion: null,
    sourceArtifactHash: 'source', executionArtifactHash: 'execution', bundleHash: 'bundle', runtimeFingerprint: 'runtime',
    executorType: ExecutorType.Local, backendMode: SandboxBackendMode.Bubblewrap, status: ExecutionStatus.Running, isCompleted: false,
    windows: [{ title: 'input', fields: [field as never] }], htmlPath: '', updateType: 1, htmlContentPatch: null,
    createdAt: new Date().toISOString(), completedAt: null
  }
}

describe('execution field adapter', () => {
  it('compiles trusted visible and onChanged callbacks', () => {
    const execution = executionWithField({ name: 'length', type: 'number', visible: '(values) => values.enabled', onChanged: '(value, old, values) => { values.total = value + old }' })
    adaptExecutionFields(execution)
    const field = execution.windows[0]!.fields[0]!
    expect(typeof field.visible).toBe('function')
    expect(typeof field.onChanged).toBe('function')
  })

  it('shows a field and removes its callback when compilation fails', () => {
    vi.spyOn(logger, 'warn').mockImplementation(() => undefined)
    const execution = executionWithField({ name: 'length', type: 'number', visible: 'invalid code', onChanged: 'invalid code' })
    adaptExecutionFields(execution)
    const field = execution.windows[0]!.fields[0]!
    expect(field.visible).toBe(true)
    expect(field.onChanged).toBeUndefined()
  })
})
