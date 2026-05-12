import { t } from 'src/i18n/helpers'
import type { ICategoryInfo, IFlatHeader } from 'src/components/categoryList/types'
import {
  createCalcReportInstanceCategory,
  deleteCalcReportInstanceCategory,
  getCalcReportInstanceCategories,
  updateCalcReportInstanceCategory
} from 'src/api/calcReportInstanceCategory'

export function useInstanceCategory() {
  const listHeader: IFlatHeader = {
    label: t('calcReportInstancePage.myCalcs'),
    icon: 'list_alt'
  }

  async function onGetCategories(): Promise<ICategoryInfo[]> {
    const result = await getCalcReportInstanceCategories()
    if (result.ok && result.data) return result.data
    return []
  }

  async function onCreateCategory(data: ICategoryInfo): Promise<ICategoryInfo> {
    const result = await createCalcReportInstanceCategory({
      name: data.name,
      order: data.order,
      description: data.description || null
    })
    if (result.ok && result.data) return result.data
    throw new Error(result.message)
  }

  async function onUpdateCategory(data: ICategoryInfo): Promise<ICategoryInfo> {
    const result = await updateCalcReportInstanceCategory(data.oid, {
      name: data.name,
      order: data.order,
      description: data.description
    })
    if (result.ok && result.data) return result.data
    throw new Error(result.message)
  }

  async function onDeleteCategoryById(categoryOid: string): Promise<void> {
    const result = await deleteCalcReportInstanceCategory(categoryOid)
    if (!result.ok) throw new Error(result.message)
  }

  return {
    listHeader,
    onGetCategories,
    onCreateCategory,
    onUpdateCategory,
    onDeleteCategoryById
  }
}
