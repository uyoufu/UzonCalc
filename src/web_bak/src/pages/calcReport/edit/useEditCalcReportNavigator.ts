import { useRouter } from 'vue-router'

export function useEditCalcReportNavigator() {
  const router = useRouter()
  async function navigateToEditCalcReport(reportOid: string, categoryOid: string, tagName: string) {
    await router.push({
      name: 'editCalcReport',
      query: {
        reportOid,
        categoryOid: categoryOid,
        tagName: tagName,
        __cacheKey: reportOid
      }
    })
  }

  return {
    navigateToEditCalcReport
  }
}
