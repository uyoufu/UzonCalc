import { t } from 'src/i18n/helpers'
import logger from 'loglevel'
import { checkCalcReportName } from './useCalcReportNameChecker'
import { notifySuccess } from 'src/utils/dialog'
import { saveCalcReport, getCalcReport } from 'src/api/calcReport'
import type { Ref, ShallowRef } from 'vue'
import { ref, onMounted, onUnmounted } from 'vue'
import type { editor } from 'monaco-editor'
import { useCalcListStore } from '../../list/compositions/useCalcListStore'
import { useRouteUpdater } from 'src/layouts/components/tags/routeHistories'
import { objectId } from 'src/utils/objectId'

/**
 * 不可多次调用该函数，避免重复 onMounted
 * @param calcReportOid
 * @returns
 */
export function useCalcReportSaver(
  calcCategoryOid: Ref<string>,
  calcReportOid: Ref<string>,
  monacoEditorRef: ShallowRef<editor.IStandaloneCodeEditor | undefined>,
  enableSaveAs: Ref<boolean>
) {
  const calcReportName = ref(t('calcReportPage.defaultCalcReportName'))

  // #region 报告名称
  watch(calcReportOid, async (newOid) => {
    if (!newOid) return

    logger.debug('[useCalcReportSaver] 计算报告 OID 变化，获取报告详情', newOid)

    try {
      const { data: reportInfo } = await getCalcReport(newOid, true)
      calcReportName.value = reportInfo.name
    } catch (error) {
      logger.warn('获取报告详情失败', error)
    }
  })
  // #endregion

  const { calcListUpdateSignal } = useCalcListStore()
  const { updateRouteTag } = useRouteUpdater()
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
      categoryOid: calcCategoryOid.value
    })

    if (enableSaveAs.value) {
      // logger.debug('[useCalcReportSaver] 另存为模式，生成新的 reportOid', calcReportOid.value, objectId())
      // 如果是另存为，则更新 reportOid 为新值
      calcReportOid.value = objectId()
    } else {
      // 更新返回的 reportOid
      calcReportOid.value = reportOid
      updateRouteTag(reportOid.slice(-4))
    }

    notifySuccess('保存成功')
    // 触发计算报告列表刷新
    calcListUpdateSignal.value += 1

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
