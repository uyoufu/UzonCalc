import type { monaco } from 'src/boot/monaco-editor'
import { monaco as monacoEditor } from 'src/boot/monaco-editor'
import type { ShallowRef } from 'vue'

export function useCalcFormatter(editorRef: ShallowRef<monaco.editor.IStandaloneCodeEditor | undefined>) {
  let formatterAction: monaco.IDisposable | null = null

  watch(
    () => editorRef.value,
    (editor) => {
      formatterAction?.dispose()
      formatterAction = null

      if (!editor) return

      formatterAction = editor.addAction({
        id: 'uzoncalc.editor.format-document',
        label: 'Format Document',
        keybindings: [monacoEditor.KeyMod.Alt | monacoEditor.KeyMod.Shift | monacoEditor.KeyCode.KeyF],
        run: async () => {
          await editor.getAction('editor.action.formatDocument')?.run()
        }
      })
    },
    { immediate: true }
  )

  onUnmounted(() => {
    formatterAction?.dispose()
    formatterAction = null
  })
}
