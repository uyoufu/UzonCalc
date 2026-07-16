/** Dialog workflows for report categories, report metadata, and UZC imports. */

import ImportUzcDialog from '../components/ImportUzcDialog.vue'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import type { CalcReport, CalcReportCategory } from 'src/api/calc/types'
import type { CategoryInput } from 'src/api/calc/categories'
import type { ReportMetadataInput } from 'src/api/calc/reports'
import { showComponentDialog, showDialog } from 'src/components/lowCode/PopupDialog'
import { t } from 'src/i18n/helpers'
import { createNonBlankValidator, type DialogSelectOption } from '../../shared/dialogForm'

export type ReportDialogMode = 'edit' | 'copy'

export interface ImportUzcDialogInput {
  categoryOid: string
  name: string
  archive: File
}

/**
 * Create report-list dialog openers.
 *
 * @returns Functions that resolve normalized dialog input or null after cancellation.
 */
export function useCalcReportListDialogs() {
  const requiredMessage = t('calcWorkspace.metadataRequired')
  const validateNonBlank = createNonBlankValidator(requiredMessage)

  /** Open report-category creation or editing. */
  async function openCategoryDialog(
    category: CalcReportCategory | undefined
  ): Promise<CategoryInput | null> {
    const result = await showDialog<CategoryInput>({
      title: category ? t('calcWorkspace.editCategory') : t('calcWorkspace.newCategory'),
      oneColumn: true,
      persistent: false,
      fields: [
        {
          name: 'name',
          label: t('calcWorkspace.categoryName'),
          type: LowCodeFieldType.text,
          value: category?.name || '',
          required: true,
          autofocus: true,
          validate: validateNonBlank
        },
        {
          name: 'description',
          label: t('calcWorkspace.description'),
          type: LowCodeFieldType.textarea,
          value: category?.description || ''
        }
      ]
    })
    if (!result.ok) return null

    return {
      name: String(result.data.name),
      description: String(result.data.description || '')
    }
  }

  /** Open report editing or copy metadata. */
  async function openReportDialog(
    report: CalcReport,
    mode: ReportDialogMode,
    categoryOptions: DialogSelectOption[]
  ): Promise<ReportMetadataInput | null> {
    const result = await showDialog<ReportMetadataInput>({
      title: mode === 'copy' ? t('calcWorkspace.copyReport') : t('calcWorkspace.editMetadata'),
      oneColumn: true,
      persistent: false,
      fields: [
        {
          name: 'categoryOid',
          label: t('calcWorkspace.categoryName'),
          type: LowCodeFieldType.selectOne,
          value: report.categoryOid,
          options: categoryOptions,
          optionLabel: 'label',
          optionValue: 'value',
          emitValue: true,
          mapOptions: true,
          required: true
        },
        {
          name: 'name',
          label: t('calcWorkspace.reportName'),
          type: LowCodeFieldType.text,
          value: mode === 'copy' ? `${report.name} - Copy` : report.name,
          required: true,
          autofocus: true,
          validate: validateNonBlank
        },
        {
          name: 'description',
          label: t('calcWorkspace.description'),
          type: LowCodeFieldType.textarea,
          value: report.description || ''
        }
      ]
    })
    if (!result.ok) return null

    return {
      categoryOid: String(result.data.categoryOid),
      name: String(result.data.name),
      description: String(result.data.description || '')
    }
  }

  /** Open the custom UZC file-import dialog. */
  async function openImportDialog(
    categoryOptions: DialogSelectOption[]
  ): Promise<ImportUzcDialogInput | null> {
    const result = await showComponentDialog<ImportUzcDialogInput>(ImportUzcDialog, {
      categoryOptions
    })
    if (!result.ok) return null

    return {
      categoryOid: String(result.data.categoryOid),
      name: String(result.data.name),
      archive: result.data.archive
    }
  }

  return { openCategoryDialog, openReportDialog, openImportDialog }
}
