/** Own fixed saved-instance row commands and their context-menu presentation. */

import type { CalcInstance, CalcInstanceCategory } from 'src/api/calc/types'
import { listInstanceCategories } from 'src/api/calc/categories'
import {
  deleteInstance,
  revokeInstanceShare,
  shareInstance,
  updateInstance
} from 'src/api/calc/instances'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type { deleteRowByIdType, updateExistOneType } from 'src/compositions/qTableUtils'
import { t } from 'src/i18n/helpers'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'
import { useInstanceListDialogs } from '../compositions/useInstanceListDialogs'

export interface InstanceContextMenuOptions {
  categories: Ref<CalcInstanceCategory[]>
  updateInstanceRow: updateExistOneType<CalcInstance>
  deleteInstanceRow: deleteRowByIdType
}

/**
 * Create saved-instance commands and their context-menu items.
 *
 * @param options - Reactive category state and minimum table mutation capabilities.
 * @returns Menu items plus the command reused by the visible instance link.
 * @throws Propagates router, API, confirmation, and dialog errors.
 */
export function useInstanceContextMenu(options: InstanceContextMenuOptions) {
  const router = useRouter()
  const { openInstanceDialog } = useInstanceListDialogs()
  const categoryOptions = computed(() =>
    options.categories.value.map((category) => ({
      label: category.name,
      value: category.categoryOid
    }))
  )

  /**
   * Refresh instance categories after a deletion changes derived counts.
   *
   * @returns A promise that resolves after categories are replaced.
   * @throws Propagates category API errors.
   */
  async function refreshCategories(): Promise<void> {
    const response = await listInstanceCategories()
    options.categories.value = response.data || []
  }

  /**
   * Navigate to the selected saved-instance detail.
   *
   * @param instance - Instance selected by a row control.
   * @returns A promise that resolves after navigation.
   * @throws Propagates router navigation errors.
   */
  async function onOpenInstance(instance: CalcInstance): Promise<void> {
    await router.push(`/calc-report-instance/${instance.instanceOid}`)
  }

  /**
   * Edit saved-instance metadata and patch the confirmed row.
   *
   * @param instance - Instance selected for editing.
   * @returns A promise that resolves after persistence or dialog cancellation.
   * @throws Propagates instance and dialog errors.
   */
  async function onEditInstance(instance: CalcInstance): Promise<void> {
    const input = await openInstanceDialog(instance, categoryOptions.value)
    if (!input) return

    const response = await updateInstance(instance.instanceOid, {
      revision: instance.revision,
      ...input
    })
    options.updateInstanceRow(response.data, 'instanceOid')
  }

  /**
   * Delete a confirmed saved instance and synchronize row and category state.
   *
   * @param instance - Instance selected for deletion.
   * @returns A promise that resolves after deletion or confirmation cancellation.
   * @throws Propagates confirmation, instance, and category errors.
   */
  async function onDeleteInstance(instance: CalcInstance): Promise<void> {
    if (!(await confirmOperation(t('global.deleteConfirmation'), instance.name))) return
    await deleteInstance(instance.instanceOid)
    options.deleteInstanceRow(instance.instanceOid, 'instanceOid')
    await refreshCategories()
  }

  /** Build the stable anonymous frontend URL for an active share token. */
  function buildShareUrl(shareToken: string): string {
    return new URL(`/calc-report-instance/shared/${shareToken}`, window.location.origin).toString()
  }

  /** Enable anonymous access, copy its link, and patch the returned token into the row. */
  async function onShareInstance(instance: CalcInstance): Promise<void> {
    const response = await shareInstance(instance.instanceOid)
    const shareToken = response.data.token
    options.updateInstanceRow({ ...instance, isShared: true, shareToken }, 'instanceOid')
    await navigator.clipboard.writeText(buildShareUrl(shareToken))
    notifySuccess(t('calcWorkspace.instanceShareSucceeded'))
  }

  /** Copy the stable anonymous frontend URL for an active share. */
  async function onCopyShareLink(instance: CalcInstance): Promise<void> {
    if (!instance.shareToken) return
    await navigator.clipboard.writeText(buildShareUrl(instance.shareToken))
    notifySuccess(t('calcWorkspace.linkCopied'))
  }

  /** Revoke anonymous access and patch only the selected row. */
  async function onRevokeShare(instance: CalcInstance): Promise<void> {
    await revokeInstanceShare(instance.instanceOid)
    options.updateInstanceRow({ ...instance, isShared: false, shareToken: null }, 'instanceOid')
    notifySuccess(t('calcWorkspace.instanceShareRevoked'))
  }

  const items: IContextMenuItem<CalcInstance>[] = [
    {
      name: 'open',
      label: t('global.view'),
      icon: 'visibility',
      color: 'grey-9',
      onClick: onOpenInstance
    },
    {
      name: 'edit',
      label: t('global.edit'),
      icon: 'edit',
      color: 'grey-9',
      onClick: onEditInstance
    },
    {
      name: 'share',
      label: t('global.share'),
      icon: 'share',
      color: 'primary',
      vif: (instance) => !instance.isShared,
      onClick: onShareInstance
    },
    {
      name: 'copy-share-link',
      label: t('calcWorkspace.copyShareLink'),
      icon: 'content_copy',
      color: 'primary',
      vif: (instance) => instance.isShared,
      onClick: onCopyShareLink
    },
    {
      name: 'revoke-share',
      label: t('calcWorkspace.revokeShare'),
      icon: 'link_off',
      color: 'warning',
      vif: (instance) => instance.isShared,
      onClick: onRevokeShare
    },
    {
      name: 'delete',
      label: t('global.delete'),
      icon: 'delete',
      color: 'negative',
      onClick: onDeleteInstance
    }
  ]

  return { items, onOpenInstance }
}
