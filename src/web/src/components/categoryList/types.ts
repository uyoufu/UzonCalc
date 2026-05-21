export interface ICategoryInfo {
  name: string
  oid: string
  order: number

  id?: number
  userId?: number
  description?: string
  createdAt?: string
  status?: number
  total?: number

  active?: boolean
  icon?: string
  selectable?: boolean
  selected?: boolean
}

export interface IFlatHeader {
  label: string
  icon: string
}

export type getCategoriesFunc = () => Promise<ICategoryInfo[]>

export type createCategoryFunc = (data: ICategoryInfo) => Promise<ICategoryInfo>

export type updateCategoryFunc = (data: ICategoryInfo) => Promise<ICategoryInfo>

export type deleteCategoryByIdFunc = (id: string) => Promise<void>
