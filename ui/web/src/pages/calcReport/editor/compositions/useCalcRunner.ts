import type { Ref } from 'vue'

export function useCalcRunner(
  startExecutingSignal: Ref<number>,
  isExecuting: Ref<boolean>,
  onSaveCalcReport: () => Promise<boolean>
) {
  async function onStartExecuting() {
    // 如果已在执行中，则不重复执行
    if (isExecuting.value) return

    // 先保存报告
    const saveSuccess = await onSaveCalcReport()
    if (!saveSuccess) {
      return
    }

    // 触发执行信号，每次触发时增加这个数字
    // 监听这个数字的组件（CodePreviewer）会在这个数字变化时执行对应逻辑
    startExecutingSignal.value++
  }

  // 注册快捷键 F5 触发执行
  async function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'F5') {
      event.preventDefault()
      await onStartExecuting()
    }
  }
  onMounted(() => {
    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    window.addEventListener('keydown', handleKeyDown)
  })
  onUnmounted(() => {
    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    window.removeEventListener('keydown', handleKeyDown)
  })

  return {
    onStartExecuting
  }
}
