/** Component-dialog opener for approved-version share-link management. */

import ShareManagerDialog from './ShareManagerDialog.vue'
import { showComponentDialog } from 'src/components/lowCode/PopupDialog'

/**
 * Create the share-manager dialog opener.
 *
 * @returns Function that displays share-link management for one report.
 */
export function useShareManagerDialog() {
  /** Display share-link management until the user dismisses it. */
  async function openShareManagerDialog(reportOid: string, reportName: string): Promise<void> {
    await showComponentDialog(ShareManagerDialog, { reportOid, reportName })
  }

  return { openShareManagerDialog }
}
