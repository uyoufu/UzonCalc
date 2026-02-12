import { t } from 'src/i18n/helpers'
import type { ComputedRef } from 'vue'
import { useRouter } from 'vue-router'

export function useNewCalcReportRoute(categoryOid: ComputedRef<string>) {
  const router = useRouter()

  /**
   * 导航到新建计算报告页面
   */
  async function goToNewCalcReport() {
    await router.push({
      name: 'editCalcReport',
      query: {
        categoryOid: categoryOid.value,
        tagName: t('global.new'),
        // 随机数用于防止新建页被缓存
        random: Math.random().toString(36).substring(2, 8)
      }
    })
  }

  return {
    goToNewCalcReport
  }
}
