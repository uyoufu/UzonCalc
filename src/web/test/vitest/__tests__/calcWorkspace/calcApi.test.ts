import { beforeEach, describe, expect, it, vi } from 'vitest'
import { continueExecution, getCurrentExecution, startExecution } from 'src/api/calc/executions'
import { countCalcReports, listCalcReports } from 'src/api/calc/reports'
import { countInstances, listInstances } from 'src/api/calc/instances'
import { saveWorkspace } from 'src/api/calc/workspace'
import { downloadRemoteShare, downloadShare, resolveBackendShareSource, resolveShareResultUrl } from 'src/api/calc/shares'
import { ExecutionSourceType, WorkspaceFileSource } from 'src/api/calc/types'

const httpClientMock = vi.hoisted(() => ({ get: vi.fn(), getBlob: vi.fn(), post: vi.fn(), postBlob: vi.fn(), put: vi.fn() }))
vi.mock('src/api/base/httpClient', () => ({ httpClient: httpClientMock }))

describe('calculation APIs', () => {
  beforeEach(() => vi.clearAllMocks())

  it('posts the selected immutable execution source to the current route', async () => {
    await startExecution({ reportOid: 'report-oid', source: { type: ExecutionSourceType.Version, versionName: '1.2.3' }, defaults: {}, isSilent: false })
    expect(httpClientMock.post).toHaveBeenCalledWith('/calc/execution', {
      data: { reportOid: 'report-oid', source: { type: ExecutionSourceType.Version, versionName: '1.2.3' }, defaults: {}, isSilent: false }
    })

    await continueExecution('execution-oid', { input: { length: 4 } }, 'public/calcs/old.html')
    expect(httpClientMock.post).toHaveBeenLastCalledWith('/calc/execution/execution-oid/continue', {
      data: { defaults: { input: { length: 4 } }, lastHtmlPath: 'public/calcs/old.html' }
    })
  })

  it('serializes a complete workspace snapshot and preserves upload paths', async () => {
    await saveWorkspace('report-oid', {
      workspaceRevision: 3,
      files: [{ path: 'src/main.py', source: WorkspaceFileSource.Upload }, { path: 'resources/logo.png', source: WorkspaceFileSource.Current, sha256: 'sha256:value' }],
      dependencies: []
    }, [{ path: 'src/main.py', content: new Blob(['print(1)']) }])

    const formData = httpClientMock.put.mock.calls[0]?.[1].data as FormData
    const snapshotEntry = formData.get('snapshot')
    expect(typeof snapshotEntry).toBe('string')
    const serializedSnapshot = JSON.parse(snapshotEntry as string) as { workspaceRevision: number; files: Array<{ path: string }> }
    expect(httpClientMock.put.mock.calls[0]?.[0]).toBe('/calc-report/report-oid/workspace')
    expect(serializedSnapshot).toMatchObject({ workspaceRevision: 3 })
    expect(formData.get('files')).toBeInstanceOf(Blob)
    expect(serializedSnapshot.files[0]?.path).toBe('src/main.py')
  })

  it('uses explicit count and items routes with PaginationDTO fields', async () => {
    const pagination = { skip: 20, limit: 20, sortBy: 'updatedAt', descending: true }

    await countCalcReports({ categoryOid: 'report-category', query: 'beam', favoriteOnly: true })
    expect(httpClientMock.get).toHaveBeenCalledWith('/calc-report/count', {
      params: { categoryOid: 'report-category', query: 'beam', favoriteOnly: true }
    })
    await listCalcReports({ categoryOid: 'report-category', query: 'beam', favoriteOnly: true, ...pagination })
    expect(httpClientMock.get).toHaveBeenCalledWith('/calc-report/items', {
      params: { categoryOid: 'report-category', query: 'beam', favoriteOnly: true, ...pagination }
    })

    await countInstances({ categoryOid: 'instance-category' })
    expect(httpClientMock.get).toHaveBeenCalledWith('/calc-report-instance/count', {
      params: { categoryOid: 'instance-category' }
    })
    await listInstances({ categoryOid: 'instance-category', ...pagination })
    expect(httpClientMock.get).toHaveBeenCalledWith('/calc-report-instance/items', {
      params: { categoryOid: 'instance-category', ...pagination }
    })

    await getCurrentExecution('report-oid', { type: ExecutionSourceType.Version, versionName: '1.2.3' })
    expect(httpClientMock.get).toHaveBeenCalledWith('/calc/execution/current', {
      params: { reportOid: 'report-oid', sourceType: ExecutionSourceType.Version, versionName: '1.2.3' }
    })
  })

  it('uses source presence as the only frontend share-link discriminator', () => {
    const backendUrl = 'https://example.com/v1/calc-report/shared/token/preview'
    const encodedSource = btoa(backendUrl).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '')

    expect(resolveBackendShareSource(`${window.location.origin}/calc-report/shared/import?source=${encodedSource}`)).toBe(backendUrl)
    expect(resolveBackendShareSource(backendUrl)).toBe(backendUrl)
  })

  it('uses blob endpoints for local and remote share downloads', async () => {
    await downloadShare('share-token')
    expect(httpClientMock.getBlob).toHaveBeenCalledWith('/calc-report/shared/share-token/archive')

    await downloadRemoteShare('https://example.com/v1/calc-report/shared/token/preview')
    expect(httpClientMock.postBlob).toHaveBeenCalledWith('/calc-report/imports/link/archive', {
      data: { source: 'https://example.com/v1/calc-report/shared/token/preview' }
    })
  })

  it('resolves local result paths against the backend without leaking tokens remotely', () => {
    expect(resolveShareResultUrl('/api/v1/calc-report/shared/share-token/result', true, 'jwt-token')).toBe(
      'http://localhost:3345/api/v1/calc-report/shared/share-token/result?token=jwt-token'
    )
    expect(resolveShareResultUrl('https://remote.example/api/v1/calc-report/shared/share-token/result', false, 'jwt-token')).toBe(
      'https://remote.example/api/v1/calc-report/shared/share-token/result'
    )
  })
})
