/** Workspace-aware Python import completion and definition navigation. */

import { monaco } from 'src/boot/monaco-editor'

export interface WorkspacePythonFile {
  path: string
  content: string
}

/**
 * Register Python providers backed by the current workspace file graph.
 *
 * @param getFiles Returns the latest text files, including newly created files.
 * @param resolveModel Resolves or creates the Monaco model for a workspace path.
 * @returns A disposable that unregisters both workspace providers.
 */
export function registerWorkspacePythonProviders(
  getFiles: () => WorkspacePythonFile[],
  resolveModel: (path: string) => monaco.editor.ITextModel | null
): monaco.IDisposable {
  const completionProvider = monaco.languages.registerCompletionItemProvider('python', {
    triggerCharacters: ['.'],
    provideCompletionItems(model, position) {
      if (!model.uri.toString().startsWith('inmemory://uzoncalc/')) return { suggestions: [] }
      const linePrefix = model.getLineContent(position.lineNumber).slice(0, position.column - 1)
      const match = linePrefix.match(/^\s*(?:from|import)\s+([\w.]*)$/)
      if (!match) return { suggestions: [] }
      const typedModule = match[1] || ''
      const suggestions = workspaceModules(getFiles())
        .filter((moduleName) => moduleName.startsWith(typedModule) && moduleName !== typedModule)
        .map((moduleName) => ({
          label: moduleName,
          kind: monaco.languages.CompletionItemKind.Module,
          insertText: moduleName.slice(typedModule.length),
          range: new monaco.Range(position.lineNumber, position.column, position.lineNumber, position.column),
          detail: modulePath(moduleName, getFiles()) || undefined
        }))
      return { suggestions }
    }
  })
  const definitionProvider = monaco.languages.registerDefinitionProvider('python', {
    provideDefinition(model, position) {
      if (!model.uri.toString().startsWith('inmemory://uzoncalc/')) return null
      const line = model.getLineContent(position.lineNumber)
      const importedModule = importedModuleAtPosition(line, position.column)
      if (!importedModule) return null
      const path = modulePath(importedModule, getFiles())
      if (!path) return null
      const targetModel = resolveModel(path)
      if (!targetModel) return null
      return { uri: targetModel.uri, range: new monaco.Range(1, 1, 1, 1) }
    }
  })
  return {
    dispose() {
      completionProvider.dispose()
      definitionProvider.dispose()
    }
  }
}

/**
 * Return importable modules exposed by Python files under `src`.
 *
 * @param files Current workspace text files.
 * @returns Absolute Python module names available for completion.
 */
function workspaceModules(files: WorkspacePythonFile[]): string[] {
  return files
    .map((file) => file.path)
    .filter((path) => path.startsWith('src/') && path.endsWith('.py'))
    .map((path) => path.slice(4, -3).replaceAll('/', '.').replace(/\.__init__$/, ''))
    .filter(Boolean)
}

/**
 * Resolve one absolute module name to its workspace source path.
 *
 * @param moduleName Absolute dotted Python module name.
 * @param files Current workspace text files.
 * @returns The matching module or package path, otherwise `null`.
 */
function modulePath(moduleName: string, files: WorkspacePythonFile[]): string | null {
  const basePath = `src/${moduleName.replaceAll('.', '/')}`
  return files.find((file) => file.path === `${basePath}.py`)?.path
    || files.find((file) => file.path === `${basePath}/__init__.py`)?.path
    || null
}

/**
 * Parse the module segment selected in an import statement.
 *
 * @param line Current editor line.
 * @param column One-based cursor column.
 * @returns The selected imported module, otherwise `null`.
 */
function importedModuleAtPosition(line: string, column: number): string | null {
  const importMatch = line.match(/^\s*import\s+([\w.]+)/)
  const fromMatch = line.match(/^\s*from\s+([\w.]+)\s+import\s+/)
  const match = importMatch || fromMatch
  if (!match?.[1] || match.index === undefined) return null
  const moduleStart = line.indexOf(match[1], match.index)
  const cursorIndex = column - 1
  if (cursorIndex < moduleStart || cursorIndex > moduleStart + match[1].length) return null
  return match[1]
}
