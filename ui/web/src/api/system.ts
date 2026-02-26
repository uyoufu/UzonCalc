import { httpClient } from 'src/api/base/httpClient'

export interface ISystemConfig {
  name: string
  loginWelcome: string
  icon: string
  copyright: string
  icpInfo: string
}

export interface IDesktopAutoLoginInfo {
  enabled: boolean
  username: string
  password: string
}

/**
 * 获取服务器版本
 * @returns
 */
export function getServerVersion() {
  return httpClient.get<string>('/system-info/version')
}

/**
 * 获取桌面端自动登录信息
 * @returns
 */
export function getDesktopAutoLoginInfo() {
  return httpClient.get<IDesktopAutoLoginInfo>('/system-info/desktop-auto-login')
}
