import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import { buildWorkspaceTree, createDefaultWorkspaceFiles } from 'src/pages/calcReport/workbench/workspace/useWorkspaceDraft'
import { useWorkspaceTabs, WorkspaceTabKind, WORKSPACE_RUN_TAB_ID } from 'src/pages/calcReport/workbench/workspace/useWorkspaceTabs'
import { useWorkspaceViewState } from 'src/pages/calcReport/workbench/workspace/useWorkspaceViewState'

vi.mock('src/api/calc/workspace', () => ({ getWorkspaceFile: vi.fn() }))
vi.mock('src/api/userSetting', () => ({
  getUserSetting: vi.fn().mockResolvedValue({ data: null }),
  upsertUserSetting: vi.fn().mockResolvedValue({ data: null })
}))

describe('workspace tabs and view state', () => {
  beforeEach(() => window.localStorage.clear())

  it('opens unique tabs and rewrites paths after rename and delete', () => {
    const tabs = useWorkspaceTabs()
    tabs.openFileTab('src/main.py')
    tabs.openFileTab('src/helpers.py')
    tabs.openFileTab('src/main.py')
    tabs.openRunTab()

    expect(tabs.tabs.value).toHaveLength(3)
    expect(tabs.activeTabId.value).toBe(WORKSPACE_RUN_TAB_ID)

    tabs.renamePath('src', 'src2')
    expect(tabs.openFilePaths.value).toEqual(['src2/main.py', 'src2/helpers.py'])

    tabs.removePath('src2/helpers.py')
    expect(tabs.openFilePaths.value).toEqual(['src2/main.py'])
    expect(tabs.activeTab.value?.kind).toBe(WorkspaceTabKind.Run)
  })

  it('selects the nearest neighbor when the active tab closes', () => {
    const tabs = useWorkspaceTabs()
    tabs.openFileTab('src/main.py')
    tabs.openFileTab('src/helpers.py')

    tabs.closeTab(tabs.activeTabId.value)

    expect(tabs.activeTab.value?.path).toBe('src/main.py')
  })

  it('restores only valid selected and expanded tree paths per report', async () => {
    const reportOid = ref('report-1')
    const nodes = buildWorkspaceTree(createDefaultWorkspaceFiles())
    const firstTabs = useWorkspaceTabs()
    const first = useWorkspaceViewState(reportOid, firstTabs.tabs, firstTabs.activeTabId)
    await first.restoreViewState(nodes, 'src/main.py')
    first.expandedPaths.value = ['src', 'missing']
    first.selectedPath.value = 'calcbook.json'
    await nextTick()

    const restoredTabs = useWorkspaceTabs()
    const restored = useWorkspaceViewState(reportOid, restoredTabs.tabs, restoredTabs.activeTabId)
    await restored.restoreViewState(nodes, 'src/main.py')

    expect(restored.expandedPaths.value).toEqual(['src'])
    expect(restored.selectedPath.value).toBe('calcbook.json')
  })

  it('falls back safely when persisted view state is malformed', async () => {
    const reportOid = ref('report-2')
    window.localStorage.setItem('uzoncalc.calcReport.workspaceView.v2:report-2', '{invalid')
    const tabs = useWorkspaceTabs()
    const state = useWorkspaceViewState(reportOid, tabs.tabs, tabs.activeTabId)

    await state.restoreViewState(buildWorkspaceTree(createDefaultWorkspaceFiles()), 'src/main.py')

    expect(state.selectedPath.value).toBe('src/main.py')
    expect(state.expandedPaths.value).toEqual(['src'])
  })
})
