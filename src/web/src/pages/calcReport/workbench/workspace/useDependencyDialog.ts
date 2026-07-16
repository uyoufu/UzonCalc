/** Component-dialog opener for workspace dependency editing. */

import DependencyDialog from './DependencyDialog.vue'
import type { ReportDependency } from 'src/api/calc/types'
import { showComponentDialog } from 'src/components/lowCode/PopupDialog'

/**
 * Create the workspace dependency dialog opener.
 *
 * @returns Function that returns confirmed dependencies or null after cancellation.
 */
export function useDependencyDialog() {
  /** Open dependency editing with a detached copy of the current value. */
  async function openDependencyDialog(
    reportOid: string,
    dependencies: ReportDependency[]
  ): Promise<ReportDependency[] | null> {
    const result = await showComponentDialog<ReportDependency[]>(DependencyDialog, {
      reportOid,
      dependencies
    })
    return result.ok ? result.data : null
  }

  return { openDependencyDialog }
}

