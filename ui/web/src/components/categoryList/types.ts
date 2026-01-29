export interface ICategoryInfo {
  name: string,
  oid: string,
  id?: number,
  userId?: number,
  order: number,
  description?: string,
  createdAt?: string,
  status?: number,
  total?: number,

  active?: boolean,
  icon?: string,
  selectable?: boolean,
  selected?: boolean
}

export interface IFlatHeader {
  label: string,
  icon: string
}

export type getCategoriesFunc = () => Promise<ICategoryInfo[]>

export type createCategoryFunc = (data: ICategoryInfo) => Promise<ICategoryInfo>

export type updateCategoryFunc = (data: ICategoryInfo) => Promise<ICategoryInfo>

export type deleteCategoryByIdFunc = (id: string) => Promise<void>
