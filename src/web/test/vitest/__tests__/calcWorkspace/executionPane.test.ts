import { flushPromises, shallowMount } from '@vue/test-utils'
import { computed, onUnmounted, ref, watch } from 'vue'
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import ExecutionPane from 'src/pages/calcExecution/components/ExecutionPane.vue'
import { BuildStatus, ExecutionSourceType, ExecutionStatus } from 'src/api/calc/types'
import { isWorkspaceExecutionOutdated } from 'src/pages/calcExecution/utils/executionSourceState'

const mocks = vi.hoisted(() => ({
  getCalcReport: vi.fn(),
  listVersions: vi.fn(),
  startExecution: vi.fn(),
  continueExecution: vi.fn(),
  terminateExecution: vi.fn(),
  getWorkspaceBuild: vi.fn(),
  createInstance: vi.fn(),
  push: vi.fn()
}))

vi.mock('vue-router', () => ({ useRouter: () => ({ push: mocks.push }) }))
vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key, tButton: (key: string) => key }))
vi.mock('src/utils/dialog', () => ({
  confirmOperation: vi.fn().mockResolvedValue(true),
  notifyError: vi.fn(),
  notifySuccess: vi.fn()
}))
vi.mock('src/api/calc/reports', () => ({ getCalcReport: mocks.getCalcReport }))
vi.mock('src/api/calc/versions', () => ({ listVersions: mocks.listVersions }))
vi.mock('src/api/calc/workspace', () => ({ getWorkspaceBuild: mocks.getWorkspaceBuild }))
vi.mock('src/api/calc/executions', () => ({
  startExecution: mocks.startExecution,
  continueExecution: mocks.continueExecution,
  terminateExecution: mocks.terminateExecution
}))
vi.mock('src/api/calc/instances', () => ({ createInstance: mocks.createInstance }))
vi.mock('src/pages/calcExecution/compositions/useSaveInstanceDialog', () => ({
  useSaveInstanceDialog: () => ({ openSaveInstanceDialog: vi.fn() })
}))

function reportResponse(workspaceArtifactHash: string) {
  return {
    data: {
      reportOid: 'report-1',
      name: 'Report',
      workspaceArtifactHash,
      latestVersionName: null,
      buildStatus: BuildStatus.Ready
    }
  }
}

function executionResponse(sourceArtifactHash: string) {
  return {
    data: {
      executionId: 'execution-1',
      reportOid: 'report-1',
      sourceType: ExecutionSourceType.Workspace,
      resolvedVersion: null,
      sourceArtifactHash,
      executionArtifactHash: 'sha256:execution',
      bundleHash: 'sha256:bundle',
      runtimeFingerprint: 'runtime',
      executorType: 'local',
      backendMode: 'in_process',
      status: ExecutionStatus.Succeeded,
      isCompleted: true,
      windows: [],
      htmlPath: 'result.html',
      updateType: 1,
      htmlContentPatch: null,
      createdAt: '2026-07-17T00:00:00Z',
      completedAt: '2026-07-17T00:00:01Z'
    }
  }
}

describe('workspace execution pane', () => {
  beforeAll(() => {
    vi.stubGlobal('computed', computed)
    vi.stubGlobal('onUnmounted', onUnmounted)
    vi.stubGlobal('ref', ref)
    vi.stubGlobal('watch', watch)
    vi.stubGlobal('useRouter', () => ({ push: mocks.push }))
  })

  afterAll(() => vi.unstubAllGlobals())

  beforeEach(() => {
    vi.clearAllMocks()
    mocks.getCalcReport.mockResolvedValue(reportResponse('sha256:source-1'))
    mocks.listVersions.mockResolvedValue({ data: [] })
    mocks.startExecution.mockResolvedValue(executionResponse('sha256:source-1'))
  })

  it('refreshes workspace context without starting an execution automatically', async () => {
    const wrapper = shallowMount(ExecutionPane, {
      props: { reportOid: 'report-1', workspaceOnly: true, refreshToken: 0 }
    })
    await flushPromises()

    expect(mocks.getCalcReport).toHaveBeenCalledOnce()
    expect(mocks.startExecution).not.toHaveBeenCalled()

    await wrapper.setProps({ refreshToken: 1 })
    await flushPromises()

    expect(mocks.getCalcReport).toHaveBeenCalledTimes(2)
    expect(mocks.startExecution).not.toHaveBeenCalled()
  })

  it('marks a retained workspace result outdated when the source artifact changes', () => {
    const execution = executionResponse('sha256:source-1').data
    const report = reportResponse('sha256:source-2').data

    expect(isWorkspaceExecutionOutdated(execution as never, report as never)).toBe(true)
    expect(isWorkspaceExecutionOutdated(execution as never, reportResponse('sha256:source-1').data as never)).toBe(false)
  })
})
