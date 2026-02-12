import { ref } from 'vue'

const calcListUpdateSignal = ref(0)

export function useCalcListStore() {
  return {
    calcListUpdateSignal
  }
}
