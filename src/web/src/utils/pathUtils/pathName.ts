/**
 * 验证路径名称是否合法
 * 不能包含目录不允许的字符串: \ / : * ? " < > |
 * @param pathName
 * @returns
 */
export function validatePathName(pathName: string): boolean {
  // 不能包含目录不允许的字符串: \ / : * ? " < > |
  const invalidChars = /[:*?"<>|]/
  return !invalidChars.test(pathName)
}
