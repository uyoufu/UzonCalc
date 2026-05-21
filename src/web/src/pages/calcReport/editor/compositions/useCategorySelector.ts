import { getCalcReportCategories } from 'src/api/calcReportCategory'
import type { ICategoryInfo } from 'src/components/categoryList/types'
import type { Ref } from 'vue'
import { computed, ref } from 'vue'

export function useCategorySelector(calcCategoryOid: Ref<string>) {
  const allCategories = ref<ICategoryInfo[]>([])
  onMounted(async () => {
    const { data } = await getCalcReportCategories()
    allCategories.value = data
    categoryOptions.value = fullCategoryOptions.value
  })

  const categoryInfo = computed(() => {
    return (
      allCategories.value.find((cat) => cat.oid === calcCategoryOid.value) || {
        name: '',
        oid: '',
        order: 0
      }
    )
  })
  const calcCategoryName = computed(() => categoryInfo.value.name)

  const fullCategoryOptions = computed(() => {
    return allCategories.value.map((cat) => ({
      label: cat.name,
      value: cat.oid
    }))
  })
  const categoryOptions: Ref<{ label: string; value: string }[]> = ref([])
  function onFilterReportCategory(val: string, update: (callback: () => void) => void) {
    update(() => {
      const needle = val.toLowerCase()
      if (!needle) {
        categoryOptions.value = fullCategoryOptions.value
        return
      } else {
        categoryOptions.value = fullCategoryOptions.value.filter((cat) => cat.label.toLowerCase().includes(needle))
      }
    })
  }

  return {
    categoryInfo,
    calcCategoryName,
    categoryOptions,
    fullCategoryOptions,
    onFilterReportCategory
  }
}
