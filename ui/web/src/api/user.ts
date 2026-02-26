import { httpClient } from 'src/api/base/httpClient'
import type { IUserInfo } from 'src/stores/types'
import { sha256 } from 'src/utils/encrypt'

export interface IUserLoginInfo {
  token: string
  access: string[]
  userInfo: IUserInfo
  installedPlugins: string[]
  isLocalhost: boolean
}

export interface IUserInfoDetail {
  id: number
  oid: string
  name?: string
  avatar?: string | null
  roles: string[]
  status: number
  createAt?: string
  isSuperAdmin: boolean
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

/**
 * 获取用户信息
 * @param username 用户名
 * @returns
 */
export function getUserInfo(username: string) {
  return httpClient.get<IUserInfoDetail>(`/user/info/${username}`)
}

/**
 * 修改用户密码
 * @param oldPassword 旧密码
 * @param newPassword 新密码
 * @returns
 */
export function changeUserPassword(oldPassword: string, newPassword: string) {
  // 对密码加密
  oldPassword = sha256(oldPassword)
  newPassword = sha256(newPassword)
  return httpClient.put<boolean>('/user/password', {
    data: {
      oldPassword,
      newPassword
    }
  })
}

/**
 * 更新用户头像
 * @param blob 头像图片 Blob
 * @returns 返回头像 URL
 */
export function updateUserAvatar(blob: Blob) {
  const formData = new FormData()
  formData.append('avatar', blob, 'avatar.png')
  return httpClient.postForm<string>('/user/avatar', {
    data: formData
  })
}
