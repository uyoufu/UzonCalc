import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import { useCalcReportViewerStore } from 'src/stores/calcReportViewer'
import { useSystemInfo } from 'src/stores/system'
import { useUserInfoStore } from 'src/stores/user'
import type { IUserInfo } from 'src/stores/types'

const routerMock = vi.hoisted(() => ({ push: vi.fn().mockResolvedValue(undefined) }))
vi.mock('src/router/index', () => ({ useRouter: () => routerMock }))

describe('store localStorage persistence', () => {
  beforeEach(() => {
    window.localStorage.clear()
    window.sessionStorage.clear()
    routerMock.push.mockClear()
    setActivePinia(createPinia())
  })

  it('persists the existing user, system, and viewer cache fields locally', async () => {
    const userStore = useUserInfoStore()
    const systemStore = useSystemInfo()
    const viewerStore = useCalcReportViewerStore()

    userStore.setToken('token-value')
    systemStore.setVersion('1.2.3')
    viewerStore.setDevFilePath('/tmp/report.html')
    await nextTick()

    expect(window.localStorage.getItem('token')).toBe('token-value')
    expect(window.localStorage.getItem('api-version')).toBe('1.2.3')
    expect(window.localStorage.getItem('calc-report-viewer-dev-file-path')).toBe('/tmp/report.html')
    expect(window.sessionStorage.length).toBe(0)
  })

  it('reacts to storage events from another page', async () => {
    const userStore = useUserInfoStore()

    window.localStorage.setItem('token', 'remote-token')
    window.dispatchEvent(new StorageEvent('storage', { key: 'token', newValue: 'remote-token', storageArea: window.localStorage }))
    await nextTick()

    expect(userStore.token).toBe('remote-token')
  })

  it('clears persistent credentials and identity on logout while preserving locale', async () => {
    const userStore = useUserInfoStore()
    const userInfo = {
      oid: 'user-oid', id: 1, username: 'user', nickName: null, avatar: null, status: 1, roles: ['regular']
    } as IUserInfo
    userStore.setUserLoginInfo(userInfo, 'token-value', ['reports'])
    userStore.setSecretKey('secret')
    userStore.setInstalledPlugins(['plugin'])
    userStore.setLocale('zh-CN')

    await userStore.logout()

    expect(userStore.token).toBe('')
    expect(userStore.access).toEqual([])
    expect(userStore.secretKey).toBe('')
    expect(userStore.installedPlugins).toEqual([])
    expect(userStore.userInfo).toEqual({})
    expect(userStore.locale).toBe('zh-CN')
    expect(routerMock.push).toHaveBeenCalledWith('/login')
  })
})
