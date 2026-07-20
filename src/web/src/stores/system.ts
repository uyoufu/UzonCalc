import { defineStore } from 'pinia'
import { useLocalStorage } from '@vueuse/core'

// options 方式定义
export const useSystemInfo = defineStore('systemInfo', {
  state: () => ({
    isLocalhost: useLocalStorage('isLocalhost', false),
    version: useLocalStorage('api-version', '0.0.0')
  }),
  getters: {
    // 用户数据库的 id
    // userSqlId: (state) => state.userInfo.id,
  },
  actions: {
    setIsLocalhost(isLocalhost: boolean) {
      this.isLocalhost = isLocalhost
    },

    setVersion(version: string) {
      this.version = version
    }
  }
})
