<template>
  <q-list dense class="column no-wrap justify-start">
    <q-item class="plain-list__item text-primary bg-grey-11" v-ripple>
      <q-item-section avatar class="q-pr-none">
        <q-icon :name="header.icon" />
      </q-item-section>

      <q-item-section class="q-px-lg q-py-sm text-bold">
        {{ header.label }}
        <AsyncTooltip v-if="!readonly" :tooltip="t('categoryList.youCanRightClickToAddNewCategory')" />
      </q-item-section>

      <ContextMenu v-if="!readonly" :items="headerContextMenuItems"></ContextMenu>

      <q-item-section v-if="!readonly" side>
        <q-btn icon="add" dense flat size="md" @click.stop="onCreateCategory">
          <AsyncTooltip :tooltip="t('categoryList.newCategory')" />
        </q-btn>
      </q-item-section>
    </q-item>

    <q-item class="plain-list__item q-mt-xs">
      <SearchInput dense v-model="filter" class="full-width" />
    </q-item>

    <q-list class="col scroll-y hover-scroll q-mt-xs" dense>
      <draggable v-model="draggableList" group="people" item-key="id" @end="onDragEnd" :disabled="disabledDrag">
        <template #item="{ element: item }">
          <q-item class="plain-list__item" :key="item.name" clickable v-ripple :active="item.active"
            active-class="text-primary" @click="onItemClick(item)">
            <div class="row justify-between no-wrap items-center full-width">
              <div class="row justify-start items-center col">
                <div>
                  <q-icon color="primary" v-if="item.icon" :name="item.icon" size="sm" />
                  <q-checkbox v-if="selectable && item.selectable !== false" dense v-model="item.selected"
                    @click="onItemCheckboxClicked(item)" color="secondary" class="q-ml-sm" keep-color>
                  </q-checkbox>
                </div>

                <div class="q-ml-sm text-bold" v-if="item.name">{{ item.name }}
                </div>
              </div>

              <div side v-if="item.total">{{ item.total }}
              </div>
              <AsyncTooltip v-if="item.description" :tooltip="item.description" />
            </div>

            <ContextMenu v-if="!readonly" :items="itemContextMenuItems" :value="item"></ContextMenu>
          </q-item>
        </template>
      </draggable>
    </q-list>
  </q-list>
</template>

<script lang="ts" setup>
import { t, translateGlobal } from 'src/i18n/helpers'
import type { PropType } from 'vue'
import type { createCategoryFunc, deleteCategoryByIdFunc, getCategoriesFunc, ICategoryInfo, IFlatHeader, updateCategoryFunc } from './types'
import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'
import AsyncTooltip from 'src/components/asyncTooltip/AsyncTooltip.vue'
import SearchInput from 'src/components/searchInput/SearchInput.vue'
import type { IContextMenuItem } from 'src/components/contextMenu/types'

const modelValue = defineModel<ICategoryInfo>()
const selectedValues = defineModel<ICategoryInfo[]>('selected', {
  type: Array as PropType<ICategoryInfo[]>,
  default: () => []
})
function onItemCheckboxClicked(categoryInfo: ICategoryInfo) {
  // 已经修改emailGroup的值后，才触发的事件
  // console.log('onItemCheckboxClicked', emailGroup.selected)
  if (categoryInfo.selected) {
    if (!selectedValues.value.some(x => x.id === categoryInfo.id)) { selectedValues.value.push(categoryInfo) }
  } else { selectedValues.value = selectedValues.value.filter(x => x.id !== categoryInfo.id) }
}

const props = defineProps({
  // 树形结构顶部的菜单
  // 通过 order 来控制显示位置
  extraItems: {
    type: Array as PropType<ICategoryInfo[]>,
    default: () => []
  },

  // 只读模式
  readonly: {
    type: Boolean,
    default: false
  },

  // 是否允许选择
  selectable: {
    type: Boolean,
    default: false
  },

  // 右键菜单
  contextMenuItems: {
    type: Array as PropType<IContextMenuItem[]>,
    default: () => []
  },

  header: {
    type: Object as PropType<IFlatHeader>,
    default: () => ({ label: 'Category', icon: 'group' })
  },

  getCategories: {
    type: Function as PropType<getCategoriesFunc>,
    required: true
  },

  createCategory: {
    type: Function as PropType<createCategoryFunc>,
    required: true
  },

  updateCategory: {
    type: Function as PropType<updateCategoryFunc>,
    required: true
  },

  deleteCategoryById: {
    type: Function as PropType<deleteCategoryByIdFunc>,
    required: true
  }
})

const filter = ref('')
const categoryItems = ref<ICategoryInfo[]>([])
const filteredItems = computed(() => {
  const results = []
  if (props.extraItems.length > 0) {
    results.push(...props.extraItems)
  }
  results.push(...categoryItems.value)
  results.sort((a, b) => a.order - b.order)
  // 然后按是否选中排序
  results.sort((a, b) => (b.selected ? 1 : 0) - (a.selected ? 1 : 0))

  if (!filter.value) return results
  return results.filter(x => x.name.indexOf(filter.value) > -1)
})

