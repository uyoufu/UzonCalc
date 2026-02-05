import { type Ref } from 'vue'
import { selectLocalFile } from 'src/api/desktop'

export function useLocalFileSelector (
  reportOid: Ref<string | null>,
  filePath: Ref<string>,
  calcReportNameRef: Ref<string>
) {
  async function onOpenLocalFile () {
    const { data: path } = await selectLocalFile()
    if (path) {
      filePath.value = path
      // 清除 reportOid 以确保执行时使用的是文件路径
      reportOid.value = null

      // 从路径中提取文件名作为显示名称
      const fileName = path.split(/[\\/]/).pop() || path
      calcReportNameRef.value = fileName
    }
  }

  return {
    onOpenLocalFile
  }
}

