import { httpClient } from 'src/api/base/httpClient'

export interface ISystemConfig {
  name: string
  loginWelcome: string
  icon: string
  copyright: string
  icpInfo: string
}

/**
 * 获取服务器版本
 * @returns
 */
export function getServerVersion() {
  return httpClient.get<string>('/system-info/version')
}
