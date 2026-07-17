import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { BuildStatus, PublishState, type WorkspaceSnapshot } from 'src/api/calc/types'
import {
  buildWorkspaceTree,
  createDefaultWorkspaceFiles,
  normalizeWorkspacePath,
  useWorkspaceDraft
} from 'src/pages/calcReport/workbench/workspace/useWorkspaceDraft'

const getWorkspaceFileMock = vi.hoisted(() => vi.fn())
vi.mock('src/api/calc/workspace', () => ({ getWorkspaceFile: getWorkspaceFileMock }))

const snapshot: WorkspaceSnapshot = {
  reportOid: '67abcdefabcdefabcdefabcd',
  workspaceRevision: 4,
  sourceArtifactHash: `sha256:${'1'.repeat(64)}`,
  entryPath: 'src/main.py',
  formatVersion: 1,
  files: [
    { path: 'calcbook.json', size: 47, sha256: `sha256:${'2'.repeat(64)}` },
    { path: 'src/main.py', size: 10, sha256: `sha256:${'3'.repeat(64)}` },
    { path: 'resources/logo.png', size: 3, sha256: `sha256:${'4'.repeat(64)}` }
  ],
  dependencies: [],
  buildStatus: BuildStatus.NotRequested,
  publishState: PublishState.Unpublished
}

describe('workspace draft', () => {
  it('normalizes valid paths and rejects paths outside workspace roots', () => {
    expect(normalizeWorkspacePath('/src/main.py/')).toBe('src/main.py')
    expect(() => normalizeWorkspacePath('../main.py')).toThrow()
    expect(() => normalizeWorkspacePath('main.py')).toThrow()
  })

  it('derives folders from files without persisting empty directories', () => {
    const tree = buildWorkspaceTree(createDefaultWorkspaceFiles())
    expect(tree.map((node) => node.path)).toEqual(['calcbook.json', 'src', 'src/main.py'])
    expect(tree.find((node) => node.path === 'src')?.kind).toBe('folder')
  })

  it('builds current descriptors for unchanged files and uploads changed files', async () => {
    getWorkspaceFileMock.mockResolvedValue(new Blob(['print(1)']))
    const draft = useWorkspaceDraft(ref(snapshot.reportOid))
    draft.initializeFromSnapshot(snapshot)
    const source = draft.files.value.find((file) => file.path === 'src/main.py')!
    await draft.ensureFileLoaded(source)
    draft.updateText(source.path, 'print(2)')

    const payload = draft.buildSavePayload()
    expect(payload.snapshot.workspaceRevision).toBe(4)
    expect(payload.snapshot.files.find((file) => file.path === 'src/main.py')?.source).toBe('upload')
    expect(payload.snapshot.files.find((file) => file.path === 'resources/logo.png')?.source).toBe('current')
    expect(payload.uploads).toHaveLength(1)
  })

  it('clears text dirty state when editor undo restores synchronized content', async () => {
    getWorkspaceFileMock.mockResolvedValue(new Blob(['print(1)']))
    const draft = useWorkspaceDraft(ref(snapshot.reportOid))
    draft.initializeFromSnapshot(snapshot)
    const source = draft.files.value.find((file) => file.path === 'src/main.py')!
    await draft.ensureFileLoaded(source)

    draft.updateText(source.path, 'print(2)')
    expect(draft.hasUnsavedChanges.value).toBe(true)

    draft.updateText(source.path, 'print(1)')
    expect(source.isDirty).toBe(false)
    expect(draft.hasUnsavedChanges.value).toBe(false)
    expect(draft.buildSavePayload().uploads).toHaveLength(0)
  })

  it('uses newly saved text as the next undo baseline', async () => {
    getWorkspaceFileMock.mockResolvedValue(new Blob(['print(1)']))
    const draft = useWorkspaceDraft(ref(snapshot.reportOid))
    draft.initializeFromSnapshot(snapshot)
    const source = draft.files.value.find((file) => file.path === 'src/main.py')!
    await draft.ensureFileLoaded(source)
    draft.updateText(source.path, 'print(2)')
    draft.markSaved({
      ...snapshot,
      workspaceRevision: 5,
      files: snapshot.files.map((file) => file.path === source.path ? { ...file, size: source.size } : file)
    })

    draft.updateText(source.path, 'print(1)')
    expect(source.isDirty).toBe(true)
    draft.updateText(source.path, 'print(2)')
    expect(source.isDirty).toBe(false)
  })

  it('loads an unchanged binary before moving it to a new path', async () => {
    getWorkspaceFileMock.mockResolvedValue(new Blob([new Uint8Array([1, 2, 3])]))
    const draft = useWorkspaceDraft(ref(snapshot.reportOid))
    draft.initializeFromSnapshot(snapshot)

    await draft.renamePath('resources/logo.png', 'resources/brand/logo.png')

    const moved = draft.files.value.find((file) => file.path === 'resources/brand/logo.png')!
    expect(moved.isDirty).toBe(true)
    expect(moved.content?.size).toBe(3)
    expect(getWorkspaceFileMock).toHaveBeenCalledWith(snapshot.reportOid, 'resources/logo.png')
  })
})
