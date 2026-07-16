/** Component-dialog opener for managed execution details. */

import ExecutionDetailDialog from '../components/ExecutionDetailDialog.vue'
import type { CalcExecution } from 'src/api/calc/types'
import { showComponentDialog } from 'src/components/lowCode/PopupDialog'

/**
 * Create the execution-detail dialog opener.
 *
 * @returns Function that displays one immutable execution record.
 */
export function useExecutionDetailDialog() {
  /** Display one execution until the user dismisses the dialog. */
  async function openExecutionDetailDialog(execution: CalcExecution): Promise<void> {
    await showComponentDialog(ExecutionDetailDialog, { execution })
  }

  return { openExecutionDetailDialog }
}

