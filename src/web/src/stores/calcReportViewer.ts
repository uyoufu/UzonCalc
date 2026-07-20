import { defineStore } from 'pinia'
import { useLocalStorage } from '@vueuse/core'

export const useCalcReportViewerStore = defineStore('calcReportViewer', {
  state: () => ({
    devFilePath: useLocalStorage('calc-report-viewer-dev-file-path', '')
  }),

  actions: {
    setDevFilePath(path: string) {
      this.devFilePath = path
    }
  }
})
