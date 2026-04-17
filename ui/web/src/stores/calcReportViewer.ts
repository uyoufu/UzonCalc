import { defineStore } from 'pinia'
import { useSessionStorage } from '@vueuse/core'

export const useCalcReportViewerStore = defineStore('calcReportViewer', {
  state: () => ({
    devFilePath: useSessionStorage('calc-report-viewer-dev-file-path', '')
  }),

  actions: {
    setDevFilePath(path: string) {
      this.devFilePath = path
    }
  }
})
