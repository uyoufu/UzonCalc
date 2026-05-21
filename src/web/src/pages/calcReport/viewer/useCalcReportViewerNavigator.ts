import { useRouter } from 'vue-router'

export function useCalcReportViewerNavigator() {
  const router = useRouter()
  async function navigateToCalcReportViewer(reportOid: string, tagName: string) {
    await router.push({
      name: 'calcReportViewer',
      query: {
        reportOid,
        tagName: tagName,
        __cacheKey: reportOid
      }
    })
  }

  return {
    navigateToCalcReportViewer
  }
}
