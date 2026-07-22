import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import { buildWorkspaceTree, createDefaultWorkspaceFiles } from 'src/pages/calcReport/workbench/workspace/useWorkspaceDraft'
import { useWorkspaceTabs, WorkspaceTabKind, WORKSPACE_RUN_TAB_ID } from 'src/pages/calcReport/workbench/workspace/useWorkspaceTabs'
import { useWorkspaceViewState } from 'src/pages/calcReport/workbench/workspace/useWorkspaceViewState'
import { workspaceReferenceForPath } from 'src/pages/calcReport/workbench/workspace/workspaceReference'
import {
  useWorkspaceTabContextMenu,
  WorkspaceTabMenuCommand
} from 'src/pages/calcReport/workbench/workspace/useWorkspaceTabContextMenu'

vi.mock('src/api/calc/workspace', () => ({ getWorkspaceFile: vi.fn() }))
vi.mock('src/api/userSetting', () => ({
  getUserSetting: vi.fn().mockResolvedValue({ data: null }),
  upsertUserSetting: vi.fn().mockResolvedValue({ data: null })
}))
vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key }))

describe('workspace tabs and view state', () => {
  beforeEach(() => window.localStorage.clear())

  it('opens unique tabs and rewrites paths after rename and delete', () => {
    const tabs = useWorkspaceTabs()
    tabs.openFileTab('main.py')
    tabs.openFileTab('package/helpers.py')
    tabs.openFileTab('main.py')
    tabs.openRunTab()

    expect(tabs.tabs.value).toHaveLength(3)
    expect(tabs.activeTabId.value).toBe(WORKSPACE_RUN_TAB_ID)

    tabs.renamePath('package', 'shared')
    expect(tabs.openFilePaths.value).toEqual(['main.py', 'shared/helpers.py'])

    tabs.removePath('shared/helpers.py')
    expect(tabs.openFilePaths.value).toEqual(['main.py'])
    expect(tabs.activeTab.value?.kind).toBe(WorkspaceTabKind.Run)
  })

  it('selects the nearest neighbor when the active tab closes', () => {
    const tabs = useWorkspaceTabs()
    tabs.openFileTab('main.py')
    tabs.openFileTab('helpers.py')

    tabs.closeTab(tabs.activeTabId.value)

    expect(tabs.activeTab.value?.path).toBe('main.py')
  })

  it('closes tab sets atomically and honors the preferred surviving tab', () => {
    const tabs = useWorkspaceTabs()
    tabs.openFileTab('main.py')
    tabs.openFileTab('helpers.py')
    tabs.openRunTab()

    tabs.closeTabs([WORKSPACE_RUN_TAB_ID, 'workspace-file:main.py'], 'workspace-file:helpers.py')

    expect(tabs.openFilePaths.value).toEqual(['helpers.py'])
    expect(tabs.activeTab.value?.path).toBe('helpers.py')
  })

  it('builds package-relative references and exposes the four tab menu commands', async () => {
    expect(workspaceReferenceForPath('utils/index.py', 'main.py')).toBe('from .utils.index import *')
    expect(workspaceReferenceForPath('utils/index.py', 'package/main.py')).toBe('from ..utils.index import *')
    expect(workspaceReferenceForPath('package/helpers.py', 'package/main.py')).toBe('from .helpers import *')
    expect(workspaceReferenceForPath('package/__init__.py', 'package/main.py')).toBe('from . import *')
    expect(workspaceReferenceForPath('__init__.py', 'package/main.py')).toBe('from .. import *')
    expect(workspaceReferenceForPath('main.py', null)).toBeNull()
    expect(workspaceReferenceForPath('assets/logo.png', null)).toBe('assets/logo.png')
    expect(workspaceReferenceForPath('invalid-name.py', 'main.py')).toBe('invalid-name.py')

    const received: Array<[string, string]> = []
    const items = useWorkspaceTabContextMenu((command, tab) => {
      received.push([command, tab.id])
    })
    expect(items.map((item) => item.name)).toEqual([
      WorkspaceTabMenuCommand.Close,
      WorkspaceTabMenuCommand.CloseOthers,
      WorkspaceTabMenuCommand.CloseAll,
      WorkspaceTabMenuCommand.CopyReference
    ])
    await items[0]?.onClick({ id: 'workspace-file:main.py', kind: WorkspaceTabKind.File, path: 'main.py' })
    expect(received).toEqual([[WorkspaceTabMenuCommand.Close, 'workspace-file:main.py']])
  })

  it('restores only valid selected and expanded tree paths per report', async () => {
    const reportOid = ref('report-1')
    const nodes = buildWorkspaceTree(createDefaultWorkspaceFiles())
    const firstTabs = useWorkspaceTabs()
    const first = useWorkspaceViewState(reportOid, firstTabs.tabs, firstTabs.activeTabId)
    await first.restoreViewState(nodes, 'main.py')
    first.expandedPaths.value = ['missing']
    first.selectedPath.value = 'calcbook.json'
    await nextTick()

    const restoredTabs = useWorkspaceTabs()
    const restored = useWorkspaceViewState(reportOid, restoredTabs.tabs, restoredTabs.activeTabId)
    await restored.restoreViewState(nodes, 'main.py')

    expect(restored.expandedPaths.value).toEqual([])
    expect(restored.selectedPath.value).toBe('calcbook.json')
  })

  it('falls back safely when persisted view state is malformed', async () => {
    const reportOid = ref('report-2')
    window.localStorage.setItem('uzoncalc.calcReport.workspaceView.v2:report-2', '{invalid')
    const tabs = useWorkspaceTabs()
    const state = useWorkspaceViewState(reportOid, tabs.tabs, tabs.activeTabId)

    await state.restoreViewState(buildWorkspaceTree(createDefaultWorkspaceFiles()), 'main.py')

    expect(state.selectedPath.value).toBe('main.py')
    expect(state.expandedPaths.value).toEqual([])
  })
})
