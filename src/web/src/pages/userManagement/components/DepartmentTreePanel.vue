<template>
  <aside class="department-panel column no-wrap">
    <div class="department-panel__header row items-center q-px-sm">
      <div class="text-subtitle2">{{ t('userManagement.departments') }}</div>
      <q-space />
      <CommonBtn flat dense icon="add" :tooltip="t('userManagement.addDepartment')" @click="onCreateDepartment(null)" />
    </div>
    <q-separator />
    <DraggableTree v-model:current-node-key="currentDepartmentOid" class="col scroll" :data="treeNodes" node-key="id"
      draggable default-expand-all :context-menu-items="contextMenuItems" :empty-context-menu-items="emptyMenuItems"
      @node-click="onNodeClick" @node-drop="onNodeDrop" />
  </aside>
</template>

<script setup lang="ts">
/** Draggable department tree with validated CRUD context menus. */
import DraggableTree from 'src/components/draggableTree/DraggableTree.vue'
import type { DraggableTreeContextValue, DraggableTreeEmptyContextValue, TreeDropType } from 'src/components/draggableTree/types'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import { createDepartment, deleteDepartment, moveDepartment, updateDepartment, type DepartmentNode } from 'src/api/adminUsers'
import { confirmOperation } from 'src/utils/dialog'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { t } from 'src/i18n/helpers'
import type { TreeNodeData } from 'element-plus/es/components/tree/src/tree.type'

const props = defineProps<{ departments: DepartmentNode[] }>()
const selectedDepartmentOid = defineModel<string | null>({ default: null })
const emit = defineEmits<{ changed: [] }>()
const currentDepartmentOid = computed({ get: () => selectedDepartmentOid.value, set: (value) => { selectedDepartmentOid.value = value ? String(value) : null } })
const treeNodes = computed(() => props.departments.map((department) => ({
  id: department.departmentOid,
  parentId: department.parentOid,
  label: department.name,
  sort: department.sortOrder,
  department
})))

/** Open a department name form and create beneath the selected parent. */
async function onCreateDepartment(parentOid: string | null): Promise<void> {
  const result = await showDialog<{ name: string }>({ title: t('userManagement.addDepartment'), oneColumn: true, fields: [{ name: 'name', label: t('userManagement.departmentName'), required: true }] })
  if (!result.ok) return
  await createDepartment(result.data.name, parentOid)
  emit('changed')
}

/** Rename one selected department. */
async function onRenameDepartment(department: DepartmentNode): Promise<void> {
  const result = await showDialog<{ name: string }>({ title: t('userManagement.renameDepartment'), oneColumn: true, fields: [{ name: 'name', label: t('userManagement.departmentName'), value: department.name, required: true }] })
  if (!result.ok) return
  await updateDepartment(department.departmentOid, result.data.name)
  emit('changed')
}

/** Delete a confirmed empty leaf department. */
async function onDeleteDepartment(department: DepartmentNode): Promise<void> {
  if (!await confirmOperation(t('global.deleteConfirmation'), department.name)) return
  await deleteDepartment(department.departmentOid)
  emit('changed')
}

const contextMenuItems: IContextMenuItem<DraggableTreeContextValue>[] = [
  { name: 'add-sibling', label: t('userManagement.addSiblingDepartment'), icon: 'add', color: 'primary', onClick: ({ data }) => onCreateDepartment((data.department as DepartmentNode).parentOid) },
  { name: 'add-child', label: t('userManagement.addChildDepartment'), icon: 'subdirectory_arrow_right', color: 'primary', onClick: ({ data }) => onCreateDepartment((data.department as DepartmentNode).departmentOid) },
  { name: 'rename', label: t('global.edit'), icon: 'edit', color: 'grey-9', onClick: ({ data }) => onRenameDepartment(data.department as DepartmentNode) },
  { name: 'delete', label: t('global.delete'), icon: 'delete', color: 'negative', onClick: ({ data }) => onDeleteDepartment(data.department as DepartmentNode) }
]
const emptyMenuItems: IContextMenuItem<DraggableTreeEmptyContextValue>[] = [
  { name: 'add', label: t('userManagement.addDepartment'), icon: 'add', color: 'primary', onClick: () => onCreateDepartment(null) }
]

/** Select one department as the user-table subtree filter. */
function onNodeClick(data: TreeNodeData): void {
  selectedDepartmentOid.value = String(data.id)
}

/** Persist a tree drop as a parent and sibling position update. */
async function onNodeDrop(dragging: { data: TreeNodeData }, drop: { data: TreeNodeData }, type: TreeDropType): Promise<void> {
  const target = drop.data.department as DepartmentNode
  await moveDepartment(String(dragging.data.id), type === 'inner' ? target.departmentOid : target.parentOid, target.sortOrder)
  emit('changed')
}
</script>

<style scoped>
.department-panel { width: 280px; min-width: 280px; border-right: 1px solid #e4e7ec; }
.department-panel__header { min-height: 44px; }
</style>
