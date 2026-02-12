import type { RouteRecordRaw } from 'vue-router'
import type { LangKey } from 'src/i18n/types'

// 为了支持更多路由的 meta 属性，我们需要扩展RouteRecordRaw
export type ExtendedRouteRecordRaw = RouteRecordRaw & {
  meta: {
    label: LangKey // 名称
    icon: string // 图标
    access?: string[] // 访问权限，当有该权限时，才显示，权限是且的关系，即同时具有多个权限才显示
    denies?: string[] // 当有该权限时，拒绝显示，权限是或的关系，即只要有一个权限就不显示, 该值优先于 access
    noTag?: boolean // 是否不显示标签
    // 不缓存页面，默认为 false，若需要缓存，则在组件中使用 defineOptions 定义 name 属性，并且 name 要与文件名一致
    // 更多关于缓存的说明见 readme
    noCache?: boolean
    noMenu?: boolean // 是否不显示菜单
  }
  children?: ExtendedRouteRecordRaw[]
}
