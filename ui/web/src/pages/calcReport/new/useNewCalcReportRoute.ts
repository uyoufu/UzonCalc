import { useRouter } from "vue-router"

export function useNewCalcReportRoute () {
  const router = useRouter()

  /**
   * 导航到新建计算报告页面
   */
  async function goToNewCalcReport () {
    await router.push({ name: 'newCalcReport' })
  }

  return {
    goToNewCalcReport
  }
}
