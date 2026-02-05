import { httpClient } from 'src/api/base/httpClient'
import type { IUserInfo } from 'src/stores/types'
import { sha256 } from 'src/utils/encrypt'

export interface IUserLoginInfo {
  token: string
  access: string[]
  userInfo: IUserInfo
  installedPlugins: string[]
}

/**
 * 用户登录
 * @returns
 */
export function userLogin(username: string, password: string, lang: string) {
  // 对密码加密
  password = sha256(password)
  return httpClient.post<IUserLoginInfo>('/user/sign-in', {
    data: {
      username,
      password,
      lang
    }
  })
}
