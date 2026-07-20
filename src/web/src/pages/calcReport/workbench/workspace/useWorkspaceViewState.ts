/** Persist complete workspace view state locally and synchronize it to the server. */

import { ref, watch, type Ref } from 'vue'
import { getUserSetting, upsertUserSetting } from 'src/api/userSetting'
import { WorkspaceTabKind, type WorkspaceTab } from './useWorkspaceTabs'
import type { WorkspaceTreeNode } from './useWorkspaceDraft'

const WORKSPACE_VIEW_STORAGE_PREFIX = 'uzoncalc.calcReport.workspaceView.v2:'

interface StoredWorkspaceViewState {
  expandedPaths: string[]
  selectedPath: string | null
  tabs: WorkspaceTab[]
  activeTabId: string
  isTreeVisible: boolean
}

/** Create local-first, server-synchronized workspace view state. */
export function useWorkspaceViewState(
  reportOid: Ref<string>,
  tabs: Ref<WorkspaceTab[]>,
  activeTabId: Ref<string>
) {
  const expandedPaths = ref<string[]>([])
  const selectedPath = ref('')
  const isTreeVisible = ref(true)
  const isRestored = ref(false)
  let serverSyncTimer: ReturnType<typeof setTimeout> | undefined

  /** Restore valid paths and tabs, preferring browser state over server state. */
  async function restoreViewState(nodes: WorkspaceTreeNode[], entryPath: string): Promise<StoredWorkspaceViewState> {
    const localState = readLocalViewState(reportOid.value)
    const serverValue = localState ? null : (await getUserSetting(storageKey(reportOid.value))).data
    const state = localState || parseViewState(serverValue)
    const filePaths = new Set(nodes.filter((node) => node.kind === 'file').map((node) => node.path))
    const directoryPaths = new Set(nodes.filter((node) => node.kind === 'folder').map((node) => node.path))
    selectedPath.value = state?.selectedPath && filePaths.has(state.selectedPath) ? state.selectedPath : entryPath
    expandedPaths.value = state
      ? state.expandedPaths.filter((path) => directoryPaths.has(path))
      : parentPaths(selectedPath.value).filter((path) => directoryPaths.has(path))
    isTreeVisible.value = state?.isTreeVisible ?? true
    const restoredTabs = (state?.tabs || []).filter((tab) =>
      tab.kind === WorkspaceTabKind.Run || Boolean(tab.path && filePaths.has(tab.path)))
    const result: StoredWorkspaceViewState = {
      expandedPaths: expandedPaths.value,
      selectedPath: selectedPath.value,
      tabs: restoredTabs,
      activeTabId: state?.activeTabId || restoredTabs[0]?.id || '',
      isTreeVisible: isTreeVisible.value
    }
    isRestored.value = true
    persistViewState()
    return result
  }

  /** Rewrite remembered paths after a file or directory rename. */
  function renameViewPath(oldPath: string, newPath: string): void {
    if (selectedPath.value === oldPath || selectedPath.value.startsWith(`${oldPath}/`)) {
      selectedPath.value = `${newPath}${selectedPath.value.slice(oldPath.length)}`
    }
    expandedPaths.value = expandedPaths.value.map((path) => path === oldPath || path.startsWith(`${oldPath}/`)
      ? `${newPath}${path.slice(oldPath.length)}`
      : path)
  }

  /** Remove remembered paths deleted from the workspace tree. */
  function removeViewPath(path: string): void {
    expandedPaths.value = expandedPaths.value.filter((candidate) => candidate !== path && !candidate.startsWith(`${path}/`))
    if (selectedPath.value === path || selectedPath.value.startsWith(`${path}/`)) selectedPath.value = ''
  }

  /** Save immediately in the browser and debounce the server synchronization. */
  function persistViewState(): void {
    if (!isRestored.value || typeof window === 'undefined') return
    const state: StoredWorkspaceViewState = {
      expandedPaths: [...new Set(expandedPaths.value)],
      selectedPath: selectedPath.value || null,
      tabs: tabs.value.map((tab) => ({ ...tab })),
      activeTabId: activeTabId.value,
      isTreeVisible: isTreeVisible.value
    }
    window.localStorage.setItem(storageKey(reportOid.value), JSON.stringify(state))
    clearTimeout(serverSyncTimer)
    serverSyncTimer = setTimeout(() => {
      void upsertUserSetting(storageKey(reportOid.value), { value: state as unknown as Record<string, unknown> })
    }, 500)
  }

  watch([expandedPaths, selectedPath, tabs, activeTabId, isTreeVisible], persistViewState, { deep: true })
  return { expandedPaths, selectedPath, isTreeVisible, restoreViewState, renameViewPath, removeViewPath }
}

/** Read a complete stored state from browser storage. */
function readLocalViewState(reportOid: string): StoredWorkspaceViewState | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(storageKey(reportOid))
    return raw ? parseViewState(JSON.parse(raw)) : null
  } catch {
    return null
  }
}

/** Validate unknown local or server JSON as a workspace view state. */
function parseViewState(value: unknown): StoredWorkspaceViewState | null {
  if (!value || typeof value !== 'object') return null
  const state = value as Partial<StoredWorkspaceViewState>
  if (!Array.isArray(state.expandedPaths) || !state.expandedPaths.every((path) => typeof path === 'string')) return null
  if (state.selectedPath !== null && typeof state.selectedPath !== 'string') return null
  if (!Array.isArray(state.tabs) || !state.tabs.every((tab) => tab && typeof tab.id === 'string' && (tab.kind === WorkspaceTabKind.File || tab.kind === WorkspaceTabKind.Run))) return null
  return {
    expandedPaths: state.expandedPaths,
    selectedPath: state.selectedPath || null,
    tabs: state.tabs,
    activeTabId: typeof state.activeTabId === 'string' ? state.activeTabId : '',
    isTreeVisible: state.isTreeVisible !== false
  }
}

/** Build the shared browser/server setting key for one report. */
function storageKey(reportOid: string): string {
  return `${WORKSPACE_VIEW_STORAGE_PREFIX}${reportOid}`
}

/** Return every parent path of a selected workspace file. */
function parentPaths(path: string): string[] {
  const parts = path.split('/')
  return parts.slice(0, -1).map((_part, index) => parts.slice(0, index + 1).join('/'))
}
