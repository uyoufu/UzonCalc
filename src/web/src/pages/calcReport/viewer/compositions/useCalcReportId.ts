import { useRoute } from 'vue-router'
import { computed } from 'vue'

export function useCalcReportId() {
  const route = useRoute()

  const calcReportId = computed(() => {
    return (route.params.calcReportId as string) || (route.query.calcReportId as string)
  })

  return {
    calcReportId
  }
}
