import { computed, type ComputedRef } from 'vue'
import { t, tGlobal } from 'src/i18n/helpers'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type { ICalcReportInfo } from 'src/api/calcReport'
import { copyCalcReport, deleteCalcReport, updateCalcReport } from 'src/api/calcReport'
import { confirmOperation, notifyError, notifySuccess } from 'src/utils/dialog'
import type { deleteRowByIdType } from 'src/compositions/qTableUtils'
import type { ILowCodeField, IPopupDialogParams } from 'src/components/lowCode/types'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { useEditCalcReportNavigator } from '../../edit/useEditCalcReportNavigator'
import { useCalcReportViewerNavigator } from '../../viewer/useCalcReportViewerNavigator'
import { useCalcListStore } from '../compositions/useCalcListStore'
import { showCalcReportInExplorer } from 'src/api/desktop'

import { useSystemInfo } from 'src/stores/system'

const COPY_REPORT_NAME_SUFFIX = '_副本'

export function useContextMenu(
  categoryOid: ComputedRef<string>,
  deleteRowByIdFn: deleteRowByIdType
) {
  const { navigateToEditCalcReport } = useEditCalcReportNavigator()
  const { navigateToCalcReportViewer } = useCalcReportViewerNavigator()
  const { calcListUpdateSignal } = useCalcListStore()
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
        label: t('calcReportPage.list.modifyInfo'),
        onClick: onModifyCalcReport
      },
      {
        name: 'modifyReportSourceCode',
        label: t('calcReportPage.list.modifyReportSourceCode'),
        onClick: onModifyReportSourceCode
      },
      {
        name: 'copy',
        label: t('calcReportPage.list.copy'),
        onClick: onCopyCalcReport
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
   * 复制计算报告
   */
  async function onCopyCalcReport(report: ICalcReportInfo) {
    const popupParams: IPopupDialogParams = {
      title: t('calcReportPage.list.copyReport'),
      fields: [
        {
          name: 'name',
          label: t('calcReportPage.list.reportName'),
          value: `${report.name}${COPY_REPORT_NAME_SUFFIX}`,
          type: LowCodeFieldType.text,
          required: true
        }
      ],
      oneColumn: true
    }

    const result = await showDialog<{ name: string }>(popupParams)
    if (!result.ok) return

    const name = result.data.name.trim()
    if (!name) {
      notifyError('calcReportPage.list.reportNameRequired')
      return false
    }

    // 后端会复制数据库记录和源码文件，完成后统一刷新列表与分类计数
    await copyCalcReport(report.oid, { name })
    calcListUpdateSignal.value++

    notifySuccess(t('calcReportPage.list.copyReportSuccess'))
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
