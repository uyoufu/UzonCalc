/** Own the context-menu presentation for calculation workspace tabs. */

import type { IContextMenuItem } from 'src/components/contextMenu/types'
import { t } from 'src/i18n/helpers'
import { WorkspaceTabKind, type WorkspaceTab } from './useWorkspaceTabs'

export const WorkspaceTabMenuCommand = {
  Close: 'close',
  CloseOthers: 'close-others',
  CloseAll: 'close-all',
  CopyReference: 'copy-reference'
} as const
export type WorkspaceTabMenuCommand = typeof WorkspaceTabMenuCommand[keyof typeof WorkspaceTabMenuCommand]

/**
 * Create the fixed VS Code-style tab context-menu commands.
 *
 * @param onCommand Receives the selected command and target tab.
 * @param canCopyReference Returns whether the target has a valid import context.
 * @returns Context-menu items ready for the shared menu component.
 * @throws This function does not throw; command failures belong to the owner.
 */
export function useWorkspaceTabContextMenu(
  onCommand: (command: WorkspaceTabMenuCommand, tab: WorkspaceTab) => void | Promise<void>,
  canCopyReference: (tab: WorkspaceTab) => boolean = () => true
): IContextMenuItem<WorkspaceTab>[] {
  return [
    {
      name: WorkspaceTabMenuCommand.Close,
      label: t('calcWorkspace.close'),
      icon: 'close',
      onClick: (tab) => onCommand(WorkspaceTabMenuCommand.Close, tab)
    },
    {
      name: WorkspaceTabMenuCommand.CloseOthers,
      label: t('calcWorkspace.closeOtherTabs'),
      icon: 'tab_unselected',
      onClick: (tab) => onCommand(WorkspaceTabMenuCommand.CloseOthers, tab)
    },
    {
      name: WorkspaceTabMenuCommand.CloseAll,
      label: t('calcWorkspace.closeAllTabs'),
      icon: 'clear_all',
      onClick: (tab) => onCommand(WorkspaceTabMenuCommand.CloseAll, tab)
    },
    {
      name: WorkspaceTabMenuCommand.CopyReference,
      label: t('calcWorkspace.copyReference'),
      icon: 'content_copy',
      vif: (tab) => tab.kind === WorkspaceTabKind.File && Boolean(tab.path) && canCopyReference(tab),
      onClick: (tab) => onCommand(WorkspaceTabMenuCommand.CopyReference, tab)
    }
  ]
}
