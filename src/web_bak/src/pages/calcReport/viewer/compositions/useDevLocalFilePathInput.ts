import { type Ref } from 'vue'
import { HtmlUpdateType, type ExecutionResult } from 'src/api/calcExecution'
import { useCalcReportViewerStore } from 'src/stores/calcReportViewer'

function createEmptyExecutionResult(): ExecutionResult {
  return {
    executionId: '',
    html: '',
    htmlPath: '',
    updateType: HtmlUpdateType.Full,
    windows: [],
    isCompleted: false
  }
}

export function useDevLocalFilePathInput(
  reportOid: Ref<string | null>,
  filePath: Ref<string>,
  calcReportNameRef: Ref<string>,
  executeResult: Ref<ExecutionResult>
) {
  const isDev = import.meta.env.DEV
  const calcReportViewerStore = useCalcReportViewerStore()
  const devFilePath = ref(calcReportViewerStore.devFilePath || filePath.value)

  watch(filePath, (newPath) => {
    devFilePath.value = newPath || ''
  })

  function onApplyDevFilePath() {
    const path = devFilePath.value.trim()
    if (!path) return

    const prevPath = filePath.value
    const fileName = path.split(/[\\/]/).pop() || path

    if (path !== prevPath && fileName !== calcReportNameRef.value) {
      executeResult.value = createEmptyExecutionResult()
    }

    filePath.value = path
    reportOid.value = null
    calcReportNameRef.value = fileName
    calcReportViewerStore.setDevFilePath(path)
  }

  return {
    isDev,
    devFilePath,
    onApplyDevFilePath
  }
}
