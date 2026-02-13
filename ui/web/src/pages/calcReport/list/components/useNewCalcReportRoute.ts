import { t } from 'src/i18n/helpers'
import type { ComputedRef } from 'vue'
import { useRouter } from 'vue-router'
import { objectId } from 'src/utils/objectId'

export function generateEditorCacheKey(reportOid: string) {
  return reportOid
}

export function useNewCalcReportRoute(categoryOid: ComputedRef<string>) {
  const router = useRouter()

  /**
   * 导航到新建计算报告页面
   */
  async function goToNewCalcReport() {
    const reportOid = objectId()
    await router.push({
      name: 'editCalcReport',
      query: {
        categoryOid: categoryOid.value,
        reportOid: reportOid,
        tagName: t('global.new'),
        // 覆盖默认的缓存 key，确保每次新建报告都是一个新的页面实例
        __cacheKey: generateEditorCacheKey(reportOid)
      }
    })
  }

  return {
    goToNewCalcReport
  }
}
