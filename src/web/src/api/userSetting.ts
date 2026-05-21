import { httpClient } from 'src/api/base/httpClient'

/**
 * 用户设置 Upsert 请求数据
 */
export interface IUpsertUserSettingData {
  value: Record<string, unknown>
  description?: string | null
}

/**
 * 获取用户设置（仅返回 value）
 * @param key 设置键名
 * @returns 用户设置的 value（如果不存在返回 null）
 */
export function getUserSetting(key: string) {
  return httpClient.get<Record<string, unknown> | null>(`/user-settings/${key}`)
}

/**
 * 更新或创建用户设置（Upsert）
 * @param key 设置键名
 * @param data 用户设置数据
 * @returns 用户设置的 value
 */
export function upsertUserSetting(key: string, data: IUpsertUserSettingData) {
  return httpClient.put<Record<string, unknown>>(`/user-settings/${key}`, { data })
}

/**
 * 删除用户设置
 * @param key 设置键名
 */
export function deleteUserSetting(key: string) {
  return httpClient.delete(`/user-settings/${key}`)
}
