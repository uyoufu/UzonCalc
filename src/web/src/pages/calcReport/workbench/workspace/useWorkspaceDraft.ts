/** Own the complete client-side draft for a calculation-report workspace. */

import { strToU8, zipSync } from 'fflate'
import type {
  ReportDependency,
  WorkspaceFileDescriptor,
  WorkspaceSaveRequest,
  WorkspaceSnapshot
} from 'src/api/calc/types'
import { getWorkspaceFile, type WorkspaceUpload } from 'src/api/calc/workspace'
import type { TreeNodeData } from 'element-plus/es/components/tree/src/tree.type'
import { computed, ref, type Ref } from 'vue'

const TEXT_EXTENSIONS = new Set([
  'css', 'csv', 'html', 'ini', 'js', 'json', 'md', 'py', 'scss', 'toml', 'ts', 'txt', 'xml', 'yaml', 'yml'
])

export interface WorkspaceDraftFile {
  path: string
  originalPath: string | null
  size: number
  sha256: string | null
  content: Blob | null
  text: string | null
  originalText: string | null
  isText: boolean
  isDirty: boolean
  isNew: boolean
}

export interface WorkspaceTreeNode extends TreeNodeData {
  id: string
  parentId: string | null
  label: string
  path: string
  kind: 'file' | 'folder'
  sort: number
}

/** Return whether a workspace path should be edited as UTF-8 text. */
export function isWorkspaceTextFile(path: string): boolean {
  const extension = path.split('.').pop()?.toLowerCase() || ''
  return TEXT_EXTENSIONS.has(extension)
}

/** Validate and normalize a client-created workspace path. */
export function normalizeWorkspacePath(path: string): string {
  const normalized = path.trim().replaceAll('\\', '/').replace(/^\/+|\/+$/g, '')
  const parts = normalized.split('/')
  if (!normalized || parts.some((part) => !part || part === '.' || part === '..')) {
    throw new Error('Workspace path must be normalized and relative')
  }
  if (normalized !== 'calcbook.json' && !normalized.startsWith('src/') && !normalized.startsWith('resources/')) {
    throw new Error('Files must be calcbook.json or live under src/resources')
  }
  return normalized
}

/** Create a derived flat tree from persisted file paths. */
export function buildWorkspaceTree(files: WorkspaceDraftFile[]): WorkspaceTreeNode[] {
  const nodes = new Map<string, WorkspaceTreeNode>()
  files.forEach((file) => {
    const parts = file.path.split('/')
    for (let index = 0; index < parts.length; index += 1) {
      const path = parts.slice(0, index + 1).join('/')
      const isFile = index === parts.length - 1
      if (!nodes.has(path)) {
        nodes.set(path, {
          id: path,
          parentId: index === 0 ? null : parts.slice(0, index).join('/'),
          label: parts[index] || path,
          path,
          kind: isFile ? 'file' : 'folder',
          sort: isFile ? 1 : 0
        })
      }
    }
  })
  return [...nodes.values()]
}

/** Build the default files for a new report workspace. */
export function createDefaultWorkspaceFiles(): WorkspaceDraftFile[] {
  const manifest = JSON.stringify({ formatVersion: 1, entryPath: 'src/main.py' }, null, 2) + '\n'
  const source = `from uzoncalc import *\n\n\n@uzon_calc()\nasync def sheet():\n    # Write calculation logic here.\n    pass\n`
  return [
    createTextDraftFile('calcbook.json', manifest),
    createTextDraftFile('src/main.py', source)
  ]
}

/** Create one unsaved text draft file. */
function createTextDraftFile(path: string, text: string): WorkspaceDraftFile {
  const content = new Blob([text], { type: 'text/plain;charset=utf-8' })
  return { path, originalPath: null, size: content.size, sha256: null, content, text, originalText: null, isText: true, isDirty: true, isNew: true }
}

/** Download a Blob with a browser-managed object URL. */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

