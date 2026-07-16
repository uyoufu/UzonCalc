/** Component-dialog opener for workspace revision-conflict recovery. */

import WorkspaceConflictDialog from './WorkspaceConflictDialog.vue'
import { showComponentDialog } from 'src/components/lowCode/PopupDialog'
import type { WorkspaceConflictResolution } from './workspaceConflict'

/**
 * Create the workspace-conflict dialog opener.
 *
 * @returns Function that returns the confirmed recovery action or null.
 */
export function useWorkspaceConflictDialog() {
  /** Display recovery choices and return only a confirmed selection. */
  async function openWorkspaceConflictDialog(): Promise<WorkspaceConflictResolution | null> {
    const result = await showComponentDialog<WorkspaceConflictResolution>(WorkspaceConflictDialog)
    return result.ok ? result.data : null
  }

  return { openWorkspaceConflictDialog }
}

