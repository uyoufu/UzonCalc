/** Context-menu workflow for importing or exporting catalog shares. */
import type { Ref } from 'vue'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type { CalcReportCategory, SharedReport } from 'src/api/calc/types'
import { exportCatalogShare, importCatalogShare } from 'src/api/calc/shares'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import { notifySuccess, notifyUntil } from 'src/utils/dialog'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { t } from 'src/i18n/helpers'

interface SharedImportInput {
  categoryOid: string
  name: string
  shouldSync: boolean
}

/** Create fixed shared-report row actions. */
export function useSharedReportContextMenu(categories: Ref<CalcReportCategory[]>) {
  /** Select import metadata and persist one catalog import. */
  async function onImportReport(report: SharedReport): Promise<void> {
    const result = await showDialog<SharedImportInput>({
      title: t('calcWorkspace.importSharedReport'),
      oneColumn: true,
      fields: [
        { name: 'categoryOid', label: t('calcWorkspace.categoryName'), type: LowCodeFieldType.selectOne, required: true, value: categories.value[0]?.categoryOid, options: categories.value.map((category) => ({ label: category.name, value: category.categoryOid })), optionLabel: 'label', optionValue: 'value', emitValue: true, mapOptions: true },
        { name: 'name', label: t('calcWorkspace.reportName'), required: true, value: report.reportName },
        { name: 'shouldSync', label: t('calcWorkspace.keepSynchronized'), type: LowCodeFieldType.boolean, value: false }
      ]
    })
    if (!result.ok) return
    await importCatalogShare(report.shareOid, result.data.categoryOid, result.data.name, result.data.shouldSync)
    notifySuccess(t('calcWorkspace.importSucceeded'))
  }

  /** Download a shared report through the same-backend archive endpoint. */
  async function onExportReport(report: SharedReport): Promise<void> {
    const response = await notifyUntil(
      async () => await exportCatalogShare(report.shareOid),
      t('calcWorkspace.exportingArchive')
    )
    if (!response) return
    const objectUrl = URL.createObjectURL(response.data)
    const anchor = document.createElement('a')
    anchor.href = objectUrl
    anchor.download = `${report.reportName}.png`
    anchor.click()
    URL.revokeObjectURL(objectUrl)
  }

  const contextMenuItems: IContextMenuItem<SharedReport>[] = [
    { name: 'import', label: t('global.import'), icon: 'download', color: 'primary', onClick: onImportReport },
    { name: 'export', label: t('global.export'), icon: 'upload', color: 'secondary', onClick: onExportReport }
  ]
  return { contextMenuItems }
}
