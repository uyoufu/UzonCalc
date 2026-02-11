import { t } from 'src/i18n/helpers'
import { checkCalcReportName } from './useCalcReportNameChecker'
import { notifyError, notifySuccess } from 'src/utils/dialog'
import { saveCalcReport, getCalcReport } from 'src/api/calcReport'
import type { Ref, ShallowRef } from 'vue'
import { ref, onMounted, onUnmounted } from 'vue'
import type { editor } from 'monaco-editor'
import { useRoute } from 'vue-router'

/**
 * 不可多次调用该函数，避免重复 onMounted
 * @param calcReportOid
 * @returns
 */
export function useCalcReportSaver(
  calcReportOid: Ref<string>,
  monacoEditorRef: ShallowRef<editor.IStandaloneCodeEditor | undefined>
) {
  const calcReportName = ref(t('calcReportPage.defaultCalcReportName'))
  const route = useRoute()

  const categoryOid = route.query.categoryOid as string | undefined

  onMounted(async () => {
    if (calcReportOid.value) {
      // 如果有 reportOid，说明是编辑已有报告，获取报告信息
      const { data: reportInfo } = await getCalcReport(calcReportOid.value)
      calcReportName.value = reportInfo.name
    } else {
      // 如果没有 reportOid，说明是新建报告，需要判断是否有 categoryOid
      if (!categoryOid) {
        notifyError(t('calcReportPage.errorNoCategory'))
        return
      }
    }
  })

  async function onSaveCalcReport() {
    // 保存前检查名称是否合法
    if (!checkCalcReportName(calcReportName.value)) {
      return false
    }

    // 从编辑器获取文本
    const code = monacoEditorRef.value?.getValue() ?? ''

    // 调用后端 API 保存文件
    const { data: reportOid } = await saveCalcReport({
      reportName: calcReportName.value,
      code,
      reportOid: calcReportOid.value || undefined,
      // 仅在新建报告时传递 categoryOid
      categoryOid: calcReportOid.value ? undefined : categoryOid
    })

    // 更新返回的 reportOid
    calcReportOid.value = reportOid

    notifySuccess('保存成功')
    return true
  }

  // 注册快捷键 Ctrl+S 保存
  async function handleKeyDown(event: KeyboardEvent) {
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
      event.preventDefault()
      await onSaveCalcReport()
    }
  }
  onMounted(() => {
    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    window.addEventListener('keydown', handleKeyDown)
  })
  // 组件卸载时移除事件监听
  onUnmounted(() => {
    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    window.removeEventListener('keydown', handleKeyDown)
  })

  return {
    calcReportName,
    onSaveCalcReport
  }
}
