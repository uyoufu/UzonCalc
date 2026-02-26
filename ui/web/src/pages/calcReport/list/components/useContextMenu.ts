import { computed, type ComputedRef } from 'vue'
import { t, tGlobal } from 'src/i18n/helpers'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type { ICalcReportInfo } from 'src/api/calcReport'
import { deleteCalcReport, updateCalcReport } from 'src/api/calcReport'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'
import type { deleteRowByIdType } from 'src/compositions/qTableUtils'
import type { ILowCodeField, IPopupDialogParams } from 'src/components/lowCode/types'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { useEditCalcReportNavigator } from '../../edit/useEditCalcReportNavigator'
import { useCalcReportViewerNavigator } from '../../viewer/useCalcReportViewerNavigator'
import { showCalcReportInExplorer } from 'src/api/desktop'

import { useSystemInfo } from 'src/stores/system'

export function useContextMenu(categoryOid: ComputedRef<string>, deleteRowByIdFn: deleteRowByIdType) {
  const { navigateToEditCalcReport } = useEditCalcReportNavigator()
  const { navigateToCalcReportViewer } = useCalcReportViewerNavigator()
  const systemInfoStore = useSystemInfo()

  /**
   * 构建计算报告的编辑字段
   */
  function buildCalcReportFields(report: ICalcReportInfo): ILowCodeField[] {
    const fields: ILowCodeField[] = [
      {
        name: 'name',
        label: t('calcReportPage.list.reportName'),
        value: report.name,
        type: LowCodeFieldType.text,
        required: true
      },
      {
        name: 'description',
        label: t('calcReportPage.list.reportDescription'),
        value: report.description || '',
        type: LowCodeFieldType.textarea
      }
    ]

    return fields
  }

  const itemContextMenuItems: ComputedRef<IContextMenuItem<ICalcReportInfo>[]> = computed(() => {
    const items: IContextMenuItem<ICalcReportInfo>[] = [
      {
        name: 'view',
        label: tGlobal('view'),
        onClick: onViewCalcReport
      },
      {
        name: 'modify',
        label: tGlobal('modify'),
        onClick: onModifyCalcReport
      },
      {
        name: 'modifyReportSourceCode',
        label: t('calcReportPage.list.modifyReportSourceCode'),
        onClick: onModifyReportSourceCode
      },
      {
        name: 'showInFileExplorer',
        label: t('calcReportPage.list.showInFileExplorer'),
        onClick: onShowInFileExplorer,
        vif: () => systemInfoStore.isLocalhost
      },
      {
        name: 'delete',
        label: tGlobal('delete'),
        color: 'negative',
        onClick: onDeleteCalcReport
      }
    ]

    return items
  })

  /**
   * 查看计算报告
   */
  async function onViewCalcReport(report: ICalcReportInfo) {
    await navigateToCalcReportViewer(report.oid, report.name)
  }

  async function onModifyReportSourceCode(report: ICalcReportInfo) {
    await navigateToEditCalcReport(report.oid, categoryOid.value, report.name)
  }

  /**
   * 在文件资源管理器中显示源码文件
   */
  async function onShowInFileExplorer(report: ICalcReportInfo) {
    await showCalcReportInExplorer(report.oid)
  }

  /**
   * 修改计算报告
   */
  async function onModifyCalcReport(report: ICalcReportInfo) {
    const popupParams: IPopupDialogParams = {
      title: t('calcReportPage.list.modifyReport'),
      fields: buildCalcReportFields(report),
      oneColumn: true
    }

    const result = await showDialog<{ name: string; description: string }>(popupParams)
    if (!result.ok) return

    // 调用 API 更新报告
    const response = await updateCalcReport(report.oid, {
      name: result.data.name,
      description: result.data.description,
      categoryId: report.categoryId,
      cover: report.cover
    })

    // 更新本地数据
    report.name = response.data.name
    report.description = response.data.description

    notifySuccess(t('calcReportPage.list.modifyReportSuccess'))
  }

  /**
   * 删除计算报告
   */
  async function onDeleteCalcReport(report: ICalcReportInfo) {
    // 进行确认
    const confirm = await confirmOperation(
      tGlobal('deleteConfirmation'),
      t('calcReportPage.list.deleteReportConfirm', { name: report.name })
    )
    if (!confirm) return

    // 向服务器请求删除
    await deleteCalcReport(report.oid)

    // 刷新表格
    deleteRowByIdFn(report.id)

    notifySuccess(tGlobal('deleteSuccess'))
  }

  return {
    onViewCalcReport,
    itemContextMenuItems
  }
}
