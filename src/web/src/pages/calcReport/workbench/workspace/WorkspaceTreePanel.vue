<template>
  <aside class="workspace-tree column no-wrap">
    <div class="workspace-tree__toolbar row items-center q-px-xs">
      <q-btn flat round dense icon="note_add" @click="onCreateFile"><q-tooltip>{{ t('calcWorkspace.newFile') }}</q-tooltip></q-btn>
      <q-btn flat round dense icon="upload_file" @click="fileInput?.click()"><q-tooltip>{{ t('calcWorkspace.uploadResources') }}</q-tooltip></q-btn>
      <input ref="fileInput" class="hidden" type="file" multiple @change="onFilesSelected">
      <q-space /><q-btn flat round dense icon="account_tree" @click="emit('dependencies')"><q-tooltip>{{ t('calcWorkspace.dependencies') }}</q-tooltip></q-btn>
    </div>
    <q-separator />
    <DraggableTree class="col scroll" :data="nodes as never[]" node-key="id" draggable
      :allow-drag="allowDrag" :allow-drop="allowDrop" :context-menu-items="contextItems"
      @node-click="onNodeClick" @node-drop="onNodeDrop">
      <template #default="{ data }">
        <q-icon :name="data.kind === 'folder' ? 'folder' : iconForPath(data.path)" class="q-mr-xs" />
        <span class="ellipsis" :class="{ 'text-weight-bold': data.path === entryPath }">{{ data.label }}</span>
        <q-icon v-if="data.path === entryPath" name="play_arrow" color="positive" size="xs" class="q-ml-xs" />
      </template>
    </DraggableTree>
  </aside>
</template>

<script setup lang="ts">
/** File-tree controls for a complete workspace draft. */
import { Dialog } from 'quasar'
import DraggableTree from 'src/components/draggableTree/DraggableTree.vue'
import type { DraggableTreeContextValue, TreeDropType } from 'src/components/draggableTree/types'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type { WorkspaceTreeNode } from './useWorkspaceDraft'
import { t } from 'src/i18n/helpers'
import type { TreeNodeData } from 'element-plus/es/components/tree/src/tree.type'

const props = defineProps<{ nodes: WorkspaceTreeNode[]; entryPath: string }>()
const emit = defineEmits<{
  select: [path: string]
  create: [path: string]
  upload: [files: File[]]
  rename: [oldPath: string, newPath: string]
  delete: [path: string]
  entry: [path: string]
  dependencies: []
}>()
const fileInput = ref<HTMLInputElement | null>(null)

const contextItems: IContextMenuItem<DraggableTreeContextValue>[] = [
  { name: 'rename', label: t('calcWorkspace.rename'), icon: 'drive_file_rename_outline', color: 'grey-9', vif: ({ data }) => asWorkspaceNode(data).path !== 'calcbook.json', onClick: ({ data }) => onRename(asWorkspaceNode(data)) },
  { name: 'entry', label: t('calcWorkspace.setEntry'), icon: 'play_arrow', color: 'positive', vif: ({ data }) => { const node = asWorkspaceNode(data); return node.kind === 'file' && node.path.startsWith('src/') && node.path.endsWith('.py') }, onClick: ({ data }) => emit('entry', asWorkspaceNode(data).path) },
  { name: 'delete', label: t('global.delete'), icon: 'delete', color: 'negative', vif: ({ data }) => { const path = asWorkspaceNode(data).path; return path !== 'calcbook.json' && path !== props.entryPath }, onClick: ({ data }) => emit('delete', asWorkspaceNode(data).path) }
]

/** Narrow Element Plus tree data to this workspace's node contract. */
function asWorkspaceNode(data: TreeNodeData): WorkspaceTreeNode { return data as WorkspaceTreeNode }

/** Select file nodes while folder clicks only expand the tree. */
function onNodeClick(data: TreeNodeData): void { const node = asWorkspaceNode(data); if (node.kind === 'file') emit('select', node.path) }
/** Open the path prompt for a new file. */
function onCreateFile(): void {
  Dialog.create({ title: t('calcWorkspace.newFile'), prompt: { model: 'src/', type: 'text' }, cancel: true })
    .onOk((path: string) => emit('create', path))
}
/** Open the rename prompt for one file or derived folder. */
function onRename(node: WorkspaceTreeNode): void {
  Dialog.create({ title: t('calcWorkspace.rename'), prompt: { model: node.path, type: 'text' }, cancel: true })
    .onOk((path: string) => emit('rename', node.path, path))
}
/** Forward selected local files into the resources folder. */
function onFilesSelected(event: Event): void {
  const input = event.target as HTMLInputElement
  emit('upload', [...(input.files || [])])
  input.value = ''
}
/** Prevent moving the protected manifest. */
function allowDrag(node: { data: TreeNodeData }): boolean { return asWorkspaceNode(node.data).path !== 'calcbook.json' }
/** Permit drops only into valid workspace folders or adjacent valid nodes. */
function allowDrop(_dragging: { data: TreeNodeData }, drop: { data: TreeNodeData }, type: TreeDropType): boolean {
  return type !== 'inner' || asWorkspaceNode(drop.data).kind === 'folder'
}
/** Convert a tree drop into a path rename. */
function onNodeDrop(dragging: { data: TreeNodeData }, drop: { data: TreeNodeData }, type: TreeDropType): void {
  const draggingNode = asWorkspaceNode(dragging.data)
  const dropNode = asWorkspaceNode(drop.data)
  const parentPath = type === 'inner' ? dropNode.path : dropNode.parentId
  const name = draggingNode.path.split('/').pop() || draggingNode.label
  emit('rename', draggingNode.path, parentPath ? `${parentPath}/${name}` : name)
}
/** Return an icon suited to the selected file kind. */
function iconForPath(path: string): string {
  if (path.endsWith('.py')) return 'code'
  if (path.endsWith('.json')) return 'data_object'
  if (/\.(png|jpe?g|gif|webp|svg)$/i.test(path)) return 'image'
  return 'description'
}
</script>

<style scoped>
.workspace-tree { width: 250px; min-width: 250px; border-right: 1px solid #e4e7ec; background: #fff; }
.workspace-tree__toolbar { min-height: 40px; }
</style>
