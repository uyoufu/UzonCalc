/** Persist the file-tree view state for one report in the current browser. */

import { ref, watch, type Ref } from 'vue'
import type { WorkspaceTreeNode } from './useWorkspaceDraft'

const WORKSPACE_VIEW_STORAGE_PREFIX = 'uzoncalc.calcReport.workspaceView.v1:'

interface StoredWorkspaceViewState {
  expandedPaths: string[]
  selectedPath: string | null
}

/** Create browser-persisted tree expansion and file-selection state. */
export function useWorkspaceViewState(reportOid: Ref<string>) {
  const expandedPaths = ref<string[]>([])
  const selectedPath = ref('')
  const isRestored = ref(false)

  /** Restore valid paths and fall back to the workspace entry file. */
  function restoreViewState(nodes: WorkspaceTreeNode[], entryPath: string): void {
    const state = readStoredViewState(reportOid.value)
    const filePaths = new Set(nodes.filter((node) => node.kind === 'file').map((node) => node.path))
    const directoryPaths = new Set(nodes.filter((node) => node.kind === 'folder').map((node) => node.path))
    selectedPath.value = state?.selectedPath && filePaths.has(state.selectedPath) ? state.selectedPath : entryPath
    expandedPaths.value = state
      ? state.expandedPaths.filter((path) => directoryPaths.has(path))
      : parentPaths(selectedPath.value).filter((path) => directoryPaths.has(path))
    isRestored.value = true
    persistViewState()
  }

  /** Rewrite remembered paths after a file or directory rename. */
  function renameViewPath(oldPath: string, newPath: string): void {
    if (selectedPath.value === oldPath || selectedPath.value.startsWith(`${oldPath}/`)) {
      selectedPath.value = `${newPath}${selectedPath.value.slice(oldPath.length)}`
    }
    expandedPaths.value = expandedPaths.value.map((path) => {
      if (path === oldPath || path.startsWith(`${oldPath}/`)) return `${newPath}${path.slice(oldPath.length)}`
      return path
    })
  }

  /** Remove remembered paths deleted from the workspace tree. */
  function removeViewPath(path: string): void {
    expandedPaths.value = expandedPaths.value.filter((candidate) => candidate !== path && !candidate.startsWith(`${path}/`))
    if (selectedPath.value === path || selectedPath.value.startsWith(`${path}/`)) selectedPath.value = ''
  }

  /** Persist the current state after restoration has completed. */
  function persistViewState(): void {
    if (!isRestored.value || typeof window === 'undefined') return
    const state: StoredWorkspaceViewState = {
      expandedPaths: [...new Set(expandedPaths.value)],
      selectedPath: selectedPath.value || null
    }
    window.localStorage.setItem(storageKey(reportOid.value), JSON.stringify(state))
  }

  watch([expandedPaths, selectedPath], persistViewState, { deep: true })

  return {
    expandedPaths,
    selectedPath,
    restoreViewState,
    renameViewPath,
    removeViewPath
  }
}

/** Read and validate a stored workspace view state. */
function readStoredViewState(reportOid: string): StoredWorkspaceViewState | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(storageKey(reportOid))
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<StoredWorkspaceViewState>
    if (!Array.isArray(parsed.expandedPaths) || !parsed.expandedPaths.every((path) => typeof path === 'string')) return null
    if (parsed.selectedPath !== null && typeof parsed.selectedPath !== 'string') return null
    return { expandedPaths: parsed.expandedPaths, selectedPath: parsed.selectedPath || null }
  } catch {
    return null
  }
}

/** Build a stable local-storage key for one report. */
function storageKey(reportOid: string): string {
  return `${WORKSPACE_VIEW_STORAGE_PREFIX}${reportOid}`
}

/** Return every parent path of a selected workspace file. */
function parentPaths(path: string): string[] {
  const parts = path.split('/')
  return parts.slice(0, -1).map((_part, index) => parts.slice(0, index + 1).join('/'))
}
