import type { ComputedRef } from 'vue'
import { useRouter } from 'vue-router'

export function useNewCalcReportRoute(categoryOid: ComputedRef<string>) {
  const router = useRouter()

  /**
   * 导航到新建计算报告页面
   */
  async function goToNewCalcReport() {
    await router.push({ name: 'newCalcReport', query: { categoryOid: categoryOid.value } })
  }

  return {
    goToNewCalcReport
  }
}