// 初始化获取组
import type { IPopupDialogField, IPopupDialogParams } from 'src/components/popupDialog/types'
import { PopupDialogFieldType } from 'src/components/popupDialog/types'
import { showDialog } from 'src/components/popupDialog/PopupDialog'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'
onMounted(async () => {
  const groups = await props.getCategories()
  categoryItems.value = groups.map(x => {
    // 判断是否有初始值，若有，则恢复选中状态
    if (selectedValues.value.some(y => y.id === x.id)) {
      x.selected = true
    } else {
      x.selected = false
    }
    return { ...x, active: false }
  })

  // 默认选中第一个
  if (filteredItems.value.length > 0) {
    activeCategory(filteredItems.value[0] as ICategoryInfo)
  }
})
function activeCategory(group: ICategoryInfo) {
  categoryItems.value.forEach(x => { x.active = false })
  group.active = true
  modelValue.value = group
}

function onItemClick(item: ICategoryInfo) {
  activeCategory(item)
}

// #region 右键菜单相关
// 构建分类表单字段
function buildCategoryFields(category?: ICategoryInfo) {
  const fields: IPopupDialogField[] = [
    {
      name: 'name',
      label: t('categoryList.field_name'),
      value: category ? category.name : '',
      type: PopupDialogFieldType.text,
      required: true,
      validate: (value: string) => {
        // 必须仅包含字母、数字、下划线且不能以数字开头
        const valid = /^[A-Za-z_][A-Za-z0-9_]*$/.test(value)
        if (!valid) {
          return {
            ok: false,
            message: t('categoryList.onlyLettersNumbersUnderscoresAndCannotStartWithNumber')
          }
        }
        return { ok: true }
      }
    },
    {
      name: 'description',
      label: t('categoryList.field_description'),
      value: category ? category.description || '' : '',
      type: PopupDialogFieldType.textarea
    }
  ]

  return fields
}

// 新增分类
async function onCreateCategory() {
  const popupParams: IPopupDialogParams = {
    title: t('categoryList.newCategory'),
    fields: buildCategoryFields(),
    oneColumn: true
  }
  const result = await showDialog<ICategoryInfo>(popupParams)
  if (!result.ok) return

  // 添加默认的 icon
  const newCategory = await props.createCategory(result.data)

  categoryItems.value.push({
    ...newCategory,
    active: false
  })

  // 设置新组为当前组
  activeCategory(categoryItems.value[categoryItems.value.length - 1] as ICategoryInfo)

  // 新增组
  notifySuccess(t('categoryList.newCategorySuccess'))
}
// 分类 header 右键
const headerContextMenuItems: ComputedRef<IContextMenuItem[]> = computed(() => [
  {
    name: 'add',
    label: translateGlobal('new'),
    tooltip: t('categoryList.newCategory'),
    onClick: onCreateCategory
  }
])

/**
 * 具体分类上的右键菜单
 */

// 修改分类
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function onModifyCategory(categoryDetails: Record<string, any>) {
  const categoryInfo = categoryDetails as ICategoryInfo
  const popupParams: IPopupDialogParams = {
    title: t('categoryList.modifyCategory'),
    fields: buildCategoryFields(categoryInfo),
    oneColumn: true
  }
  const result = await showDialog<ICategoryInfo>(popupParams)
  if (!result.ok) return

  // 指定 id 和 oid
  result.data.id = categoryInfo.id
  result.data.oid = categoryInfo.oid

  await props.updateCategory(result.data)

  // 更新数据
  categoryInfo.name = result.data.name
  categoryInfo.description = result.data.description

  // 修改分类成功
  notifySuccess(t('categoryList.newCategorySuccess'))
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function onDeleteCategory(categoryDetails: Record<string, any>) {
  // 进行确认
  const confirm = await confirmOperation(
    translateGlobal('deleteConfirmation'),
    t('categoryList.deleteCategoryConfirm', { label: categoryDetails.name })
  )
  if (!confirm) return

  // 向服务器请求删除
  await props.deleteCategoryById(categoryDetails.oid)

  // 从当前列表中清除组
  const groupIndex = categoryItems.value.findIndex(x => x.oid === categoryDetails.oid)
  categoryItems.value.splice(groupIndex, 1)

  // 切换到临近的组
  const newIndex = Math.max(0, groupIndex - 1)
  if (categoryItems.value.length > 0) {
    categoryItems.value[newIndex]!.active = true
    modelValue.value = categoryItems.value[newIndex]
  } else {
    modelValue.value = {
      oid: "all",
      name: 'all',
      description: '',
      order: 0
    }
  }

  notifySuccess(t('categoryList.deleteCategorySuccess', { label: categoryDetails.name }))
}
const itemContextMenuItems: ComputedRef<IContextMenuItem[]> = computed(() => [
  ...props.contextMenuItems,
  ...headerContextMenuItems.value,
  {
    name: 'modify',
    label: translateGlobal('modify'),
    tooltip: t('categoryList.modifyCategory'),
    onClick: onModifyCategory
  },
  {
    name: 'delete',
    label: translateGlobal('delete'),
    color: 'negative',
    tooltip: t('categoryList.deleteCategory'),
    onClick: onDeleteCategory
  }
])
// #endregion

// #region 拖拽排序
import draggable from 'vuedraggable'
const draggableList: Ref<ICategoryInfo[]> = ref([])
watch(filteredItems, (newVal) => {
  draggableList.value = [...newVal]
})
const disabledDrag = computed(() => {
  return !!filter.value || draggableList.value.length <= 1
})
export interface IDragEndEvent {
  oldIndex: number
  newIndex: number
}

async function onDragEnd(evt: IDragEndEvent) {
  // 刷新 order 顺序

}
// #endregion
</script>

<style lang="scss" scoped>
.plain-list__item {
  :deep(.q-item__section--avatar) {
    min-width: auto !important;
  }
}
</style>
