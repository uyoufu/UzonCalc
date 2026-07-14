import type { monaco } from 'src/boot/monaco-editor'
import type { ShallowRef } from 'vue'
import { Range } from 'monaco-editor'

export function useMenuCommands(editorRef: ShallowRef<monaco.editor.IStandaloneCodeEditor | undefined>) {
  function insertTemplateCmd() {}

  // 在当前代码中插入 toc() 调用
  function insertTocCmd() {
    const editor = editorRef.value
    if (!editor) return

    const position = editor.getPosition()
    if (!position) return

    const model = editor.getModel()
    if (!model) return

    // 插入 toc() 函数调用
    const edit = {
      range: new Range(position.lineNumber, position.column, position.lineNumber, position.column),
      text: 'toc()'
    }

    model.applyEdits([edit])
  }

  return {
    insertTemplateCmd,
    insertTocCmd
  }
}
