/** Dialog workflows for saved-instance categories and instance metadata. */

import { LowCodeFieldType } from 'src/components/lowCode/types'
import type { CalcInstance, CalcInstanceCategory } from 'src/api/calc/types'
import type { CategoryInput } from 'src/api/calc/categories'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { t } from 'src/i18n/helpers'
import {
  createNonBlankValidator,
  type DialogSelectOption
} from '../../../calcReport/shared/dialogForm'

export interface InstanceMetadataInput {
  categoryOid: string
  name: string
  description: string
}

/**
 * Create saved-instance dialog openers.
 *
 * @returns Functions that resolve normalized dialog input or null after cancellation.
 */
export function useInstanceListDialogs() {
  const validateNonBlank = createNonBlankValidator(t('calcWorkspace.metadataRequired'))

  /** Open instance-category creation or editing. */
  async function openCategoryDialog(
    category: CalcInstanceCategory | undefined
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

  /** Open instance metadata editing. */
  async function openInstanceDialog(
    instance: CalcInstance,
    categoryOptions: DialogSelectOption[]
  ): Promise<InstanceMetadataInput | null> {
    const result = await showDialog<InstanceMetadataInput>({
      title: t('calcWorkspace.editInstance'),
      oneColumn: true,
      persistent: false,
      fields: [
        {
          name: 'categoryOid',
          label: t('calcWorkspace.categoryName'),
          type: LowCodeFieldType.selectOne,
          value: instance.categoryOid,
          options: categoryOptions,
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
          value: instance.name,
          required: true,
          validate: validateNonBlank
        },
        {
          name: 'description',
          label: t('calcWorkspace.description'),
          type: LowCodeFieldType.textarea,
          value: instance.description || ''
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

  return { openCategoryDialog, openInstanceDialog }
}
