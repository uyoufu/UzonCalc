import { useUserInfoStore } from 'src/stores/user'
import { computed } from 'vue'

/**
 * 权限控制
 */
export function usePermission() {
  const store = useUserInfoStore()

  // 是否是管理员
  const isSuperAdmin = computed(() => {
    return hasPermission('*')
  })

  const hasPermission = store.hasPermission.bind(store)
  const hasPermissionOr = store.hasPermissionOr.bind(store)

  /**
   * 是否有专业版权限
   * @returns
   */
  function hasProfessionAccess() {
    if (!store.hasProPlugin) return false
    if (hasEnterpriseAccess()) return true
    return hasPermissionOr(['professional'])
  }

  const isProfession = computed(() => {
    return hasProfessionAccess()
  })

  /**
   * 是否有企业版权限
   * @returns
   */
  function hasEnterpriseAccess() {
    return hasPermission('enterprise')
  }

  const isEnterprise = computed(() => {
    return hasEnterpriseAccess()
  })

  /**
   * 是否是桌面端 API 访问
   */
  const isDesktopApi = computed(() => {
    return hasPermission('desktop-api')
  })

  return {
    hasPermission,
    hasPermissionOr,
    isSuperAdmin,
    hasProfessionAccess,
    hasEnterpriseAccess,
    isProfession,
    isEnterprise,
    isDesktopApi
  }
}
