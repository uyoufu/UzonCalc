export interface ICascadeMenuSeparatorItem {
  type: 'separator'
  name?: string
  inset?: boolean
  spaced?: boolean
}

export interface ICascadeMenuActionItem<T = unknown> {
  type?: 'item'
  name?: string
  label: string
  icon?: string
  disable?: boolean
  closeOnClick?: boolean
  payload?: T
  children?: ICascadeMenuItem<T>[]
  onClick?: (item: ICascadeMenuActionItem<T>) => void | Promise<void>
}

export type ICascadeMenuItem<T = unknown> = ICascadeMenuSeparatorItem | ICascadeMenuActionItem<T>
