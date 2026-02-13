import { computed, type ComputedRef } from 'vue'
import { useRouter } from 'vue-router'
import { t, tGlobal } from 'src/i18n/helpers'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type { ICalcReportInfo } from 'src/api/calcReport'
import { deleteCalcReport, updateCalcReport } from 'src/api/calcReport'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'
import type { deleteRowByIdType } from 'src/compositions/qTableUtils'
import type { ILowCodeField, IPopupDialogParams } from 'src/components/lowCode/types'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { generateEditorCacheKey } from './useNewCalcReportRoute'

export function useContextMenu(categoryOid: ComputedRef<string>, deleteRowByIdFn: deleteRowByIdType) {
  const router = useRouter()

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

  const itemContextMenuItems: ComputedRef<IContextMenuItem<ICalcReportInfo>[]> = computed(() => [
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
      name: 'delete',
      label: tGlobal('delete'),
      color: 'negative',
      onClick: onDeleteCalcReport
    }
  ])

  /**
   * 查看计算报告
   */
  async function onViewCalcReport(report: ICalcReportInfo) {
    await router.push({
      name: 'calcReportViewer',
      query: {
        reportOid: report.oid,
        tagName: report.oid.slice(-4),
        __cacheKey: generateEditorCacheKey(report.oid)
      }
    })
  }

  async function onModifyReportSourceCode(report: ICalcReportInfo) {
    await router.push({
      name: 'editCalcReport',
      query: {
        reportOid: report.oid,
        categoryOid: categoryOid.value,
        tagName: report.oid.slice(-4),
        __cacheKey: generateEditorCacheKey(report.oid)
      }
    })
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
