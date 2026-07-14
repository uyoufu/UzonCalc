import CollapseRight from 'src/components/collapseIcon/CollapseRight.vue'
import { useWindowSize } from '@vueuse/core'
import { ref, watch } from 'vue'

/**
 * 使用折叠功能
 * @param splitterModel
 * @param splitterLimitsRef
 * @param defaultLimits
 * @returns
 */
export function useCollapse (splitterModel: Ref<number>, splitterLimitsRef: Ref<[number, number]>, defaultLimits: [number, number]) {
  // #region 向右折叠
  const isCollapsed = ref(false)
  const lastSplitterModel = ref(splitterModel.value)
  watch(isCollapsed, (newVal) => {
    if (newVal) {
      // 折叠
      lastSplitterModel.value = splitterModel.value
      splitterLimitsRef.value = [0, 100]
      splitterModel.value = 100
    } else {
      // 展开
      splitterLimitsRef.value = defaultLimits
      splitterModel.value = lastSplitterModel.value
    }
  })

  // 当窗体大小变化时，根据大小进行折叠状态调整
  const { width } = useWindowSize()
  watch(width, (newWidth) => {
    if (newWidth < 600) {
      // 窗体较小，自动折叠
      isCollapsed.value = true
    } else {
      // 窗体较大，恢复上次状态
      isCollapsed.value = false
    }
  }, { immediate: true })
  // #endregion

  return {
    isCollapsed,
    CollapseRight
  }
}