/** Manage one workspace's files, dependencies, dirty state, and snapshots. */
export function useWorkspaceDraft(reportOid: Ref<string>) {
  const files = ref<WorkspaceDraftFile[]>([])
  const dependencies = ref<ReportDependency[]>([])
  const workspaceRevision = ref(0)
  const entryPath = ref('src/main.py')
  const isLoading = ref(false)
  const isSaving = ref(false)
  const isDependencyDirty = ref(false)
  const treeNodes = computed(() => buildWorkspaceTree(files.value))
  const hasUnsavedChanges = computed(() => isDependencyDirty.value || files.value.some((file) => file.isDirty))

  /** Replace local state from server workspace metadata. */
  function initializeFromSnapshot(snapshot: WorkspaceSnapshot): void {
    workspaceRevision.value = snapshot.workspaceRevision
    entryPath.value = snapshot.entryPath
    dependencies.value = structuredClone(snapshot.dependencies)
    files.value = snapshot.files.map((file) => ({
      path: file.path,
      originalPath: file.path,
      size: file.size,
      sha256: file.sha256,
      content: null,
      text: null,
      originalText: null,
      isText: isWorkspaceTextFile(file.path),
      isDirty: false,
      isNew: false
    }))
    isDependencyDirty.value = false
  }

  /** Initialize a new report with the canonical default workspace. */
  function initializeNewWorkspace(): void {
    workspaceRevision.value = 0
    entryPath.value = 'src/main.py'
    dependencies.value = []
    files.value = createDefaultWorkspaceFiles()
    isDependencyDirty.value = false
  }

  /** Ensure one draft file has its current bytes loaded. */
  async function ensureFileLoaded(file: WorkspaceDraftFile): Promise<WorkspaceDraftFile> {
    if (file.content !== null) {
      if (file.isText && file.text === null) {
        file.text = await file.content.text()
        if (!file.isNew && !file.isDirty) file.originalText = file.text
      }
      return file
    }
    isLoading.value = true
    try {
      file.content = await getWorkspaceFile(reportOid.value, file.originalPath || file.path)
      file.size = file.content.size
      if (file.isText) {
        file.text = await file.content.text()
        if (!file.isNew && !file.isDirty) file.originalText = file.text
      }
      return file
    } finally {
      isLoading.value = false
    }
  }

  /** Add a new text or binary file to the draft. */
  function addFile(path: string, content: Blob | string = ''): WorkspaceDraftFile {
    const normalized = normalizeWorkspacePath(path)
    if (files.value.some((file) => file.path === normalized)) throw new Error('A file already exists at this path')
    const blob = typeof content === 'string' ? new Blob([content], { type: 'text/plain;charset=utf-8' }) : content
    const isText = typeof content === 'string' || isWorkspaceTextFile(normalized)
    const file: WorkspaceDraftFile = {
      path: normalized,
      originalPath: null,
      size: blob.size,
      sha256: null,
      content: blob,
      text: typeof content === 'string' ? content : null,
      originalText: null,
      isText,
      isDirty: true,
      isNew: true
    }
    files.value.push(file)
    return file
  }

  /** Update one text file and compare it with the last synchronized content. */
  function updateText(path: string, text: string): void {
    const file = files.value.find((candidate) => candidate.path === path)
    if (!file) return
    file.text = text
    file.content = new Blob([text], { type: 'text/plain;charset=utf-8' })
    file.size = file.content.size
    file.isDirty = file.isNew || file.path !== file.originalPath || text !== file.originalText
  }

  /** Rename one file or every file below a derived folder. */
  async function renamePath(oldPath: string, newPath: string): Promise<void> {
    if (oldPath === 'calcbook.json') throw new Error('calcbook.json cannot be renamed')
    const normalized = normalizeWorkspacePath(newPath)
    const matches = files.value.filter((file) => file.path === oldPath || file.path.startsWith(`${oldPath}/`))
    if (matches.length === 0) return
    for (const file of matches) {
      await ensureFileLoaded(file)
      const suffix = file.path.slice(oldPath.length)
      const targetPath = normalizeWorkspacePath(`${normalized}${suffix}`)
      if (files.value.some((candidate) => !matches.includes(candidate) && candidate.path === targetPath)) {
        throw new Error(`A file already exists at ${targetPath}`)
      }
      file.path = targetPath
      file.isDirty = file.isNew || file.path !== file.originalPath || (file.isText && file.text !== file.originalText)
    }
    if (entryPath.value === oldPath || entryPath.value.startsWith(`${oldPath}/`)) {
      setEntryPath(`${normalized}${entryPath.value.slice(oldPath.length)}`)
    }
  }

  /** Remove one file or all files below a derived folder. */
  function deletePath(path: string): void {
    if (path === 'calcbook.json') throw new Error('calcbook.json cannot be deleted')
    if (entryPath.value === path || entryPath.value.startsWith(`${path}/`)) throw new Error('The entry file cannot be deleted')
    files.value = files.value.filter((file) => file.path !== path && !file.path.startsWith(`${path}/`))
  }

  /** Set a Python source file as the manifest entry path. */
  function setEntryPath(path: string): void {
    if (!path.startsWith('src/') || !path.endsWith('.py')) throw new Error('The entry must be a Python file under src')
    entryPath.value = path
    const manifest = files.value.find((file) => file.path === 'calcbook.json')
    if (!manifest) return
    const current = manifest.text ? JSON.parse(manifest.text) as Record<string, unknown> : {}
    current.formatVersion = typeof current.formatVersion === 'number' ? current.formatVersion : 1
    current.entryPath = path
    updateText('calcbook.json', JSON.stringify(current, null, 2) + '\n')
  }

  /** Replace dependency declarations and mark the workspace dirty. */
  function setDependencies(value: ReportDependency[]): void {
    dependencies.value = structuredClone(value)
    isDependencyDirty.value = true
  }

  /** Build a complete multipart snapshot without uploading unchanged files. */
  function buildSavePayload(create?: WorkspaceSaveRequest['create']): { snapshot: WorkspaceSaveRequest; uploads: WorkspaceUpload[] } {
    const descriptors: WorkspaceFileDescriptor[] = []
    const uploads: WorkspaceUpload[] = []
    files.value.forEach((file) => {
      if (file.isDirty || file.isNew || file.path !== file.originalPath) {
        if (!file.content) throw new Error(`Dirty file is not loaded: ${file.path}`)
        descriptors.push({ path: file.path, source: 'upload' })
        uploads.push({ path: file.path, content: file.content })
      } else {
        descriptors.push({ path: file.path, source: 'current', sha256: file.sha256 || undefined })
      }
    })
    return {
      snapshot: { workspaceRevision: workspaceRevision.value, create, files: descriptors, dependencies: dependencies.value },
      uploads
    }
  }

  /** Mark all current files as synchronized after a successful save. */
  function markSaved(snapshot: WorkspaceSnapshot): void {
    const serverFiles = new Map(snapshot.files.map((file) => [file.path, file]))
    files.value.forEach((file) => {
      const persisted = serverFiles.get(file.path)
      file.originalPath = file.path
      file.sha256 = persisted?.sha256 || null
      file.size = persisted?.size ?? file.size
      file.originalText = file.isText ? file.text : null
      file.isDirty = false
      file.isNew = false
    })
    workspaceRevision.value = snapshot.workspaceRevision
    dependencies.value = structuredClone(snapshot.dependencies)
    entryPath.value = snapshot.entryPath
    isDependencyDirty.value = false
  }

  /** Export every local file as a standard ZIP while preserving workspace paths. */
  async function exportLocalZip(filename: string): Promise<void> {
    const archiveEntries: Record<string, Uint8Array> = {}
    for (const file of files.value) {
      await ensureFileLoaded(file)
      if (file.text !== null) archiveEntries[file.path] = strToU8(file.text)
      else archiveEntries[file.path] = new Uint8Array(await file.content!.arrayBuffer())
    }
    downloadBlob(new Blob([zipSync(archiveEntries)], { type: 'application/zip' }), filename)
  }

  return {
    files,
    dependencies,
    workspaceRevision,
    entryPath,
    isLoading,
    isSaving,
    treeNodes,
    hasUnsavedChanges,
    initializeFromSnapshot,
    initializeNewWorkspace,
    ensureFileLoaded,
    addFile,
    updateText,
    renamePath,
    deletePath,
    setEntryPath,
    setDependencies,
    buildSavePayload,
    markSaved,
    exportLocalZip
  }
}
