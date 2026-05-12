import { computed, type ComputedRef } from 'vue'
import { useRouter } from 'vue-router'
import { t, tGlobal } from 'src/i18n/helpers'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type { ICalcReportInstanceInfo } from 'src/api/calcReportInstance'
import { deleteCalcReportInstance, updateCalcReportInstance } from 'src/api/calcReportInstance'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'
import type { deleteRowByIdType } from 'src/compositions/qTableUtils'
import type { ILowCodeField, IPopupDialogParams } from 'src/components/lowCode/types'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { useInstanceListStore } from '../compositions/useInstanceListStore'

export function useContextMenu(deleteRowByIdFn: deleteRowByIdType) {
  const router = useRouter()
  const { instanceListUpdateSignal } = useInstanceListStore()

  function buildInstanceFields(instance: ICalcReportInstanceInfo): ILowCodeField[] {
    return [
      {
        name: 'name',
        label: t('calcReportInstancePage.list.instanceName'),
        value: instance.name,
        type: LowCodeFieldType.text,
        required: true
      },
      {
        name: 'description',
        label: t('calcReportInstancePage.list.instanceDescription'),
        value: instance.description || '',
        type: LowCodeFieldType.textarea
      }
    ]
  }

  const itemContextMenuItems: ComputedRef<IContextMenuItem<ICalcReportInstanceInfo>[]> = computed(() => [
    {
      name: 'view',
      label: tGlobal('view'),
      onClick: onViewCalcReportInstance
    },
    {
      name: 'modify',
      label: t('calcReportInstancePage.list.modifyInfo'),
      onClick: onModifyCalcReportInstance
    },
    {
      name: 'delete',
      label: tGlobal('delete'),
      color: 'negative',
      onClick: onDeleteCalcReportInstance
    }
  ])

  async function onViewCalcReportInstance(instance: ICalcReportInstanceInfo) {
    await router.push({
      name: 'calcReportViewer',
      query: {
        instanceOid: instance.oid,
        tagName: instance.name,
        __cacheKey: instance.oid
      }
    })
  }

  async function onModifyCalcReportInstance(instance: ICalcReportInstanceInfo) {
    const popupParams: IPopupDialogParams = {
      title: t('calcReportInstancePage.list.modifyInstance'),
      fields: buildInstanceFields(instance),
      oneColumn: true
    }

    const result = await showDialog<{ name: string; description: string }>(popupParams)
    if (!result.ok) return

    const response = await updateCalcReportInstance(instance.oid, {
      name: result.data.name,
      description: result.data.description,
      categoryId: instance.categoryId
    })
    instance.name = response.data.name
    instance.description = response.data.description
    notifySuccess(t('calcReportInstancePage.list.modifyInstanceSuccess'))
  }

  async function onDeleteCalcReportInstance(instance: ICalcReportInstanceInfo) {
    const confirm = await confirmOperation(
      tGlobal('deleteConfirmation'),
      t('calcReportInstancePage.list.deleteInstanceConfirm', { name: instance.name })
    )
    if (!confirm) return

    await deleteCalcReportInstance(instance.oid)
    deleteRowByIdFn(instance.id)
    instanceListUpdateSignal.value++
    notifySuccess(tGlobal('deleteSuccess'))
  }

  return {
    itemContextMenuItems,
    onViewCalcReportInstance
  }
}
