<template>
  <div class="workspace-tabs row no-wrap items-stretch">
    <q-scroll-area class="col" :thumb-style="{ height: '3px' }">
      <div class="row no-wrap full-height">
        <div v-for="tab in tabs" :key="tab.id" role="tab" tabindex="0"
          class="workspace-tab row no-wrap items-center"
          :aria-selected="tab.id === activeTabId" :class="{ 'workspace-tab--active': tab.id === activeTabId }"
          @click="emit('activate', tab.id)" @keydown.enter="emit('activate', tab.id)"
          @keydown.space.prevent="emit('activate', tab.id)">
          <q-icon :name="tab.kind === WorkspaceTabKind.Run ? 'play_circle' : iconForPath(tab.path || '')" size="16px" />
          <span class="workspace-tab__label ellipsis">{{ tabLabel(tab) }}</span>
          <span v-if="tab.kind === WorkspaceTabKind.File && isDirty(tab.path)" class="workspace-tab__dirty" />
          <CommonBtn flat round dense size="xs" icon="close" :tooltip="t('calcWorkspace.closeTab')"
            @click.stop="emit('close', tab.id)" />
          <q-tooltip v-if="tab.path">{{ tab.path }}</q-tooltip>
          <ContextMenu :items="contextMenuItems" :value="tab" />
        </div>
      </div>
    </q-scroll-area>
  </div>
</template>

<script setup lang="ts">
/** Render the closable document and execution tabs for a workspace. */
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'
import { t } from 'src/i18n/helpers'
import { WorkspaceTabKind, type WorkspaceTab } from './useWorkspaceTabs'
import {
  useWorkspaceTabContextMenu,
  type WorkspaceTabMenuCommand
} from './useWorkspaceTabContextMenu'

const props = defineProps<{
  tabs: WorkspaceTab[]
  activeTabId: string
  dirtyPaths: string[]
}>()
const emit = defineEmits<{
  activate: [tabId: string]
  close: [tabId: string]
  menu: [command: WorkspaceTabMenuCommand, tabId: string]
}>()
const contextMenuItems = useWorkspaceTabContextMenu((command, tab) => emit('menu', command, tab.id))

/** Return the compact visible label for one tab. */
function tabLabel(tab: WorkspaceTab): string {
  if (tab.kind === WorkspaceTabKind.Run) return t('calcWorkspace.run')
  return tab.path?.split('/').pop() || tab.path || '-'
}

/** Return whether a file tab represents an unsaved draft file. */
function isDirty(path: string | null): boolean {
  return Boolean(path && props.dirtyPaths.includes(path))
}

/** Resolve a familiar icon for one workspace file path. */
function iconForPath(path: string): string {
  if (path.endsWith('.py')) return 'code'
  if (path.endsWith('.json')) return 'data_object'
  if (/\.(png|jpe?g|gif|webp|svg)$/i.test(path)) return 'image'
  return 'description'
}
</script>

<style scoped>
.workspace-tabs {
  height: 38px;
  min-height: 38px;
  border-bottom: 1px solid #dfe3e8;
  background: #f4f6f8;
}

.workspace-tab {
  width: 180px;
  min-width: 120px;
  max-width: 220px;
  height: 38px;
  padding: 0 4px 0 10px;
  gap: 6px;
  border: 0;
  border-right: 1px solid #dfe3e8;
  border-top: 2px solid transparent;
  background: #eef1f4;
  color: #5f6670;
  cursor: pointer;
  font: inherit;
}

.workspace-tab--active {
  border-top-color: var(--q-primary);
  background: #fff;
  color: #20252b;
}

.workspace-tab__label {
  flex: 1;
  min-width: 0;
  text-align: left;
  font-size: 12px;
}

.workspace-tab__dirty {
  width: 8px;
  height: 8px;
  flex: none;
  border-radius: 50%;
  background: var(--q-warning);
}
</style>
