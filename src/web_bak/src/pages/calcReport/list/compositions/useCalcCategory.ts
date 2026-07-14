import { t } from 'src/i18n/helpers'
import type { ICategoryInfo, IFlatHeader } from 'src/components/categoryList/types'
import {
  createCalcReportCategory,
  deleteCalcReportCategory,
  getCalcReportCategories,
  updateCalcReportCategory
} from 'src/api/calcReportCategory'

export function useCalcCategory() {
  const listHeader: IFlatHeader = {
    label: t('calcReportPage.myCalcs'),
    icon: 'article'
  }

  async function onGetCategories(): Promise<ICategoryInfo[]> {
    const result = await getCalcReportCategories()
    if (result.ok && result.data) {
      return result.data
    }
    return []
  }

  async function onCreateCategory(data: ICategoryInfo): Promise<ICategoryInfo> {
    const result = await createCalcReportCategory({
      name: data.name,
      order: data.order,
      description: data.description || null
    })
    if (result.ok && result.data) {
      return result.data
    }
    throw new Error(result.message)
  }

  async function onUpdateCategory(data: ICategoryInfo): Promise<ICategoryInfo> {
    if (!data.id) {
      throw new Error('Category id is required')
    }
    const result = await updateCalcReportCategory(data.oid, {
      name: data.name,
      order: data.order,
      description: data.description
    })
    if (result.ok && result.data) {
      return result.data
    }
    throw new Error(result.message)
  }

  async function onDeleteCategoryById(categoryOid: string): Promise<void> {
    const result = await deleteCalcReportCategory(categoryOid)
    if (!result.ok) {
      throw new Error(result.message)
    }
  }

  return {
    listHeader,
    onGetCategories,
    onCreateCategory,
    onUpdateCategory,
    onDeleteCategoryById
  }
}
