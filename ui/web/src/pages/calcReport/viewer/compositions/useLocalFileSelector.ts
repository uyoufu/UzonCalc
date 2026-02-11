import { type Ref } from 'vue'
import { selectLocalFile } from 'src/api/desktop'
import type { ExecutionResult } from 'src/api/calcExecution'

export function useLocalFileSelector(
  reportOid: Ref<string | null>,
  filePath: Ref<string>,
  calcReportNameRef: Ref<string>,
  executeResult: Ref<ExecutionResult>
) {
  async function onOpenLocalFile() {
    const { data: path } = await selectLocalFile()
    if (path) {
      // 从路径中提取文件名作为显示名称
      const fileName = path.split(/[\\/]/).pop() || path

      // 若文件名与之前不同，则重置执行结果
      if (fileName !== calcReportNameRef.value) {
        executeResult.value = {
          executionId: '',
          html: '',
          windows: [],
          isCompleted: false
        }
      }

      filePath.value = path
      // 清除 reportOid 以确保执行时使用的是文件路径
      reportOid.value = null
      calcReportNameRef.value = fileName
    }
  }

  return {
    onOpenLocalFile
  }
}
