export enum UserStatus {
  Deleted = 0,
  Active = 1,
  Forbidden_login = 2
}

// 用户信息
export interface IUserInfo {
  oid: string,
  id: number,
  username: string
  nickName: string | null,
  avatar: string | null,
  status: UserStatus,
  roles: string[]
}
