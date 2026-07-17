<template><div ref="editorElement" class="workspace-editor" /></template>

<script setup lang="ts">
/** Monaco editor that retains one model per open workspace file. */
import { monaco } from 'src/boot/monaco-editor'
import { registerUzoncalcProviders } from '../../editor/utils/uzoncalcCompletion'

const props = defineProps<{ path: string; content: string; openPaths: string[] }>()
const emit = defineEmits<{ change: [path: string, content: string] }>()
const editorElement = ref<HTMLElement | null>(null)
const editor = shallowRef<monaco.editor.IStandaloneCodeEditor | null>(null)
const models = new Map<string, monaco.editor.ITextModel>()
const viewStates = new Map<string, monaco.editor.ICodeEditorViewState>()
let changeSubscription: monaco.IDisposable | null = null
let providers: { dispose: () => void } | null = null
let isApplyingExternalContent = false
let activePath = ''

/** Resolve Monaco language from a workspace path. */
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

/** Activate or create the Monaco model for the selected file. */
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

onMounted(() => {
  if (!editorElement.value) return
  providers = registerUzoncalcProviders()
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
  const retainedPaths = new Set(paths)
  models.forEach((model, path) => {
    if (retainedPaths.has(path)) return
    if (activePath === path) activePath = ''
    model.dispose()
    models.delete(path)
    viewStates.delete(path)
  })
  if (paths.includes(props.path) && !models.has(props.path)) activateModel(props.path, props.content)
}, { deep: true })
onUnmounted(() => {
  changeSubscription?.dispose()
  editor.value?.dispose()
  models.forEach((model) => model.dispose())
  providers?.dispose()
})
</script>

<style scoped>.workspace-editor { width: 100%; height: 100%; min-height: 420px; }</style>
