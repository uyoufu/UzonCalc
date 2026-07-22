import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { BuildStatus, PublishState, type WorkspaceSnapshot } from 'src/api/calc/types'
import {
  buildWorkspaceTree,
  createDefaultWorkspaceFiles,
  normalizeWorkspaceDirectoryPath,
  normalizeWorkspacePath,
  useWorkspaceDraft
} from 'src/pages/calcReport/workbench/workspace/useWorkspaceDraft'

const getWorkspaceFileMock = vi.hoisted(() => vi.fn())
vi.mock('src/api/calc/workspace', () => ({ getWorkspaceFile: getWorkspaceFileMock }))

const snapshot: WorkspaceSnapshot = {
  reportOid: '67abcdefabcdefabcdefabcd',
  workspaceRevision: 4,
  workspaceHash: `sha256:${'1'.repeat(64)}`,
  entryPath: 'main.py',
  formatVersion: 2,
  files: [
    { path: 'calcbook.json', size: 47, sha256: `sha256:${'2'.repeat(64)}` },
    { path: '__init__.py', size: 0, sha256: `sha256:${'5'.repeat(64)}` },
    { path: 'main.py', size: 10, sha256: `sha256:${'3'.repeat(64)}` },
    { path: 'assets/logo.png', size: 3, sha256: `sha256:${'4'.repeat(64)}` }
  ],
  dependencies: [],
  buildStatus: BuildStatus.NotRequested,
  publishState: PublishState.Unpublished
}

describe('workspace draft', () => {
  it('normalizes root paths and rejects traversal or runtime-reserved paths', () => {
    expect(normalizeWorkspacePath('/main.py/')).toBe('main.py')
    expect(normalizeWorkspacePath('assets/logo.png')).toBe('assets/logo.png')
    expect(() => normalizeWorkspacePath('../main.py')).toThrow()
    expect(() => normalizeWorkspacePath('__uzon_deps__/value.py')).toThrow()
  })

  it('derives folders from files without persisting empty directories', () => {
    const tree = buildWorkspaceTree(createDefaultWorkspaceFiles())
    expect(tree.map((node) => node.path)).toEqual(['calcbook.json', '__init__.py', 'main.py'])
  })

  it('shows session directories without serializing them into the workspace snapshot', () => {
    expect(normalizeWorkspaceDirectoryPath('/helpers/')).toBe('helpers')

    const draft = useWorkspaceDraft(ref(snapshot.reportOid))
    draft.initializeFromSnapshot(snapshot)
    draft.addDirectory('helpers')

    expect(draft.treeNodes.value.find((node) => node.path === 'helpers')?.kind).toBe('folder')
    expect(draft.hasUnsavedChanges.value).toBe(false)
    expect(draft.buildSavePayload().snapshot.files.some((file) => file.path === 'helpers')).toBe(false)
  })

  it('renames and deletes session-only directories with their descendants', async () => {
    const draft = useWorkspaceDraft(ref(snapshot.reportOid))
    draft.initializeFromSnapshot(snapshot)
    draft.addDirectory('helpers/internal')

    await draft.renamePath('helpers', 'shared')
    expect(draft.directories.value).toEqual(['shared/internal'])

    draft.deletePath('shared')
    expect(draft.directories.value).toEqual([])
  })

  it('rejects file and directory path collisions before saving', () => {
    const draft = useWorkspaceDraft(ref(snapshot.reportOid))
    draft.initializeFromSnapshot(snapshot)
    draft.addDirectory('helpers')

    expect(() => draft.addFile('helpers', '')).toThrow()
    expect(() => draft.addDirectory('main.py/child')).toThrow()
  })

  it('builds current descriptors for unchanged files and uploads changed files', async () => {
    getWorkspaceFileMock.mockResolvedValue(new Blob(['print(1)']))
    const draft = useWorkspaceDraft(ref(snapshot.reportOid))
    draft.initializeFromSnapshot(snapshot)
    const source = draft.files.value.find((file) => file.path === 'main.py')!
    await draft.ensureFileLoaded(source)
    draft.updateText(source.path, 'print(2)')

    const payload = draft.buildSavePayload()
    expect(payload.snapshot.workspaceRevision).toBe(4)
    expect(payload.snapshot.files.find((file) => file.path === 'main.py')?.source).toBe('upload')
    expect(payload.snapshot.files.find((file) => file.path === 'assets/logo.png')?.source).toBe('current')
    expect(payload.uploads).toHaveLength(1)
  })

  it('clears text dirty state when editor undo restores synchronized content', async () => {
    getWorkspaceFileMock.mockResolvedValue(new Blob(['print(1)']))
    const draft = useWorkspaceDraft(ref(snapshot.reportOid))
    draft.initializeFromSnapshot(snapshot)
    const source = draft.files.value.find((file) => file.path === 'main.py')!
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
    const source = draft.files.value.find((file) => file.path === 'main.py')!
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

    await draft.renamePath('assets/logo.png', 'assets/brand/logo.png')

    const moved = draft.files.value.find((file) => file.path === 'assets/brand/logo.png')!
    expect(moved.isDirty).toBe(true)
    expect(moved.content?.size).toBe(3)
    expect(getWorkspaceFileMock).toHaveBeenCalledWith(snapshot.reportOid, 'assets/logo.png')
  })
})
