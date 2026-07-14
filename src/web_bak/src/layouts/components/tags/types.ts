import type { LocationQuery } from 'vue-router'
import type { LangKey } from 'src/i18n/types'

/**
 * 路由历史
 */
export interface IRouteHistory {
  id: string, // 全路径 + 查询参数
  fullPath: string,
  query: LocationQuery,
  name: string,
  label: LangKey,
  isActive: boolean,
  icon: string,
  noCache: boolean,
  showCloseIcon: boolean,
}
