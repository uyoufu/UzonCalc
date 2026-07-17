/** Manage the session-local tabs shown by one calculation workspace. */

import { computed, ref } from 'vue'

export const WorkspaceTabKind = {
  File: 'file',
  Run: 'run'
} as const
export type WorkspaceTabKind = typeof WorkspaceTabKind[keyof typeof WorkspaceTabKind]

const FILE_TAB_PREFIX = 'workspace-file:'
export const WORKSPACE_RUN_TAB_ID = 'workspace-run'

export interface WorkspaceTab {
  id: string
  kind: WorkspaceTabKind
  path: string | null
}

/** Create the state and operations for workspace tabs. */
export function useWorkspaceTabs() {
  const tabs = ref<WorkspaceTab[]>([])
  const activeTabId = ref('')
  const activeTab = computed(() => tabs.value.find((tab) => tab.id === activeTabId.value) || null)
  const openFilePaths = computed(() => tabs.value.flatMap((tab) => tab.kind === WorkspaceTabKind.File && tab.path ? [tab.path] : []))
  const hasRunTab = computed(() => tabs.value.some((tab) => tab.kind === WorkspaceTabKind.Run))

  /** Open or activate one file tab. */
  function openFileTab(path: string): void {
    const id = fileTabId(path)
    if (!tabs.value.some((tab) => tab.id === id)) {
      tabs.value.push({ id, kind: WorkspaceTabKind.File, path })
    }
    activeTabId.value = id
  }

  /** Open or activate the singleton workspace-run tab. */
  function openRunTab(): void {
    if (!hasRunTab.value) {
      tabs.value.push({ id: WORKSPACE_RUN_TAB_ID, kind: WorkspaceTabKind.Run, path: null })
    }
    activeTabId.value = WORKSPACE_RUN_TAB_ID
  }

  /** Activate an existing tab without changing its order. */
  function activateTab(id: string): void {
    if (tabs.value.some((tab) => tab.id === id)) activeTabId.value = id
  }

  /** Close one tab and activate the nearest remaining neighbor. */
  function closeTab(id: string): WorkspaceTab | null {
    const index = tabs.value.findIndex((tab) => tab.id === id)
    if (index < 0) return activeTab.value
    const wasActive = activeTabId.value === id
    tabs.value.splice(index, 1)
    if (wasActive) {
      activeTabId.value = tabs.value[index]?.id || tabs.value[index - 1]?.id || ''
    }
    return activeTab.value
  }

  /** Rewrite file-tab paths after a file or folder rename. */
  function renamePath(oldPath: string, newPath: string): void {
    tabs.value.forEach((tab) => {
      if (tab.kind !== WorkspaceTabKind.File || !tab.path) return
      if (tab.path !== oldPath && !tab.path.startsWith(`${oldPath}/`)) return
      const oldId = tab.id
      tab.path = `${newPath}${tab.path.slice(oldPath.length)}`
      tab.id = fileTabId(tab.path)
      if (activeTabId.value === oldId) activeTabId.value = tab.id
    })
  }

  /** Remove file tabs deleted with a file or folder. */
  function removePath(path: string): WorkspaceTab | null {
    const removedIds = tabs.value
      .filter((tab) => tab.kind === WorkspaceTabKind.File && tab.path && (tab.path === path || tab.path.startsWith(`${path}/`)))
      .map((tab) => tab.id)
    removedIds.forEach((id) => closeTab(id))
    return activeTab.value
  }

  /** Build the stable tab identifier for a workspace file. */
  function fileTabId(path: string): string {
    return `${FILE_TAB_PREFIX}${path}`
  }

  return {
    tabs,
    activeTabId,
    activeTab,
    openFilePaths,
    hasRunTab,
    openFileTab,
    openRunTab,
    activateTab,
    closeTab,
    renamePath,
    removePath
  }
}
