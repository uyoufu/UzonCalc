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
 * Build a Python import reference or raw workspace-relative resource path.
 *
 * @param path Workspace-root-relative file or directory path.
 * @returns Copyable reference calculated from the workspace root.
 * @throws This function does not throw.
 */
export function workspaceReferenceForPath(path: string): string {
  if (!isImportableWorkspacePythonPath(path)) return path
  const moduleParts = path.slice(0, -3).split('/')
  if (moduleParts.at(-1) === '__init__') moduleParts.pop()
  return moduleParts.length > 0 ? `from ${moduleParts.join('.')} import *` : 'from . import *'
}
