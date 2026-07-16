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
 * @returns Functions that resolve true only after successful submission.
 */
export function useInstanceListDialogs() {
  const validateNonBlank = createNonBlankValidator(t('calcWorkspace.metadataRequired'))

  /** Open instance-category creation or editing. */
  async function openCategoryDialog(
    category: CalcInstanceCategory | undefined,
    onSubmit: (input: CategoryInput) => Promise<void>
  ): Promise<boolean> {
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
      ],
      onOkMain: async (values) => {
        await onSubmit({ name: String(values.name), description: String(values.description || '') })
      }
    })
    return result.ok
  }

  /** Open instance metadata editing. */
  async function openInstanceDialog(
    instance: CalcInstance,
    categoryOptions: DialogSelectOption[],
    onSubmit: (input: InstanceMetadataInput) => Promise<void>
  ): Promise<boolean> {
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
      ],
      onOkMain: async (values) => {
        await onSubmit({
          categoryOid: String(values.categoryOid),
          name: String(values.name),
          description: String(values.description || '')
        })
      }
    })
    return result.ok
  }

  return { openCategoryDialog, openInstanceDialog }
}

