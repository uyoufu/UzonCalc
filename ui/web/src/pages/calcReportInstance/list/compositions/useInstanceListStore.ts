import { createGlobalState } from '@vueuse/core'

export const useInstanceListStore = createGlobalState(() => {
  const instanceListUpdateSignal = ref(0)

  return {
    instanceListUpdateSignal
  }
})
