/** Save-instance dialog workflow for completed report executions. */

import { LowCodeFieldType } from 'src/components/lowCode/types'
import { ensureDefaultInstanceCategory, listInstanceCategories } from 'src/api/calc/categories'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { t } from 'src/i18n/helpers'
import { createNonBlankValidator } from '../../calcReport/shared/dialogForm'

interface SaveInstanceInput {
  categoryOid: string
  name: string
  description: string
}

/**
 * Create the completed-execution save dialog opener.
 *
 * @returns Function that lazily prepares categories and returns confirmed metadata.
 */
export function useSaveInstanceDialog() {
  const validateNonBlank = createNonBlankValidator(t('calcWorkspace.metadataRequired'))

  /** Load category options and save the selected execution as an instance. */
  async function openSaveInstanceDialog(suggestedName: string): Promise<SaveInstanceInput | null> {
    let categories = (await listInstanceCategories()).data || []
    if (categories.length === 0) {
      const response = await ensureDefaultInstanceCategory({
        name: t('calcWorkspace.defaultInstanceCategory')
      })
      categories = [response.data]
    }

    const result = await showDialog<SaveInstanceInput>({
      title: t('calcWorkspace.saveInstance'),
      oneColumn: true,
      persistent: false,
      fields: [
        {
          name: 'categoryOid',
          label: t('calcWorkspace.categoryName'),
          type: LowCodeFieldType.selectOne,
          value: categories[0]?.categoryOid || '',
          options: categories.map((category) => ({
            label: category.name,
            value: category.categoryOid
          })),
          optionLabel: 'label',
          optionValue: 'value',
          emitValue: true,
          mapOptions: true,
          required: true
        },
        {
          name: 'name',
          label: t('calcWorkspace.instanceName'),
          type: LowCodeFieldType.text,
          value: suggestedName,
          required: true,
          validate: validateNonBlank
        },
        {
          name: 'description',
          label: t('calcWorkspace.description'),
          type: LowCodeFieldType.textarea,
          value: ''
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

  return { openSaveInstanceDialog }
}
