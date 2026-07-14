import type { Ref, ShallowRef } from 'vue'
import type { editor } from 'monaco-editor'
import { getCalcReportSourceCode } from 'src/api/calcReport'

export function useReportSourceCode(
  reportOidRef: Ref<string>,
  monacoEditorRef: ShallowRef<editor.IStandaloneCodeEditor | undefined>
) {
  let requestId = 0
  async function syncSourceCode() {
    const reportOid = reportOidRef.value
    const editorInstance = monacoEditorRef.value

    if (!reportOid || !editorInstance) return

    const currentRequestId = ++requestId

    const { data: sourceCode } = await getCalcReportSourceCode(reportOid, true)
    if (currentRequestId !== requestId) {
      return
    }

    if (editorInstance.getValue() !== sourceCode) {
      editorInstance.setValue(sourceCode)
    }
  }

  onMounted(async () => {
    await syncSourceCode()
  })

  watch(reportOidRef, async () => {
    await syncSourceCode()
  })

  return {
    syncSourceCode
  }
}
