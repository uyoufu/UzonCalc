/** Administrator-only department and user-management APIs. */
import { httpClient } from 'src/api/base/httpClient'
import { sha256 } from 'src/utils/encrypt'
import type { UserStatus } from 'src/stores/types'

export interface DepartmentNode {
  departmentOid: string
  parentOid: string | null
  name: string
  sortOrder: number
  createdAt: string
  updatedAt: string
}

export interface ManagedUser {
  userOid: string
  username: string
  nickName: string | null
  avatar: string | null
  roles: string[]
  status: UserStatus
  departmentOids: string[]
  createdAt: string
}

export function listDepartments() { return httpClient.get<DepartmentNode[]>('/admin/departments') }
export function createDepartment(name: string, parentOid: string | null) { return httpClient.post<DepartmentNode>('/admin/departments', { data: { name, parentOid } }) }
export function updateDepartment(departmentOid: string, name: string) { return httpClient.put<DepartmentNode>(`/admin/departments/${departmentOid}`, { data: { name } }) }
export function moveDepartment(departmentOid: string, parentOid: string | null, sortOrder: number) { return httpClient.put<DepartmentNode>(`/admin/departments/${departmentOid}/position`, { data: { parentOid, sortOrder } }) }
export function deleteDepartment(departmentOid: string) { return httpClient.delete<void>(`/admin/departments/${departmentOid}`) }
export function countManagedUsers(params: { query?: string; departmentOid?: string }) { return httpClient.get<number>('/admin/users/count', { params }) }
export function listManagedUsers(params: { query?: string; departmentOid?: string; skip: number; limit: number; sortBy: string; descending: boolean }) { return httpClient.get<ManagedUser[]>('/admin/users/items', { params }) }
export function createManagedUser(data: { username: string; nickName?: string | null; password: string; departmentOids: string[] }) { return httpClient.post<ManagedUser>('/admin/users', { data: { ...data, password: sha256(data.password) } }) }
export function setManagedUserStatus(userOid: string, status: UserStatus) { return httpClient.put<ManagedUser>(`/admin/users/${userOid}/status`, { data: { status } }) }
export function resetManagedUserPassword(userOid: string, newPassword: string) { return httpClient.post<void>(`/admin/users/${userOid}/reset-password`, { data: { newPassword: sha256(newPassword) } }) }
