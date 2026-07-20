<template><div ref="editorElement" class="workspace-editor" /></template>

<script setup lang="ts">
/** Monaco editor that retains one model per open workspace file. */
import { monaco } from 'src/boot/monaco-editor'
import { registerUzoncalcProviders } from '../../editor/utils/uzoncalcCompletion'
import { registerWorkspacePythonProviders, type WorkspacePythonFile } from './workspacePythonLanguage'

const props = defineProps<{ path: string; content: string; openPaths: string[]; workspaceFiles: WorkspacePythonFile[] }>()
const emit = defineEmits<{ change: [path: string, content: string] }>()
const editorElement = ref<HTMLElement | null>(null)
const editor = shallowRef<monaco.editor.IStandaloneCodeEditor | null>(null)
const models = new Map<string, monaco.editor.ITextModel>()
const viewStates = new Map<string, monaco.editor.ICodeEditorViewState>()
let changeSubscription: monaco.IDisposable | null = null
let providers: { dispose: () => void } | null = null
let workspaceProviders: monaco.IDisposable | null = null
let isApplyingExternalContent = false
let activePath = ''

/**
 * Resolve the Monaco language from a workspace path.
 *
 * @param path Workspace-relative file path.
 * @returns Monaco language identifier for the file.
 */
function languageForPath(path: string): string {
  if (path.endsWith('.py')) return 'python'
  if (path.endsWith('.json')) return 'json'
  if (path.endsWith('.md')) return 'markdown'
  if (path.endsWith('.html')) return 'html'
  if (path.endsWith('.css') || path.endsWith('.scss')) return 'css'
  if (path.endsWith('.ts')) return 'typescript'
  if (path.endsWith('.js')) return 'javascript'
  return 'plaintext'
}

/**
 * Activate or create the Monaco model for the selected file.
 *
 * @param path Workspace-relative file path.
 * @param content Latest file content.
 * @returns Nothing.
 */
function activateModel(path: string, content: string): void {
  if (!editor.value || !path) return
  if (activePath) {
    const viewState = editor.value.saveViewState()
    if (viewState) viewStates.set(activePath, viewState)
  }
  let model = models.get(path)
  if (!model) {
    model = monaco.editor.createModel(content, languageForPath(path), monaco.Uri.parse(`inmemory://uzoncalc/${encodeURI(path)}`))
    models.set(path, model)
  } else if (model.getValue() !== content) {
    isApplyingExternalContent = true
    model.setValue(content)
    isApplyingExternalContent = false
  }
  editor.value.setModel(model)
  activePath = path
  const viewState = viewStates.get(path)
  if (viewState) editor.value.restoreViewState(viewState)
  changeSubscription?.dispose()
  changeSubscription = model.onDidChangeContent(() => {
    if (!isApplyingExternalContent) emit('change', path, model.getValue())
  })
  editor.value.focus()
}

/**
 * Return or create a model so definition targets include newly created files.
 *
 * @param path Workspace-relative definition target path.
 * @returns The matching Monaco model, otherwise `null`.
 */
function resolveWorkspaceModel(path: string): monaco.editor.ITextModel | null {
  const workspaceFile = props.workspaceFiles.find((file) => file.path === path)
  if (!workspaceFile) return null
  let model = models.get(path)
  if (!model) {
    model = monaco.editor.createModel(workspaceFile.content, languageForPath(path), monaco.Uri.parse(`inmemory://uzoncalc/${encodeURI(path)}`))
    models.set(path, model)
  }
  return model
}

onMounted(() => {
  if (!editorElement.value) return
  providers = registerUzoncalcProviders()
  workspaceProviders = registerWorkspacePythonProviders(() => props.workspaceFiles, resolveWorkspaceModel)
  editor.value = monaco.editor.create(editorElement.value, {
    automaticLayout: true,
    minimap: { enabled: false },
    fontSize: 14,
    tabSize: 4,
    scrollBeyondLastLine: false,
    theme: 'vs'
  })
  activateModel(props.path, props.content)
})

watch(() => [props.path, props.content] as const, ([path, content]) => activateModel(path, content))
watch(() => props.openPaths, (paths) => {
  const retainedPaths = new Set([...paths, ...props.workspaceFiles.map((file) => file.path)])
  models.forEach((model, path) => {
    if (retainedPaths.has(path)) return
    if (activePath === path) activePath = ''
    model.dispose()
    models.delete(path)
    viewStates.delete(path)
  })
  if (paths.includes(props.path) && !models.has(props.path)) activateModel(props.path, props.content)
}, { deep: true })
watch(() => props.workspaceFiles, (workspaceFiles) => {
  workspaceFiles.forEach((file) => {
    const model = models.get(file.path)
    if (model && file.path !== activePath && model.getValue() !== file.content) model.setValue(file.content)
  })
}, { deep: true })
onUnmounted(() => {
  changeSubscription?.dispose()
  editor.value?.dispose()
  models.forEach((model) => model.dispose())
  providers?.dispose()
  workspaceProviders?.dispose()
})
</script>

<style scoped>.workspace-editor { width: 100%; height: 100%; min-height: 420px; }</style>
