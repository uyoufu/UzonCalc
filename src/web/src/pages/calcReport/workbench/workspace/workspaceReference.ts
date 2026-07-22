/** Build copyable references for files in a root-package workspace. */

/**
 * Return whether a workspace path can identify an importable Python module.
 *
 * @param path Workspace-root-relative path.
 * @returns Whether every module segment is a valid Python identifier.
 * @throws This function does not throw.
 */
export function isImportableWorkspacePythonPath(path: string): boolean {
  if (!path.endsWith('.py')) return false
  const moduleParts = path.slice(0, -3).split('/')
  return moduleParts.length > 0 && moduleParts.every((part) => /^[A-Za-z_]\w*$/.test(part))
}

/**
 * Resolve a target Python file as a module relative to an importing file.
 *
 * @param targetPath Workspace-root-relative target Python path.
 * @param importerPath Workspace-root-relative importing Python path.
 * @returns Leading-dot module path, or `null` when either path is invalid.
 * @throws This function does not throw.
 */
export function workspaceRelativeModuleForPath(targetPath: string, importerPath: string): string | null {
  if (!isImportableWorkspacePythonPath(targetPath) || !isImportableWorkspacePythonPath(importerPath)) return null
  const targetParts = targetPath.slice(0, -3).split('/')
  if (targetParts.at(-1) === '__init__') targetParts.pop()
  const importerParts = importerPath.slice(0, -3).split('/')
  const importerPackageParts = importerParts.slice(0, -1)
  let commonCount = 0
  while (
    commonCount < importerPackageParts.length
    && commonCount < targetParts.length
    && importerPackageParts[commonCount] === targetParts[commonCount]
  ) commonCount += 1
  const relativeLevel = importerPackageParts.length - commonCount + 1
  const suffix = targetParts.slice(commonCount).join('.')
  return `${'.'.repeat(relativeLevel)}${suffix}`
}

/**
 * Build a relative Python import reference or raw workspace resource path.
 *
 * @param path Workspace-root-relative target file or directory path.
 * @param importerPath Active Python file receiving the copied reference.
 * @returns Copyable reference, or `null` without a valid Python import context.
 * @throws This function does not throw.
 */
export function workspaceReferenceForPath(path: string, importerPath: string | null): string | null {
  if (!isImportableWorkspacePythonPath(path)) return path
  if (!importerPath) return null
  const relativeModule = workspaceRelativeModuleForPath(path, importerPath)
  return relativeModule ? `from ${relativeModule} import *` : null
}
