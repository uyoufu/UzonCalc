<template>
  <div class="workspace-pane column no-wrap">
    <div class="workspace-toolbar row items-center q-gutter-xs q-px-sm">
      <q-btn flat round dense icon="arrow_back" @click="onBackToReports"><q-tooltip>{{
        t('calcWorkspace.backToReports') }}</q-tooltip></q-btn>
      <template v-if="isNew">
        <q-select v-model="createForm.categoryOid" dense outlined emit-value map-options :options="categoryOptions"
          :label="t('calcWorkspace.categoryName')" class="workspace-toolbar__category" />
        <q-input v-model="createForm.name" dense outlined :label="t('calcWorkspace.reportName')"
          class="workspace-toolbar__name" />
      </template>
      <template v-else>
        <span class="workspace-toolbar__category-display text-caption text-grey-7 ellipsis">{{ reportCategoryName
          }}</span>
        <span class="workspace-toolbar__name-display text-subtitle2 ellipsis">{{ report?.name || '-' }}</span>
      </template>
      <q-separator vertical inset />
      <CommonBtn icon="save" :label="t('global.save')" :tooltip="t('calcWorkspace.saveWorkspace')"
        :loading="draft.isSaving.value" :disable="!draft.hasUnsavedChanges.value" @click="onSave" />
      <q-btn flat round dense icon="play_arrow" color="positive" @click="onRunWorkspace"><q-tooltip>{{
        t('calcWorkspace.runWorkspace') }}</q-tooltip></q-btn>
      <q-btn flat round dense icon="format_align_left" :disable="!selectedFile?.path.endsWith('.py')"
        @click="onFormatFile"><q-tooltip>{{ t('calcWorkspace.format') }}</q-tooltip></q-btn>
      <q-separator vertical inset />
      <q-chip dense square :color="draft.hasUnsavedChanges.value ? 'warning' : 'positive'" text-color="white">
        {{ draft.hasUnsavedChanges.value ? t('calcWorkspace.unsaved') : t('calcWorkspace.saved') }}
      </q-chip>
      <span class="text-caption text-grey-7">rev {{ draft.workspaceRevision.value }}</span>
      <q-space />
      <template v-if="report">
        <q-chip dense square :color="publishColor" text-color="white">{{
          t(`calcWorkspace.publishStates.${report.publishState}`) }}</q-chip>
        <q-chip dense square :color="buildColor" text-color="white">{{
          t(`calcWorkspace.buildStates.${report.buildStatus}`) }}</q-chip>
      </template>
    </div>
    <q-separator />
    <div class="row no-wrap col workspace-body">
      <WorkspaceTreePanel :nodes="draft.treeNodes.value" :entry-path="draft.entryPath.value" @select="onSelectFile"
        @create="onCreateFile" @upload="onUploadResources" @rename="onRenamePath" @delete="onDeletePath"
        @entry="draft.setEntryPath" @dependencies="onOpenDependencyDialog" />
      <main class="col workspace-main">
        <template v-if="selectedFile">
          <div class="workspace-filebar row items-center q-px-sm">
            <q-icon :name="selectedFile.isText ? 'description' : 'attach_file'" class="q-mr-xs" />
            <span class="text-caption ellipsis">{{ selectedFile.path }}</span>
            <q-space /><span class="text-caption text-grey-6">{{ formatBytes(selectedFile.size) }}</span>
          </div>
          <q-separator />
          <WorkspaceCodeEditor v-if="selectedFile.isText && selectedFile.text !== null" class="col"
            :path="selectedFile.path" :content="selectedFile.text" @change="draft.updateText" />
          <div v-else-if="isImage && objectUrl" class="col column items-center justify-center resource-preview">
            <img :src="objectUrl" :alt="selectedFile.path">
            <CommonBtn class="q-mt-md" icon="download" color="grey-8" :label="t('calcWorkspace.download')"
              @click="onDownloadSelected" />
          </div>
          <div v-else class="col column items-center justify-center text-grey-7">
            <q-icon name="drafts" size="48px" />
            <div class="q-mt-sm">{{ t('calcWorkspace.binaryResource') }}</div>
            <CommonBtn class="q-mt-md" icon="download" color="grey-8" :label="t('calcWorkspace.download')"
              @click="onDownloadSelected" />
          </div>
        </template>
        <div v-else class="full-height column items-center justify-center text-grey-6"><q-icon name="code"
            size="48px" />
          <div>{{ t('calcWorkspace.selectFile') }}</div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
/** Complete multi-file workspace editor with atomic explicit saves. */
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import WorkspaceTreePanel from './WorkspaceTreePanel.vue'
import WorkspaceCodeEditor from './WorkspaceCodeEditor.vue'
import { useWorkspaceDraft, type WorkspaceDraftFile } from './useWorkspaceDraft'
import { useDependencyDialog } from './useDependencyDialog'
import { useWorkspaceConflictDialog } from './useWorkspaceConflictDialog'
import { WorkspaceConflictResolution } from './workspaceConflict'
import type { CalcReport, CalcReportCategory } from 'src/api/calc/types'
import { CalcErrorCode } from 'src/api/calc/types'
import { getWorkspace, saveWorkspace } from 'src/api/calc/workspace'
import { listReportCategories } from 'src/api/calc/categories'
import { formatPythonByBlack } from 'src/api/codeFormat'
import { getApiFailure } from '../../shared/apiFailure'
import { confirmOperation, notifyError, notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'

const props = defineProps<{ reportOid: string; report: CalcReport | null; isNew: boolean }>()
const emit = defineEmits<{ saved: [reportOid: string] }>()
const route = useRoute()
const router = useRouter()
const reportOidRef = computed(() => props.reportOid)
const draft = useWorkspaceDraft(reportOidRef)
const selectedPath = ref('')
const categories = ref<CalcReportCategory[]>([])
const createForm = reactive({ categoryOid: '', name: '', description: '' })
const { openDependencyDialog } = useDependencyDialog()
const { openWorkspaceConflictDialog } = useWorkspaceConflictDialog()
const objectUrl = ref('')
const selectedFile = computed(() => draft.files.value.find((file) => file.path === selectedPath.value) || null)
const categoryOptions = computed(() => categories.value.map((category) => ({ label: category.name, value: category.categoryOid })))
const reportCategoryName = computed(() => categories.value.find((category) => category.categoryOid === props.report?.categoryOid)?.name || '-')
const isImage = computed(() => Boolean(selectedFile.value && /\.(png|jpe?g|gif|webp|svg)$/i.test(selectedFile.value.path)))
const publishColor = computed(() => ({ published: 'positive', unpublished: 'grey-7', unpublished_changes: 'warning', workspace_version_mismatch: 'deep-orange' })[props.report?.publishState || 'unpublished'])
const buildColor = computed(() => ({ not_requested: 'grey-6', pending: 'blue-grey', building: 'info', ready: 'positive', failed: 'negative' })[props.report?.buildStatus || 'not_requested'])

/** Initialize either a new local draft or an existing server workspace. */
async function initialize(): Promise<void> {
  const categoryResponse = await listReportCategories()
  categories.value = categoryResponse.data || []
  if (props.isNew) {
    draft.initializeNewWorkspace()
    createForm.categoryOid = String(route.query.categoryOid || categories.value[0]?.categoryOid || '')
    createForm.name = t('calcWorkspace.untitledReport')
  } else {
    const response = await getWorkspace(props.reportOid)
    draft.initializeFromSnapshot(response.data)
  }
  await onSelectFile(draft.entryPath.value)
}

onMounted(initialize)
watch(() => props.reportOid, initialize)

/** Return to the report list while preserving the workspace leave guard. */
async function onBackToReports(): Promise<void> {
  await router.push('/calc-report/list')
}

/** Load and select one workspace file. */
async function onSelectFile(path: string): Promise<void> {
  const file = draft.files.value.find((candidate) => candidate.path === path)
  if (!file) return
  await draft.ensureFileLoaded(file)
  selectedPath.value = path
  refreshObjectUrl(file)
}
/** Refresh the preview URL for one loaded binary file. */
function refreshObjectUrl(file: WorkspaceDraftFile): void {
  if (objectUrl.value) URL.revokeObjectURL(objectUrl.value)
  objectUrl.value = !file.isText && file.content ? URL.createObjectURL(file.content) : ''
}
/** Create a new workspace text file. */
async function onCreateFile(path: string): Promise<void> {
  try { const file = draft.addFile(path, ''); await onSelectFile(file.path) } catch (error) { notifyError(getApiFailure(error).message) }
}
/** Add selected local files under resources/. */
function onUploadResources(localFiles: File[]): void {
  localFiles.forEach((file) => {
    try { draft.addFile(`resources/${file.name}`, file) } catch (error) { notifyError(getApiFailure(error).message) }
  })
}
/** Open dependency editing and apply only a confirmed detached result. */
async function onOpenDependencyDialog(): Promise<void> {
  const dependencies = await openDependencyDialog(props.reportOid, draft.dependencies.value)
  if (dependencies) draft.setDependencies(dependencies)
}
/** Rename a file/folder and keep the current selection aligned. */
async function onRenamePath(oldPath: string, newPath: string): Promise<void> {
  try {
    await draft.renamePath(oldPath, newPath)
    if (selectedPath.value === oldPath || selectedPath.value.startsWith(`${oldPath}/`)) selectedPath.value = `${newPath}${selectedPath.value.slice(oldPath.length)}`
  } catch (error) { notifyError(getApiFailure(error).message) }
}
/** Delete a file/folder from the local snapshot. */
function onDeletePath(path: string): void {
  try { draft.deletePath(path); if (!draft.files.value.some((file) => file.path === selectedPath.value)) selectedPath.value = '' } catch (error) { notifyError(getApiFailure(error).message) }
}
/** Format the active Python file through the backend Black endpoint. */
async function onFormatFile(): Promise<void> {
  if (!selectedFile.value?.text) return
  const response = await formatPythonByBlack({ code: selectedFile.value.text })
  draft.updateText(selectedFile.value.path, response.data.formattedCode)
}

/** Save the complete optimistic workspace and handle revision conflicts safely. */
async function onSave(): Promise<boolean> {
  if (props.isNew && (!createForm.categoryOid || !createForm.name.trim())) { notifyError(t('calcWorkspace.metadataRequired')); return false }
  draft.isSaving.value = true
  try {
    const create = props.isNew ? { ...createForm, name: createForm.name.trim() } : undefined
    const payload = draft.buildSavePayload(create)
    const response = await saveWorkspace(props.reportOid, payload.snapshot, payload.uploads)
    draft.markSaved(response.data)
    notifySuccess(t('calcWorkspace.workspaceSaved'))
    emit('saved', props.reportOid)
    if (props.isNew) await router.replace(`/calc-report/${props.reportOid}/workspace`)
    return true
  } catch (error) {
    const failure = getApiFailure(error)
    if (failure.errorCode === CalcErrorCode.WorkspaceRevisionConflict) await showConflictDialog()
    else notifyError(failure.message)
    return false
  } finally { draft.isSaving.value = false }
}

/** Present recovery choices and execute only a confirmed action. */
async function showConflictDialog(): Promise<void> {
  const resolution = await openWorkspaceConflictDialog()
  if (resolution) await onConflictChoice(resolution)
}
/** Execute the selected revision-conflict recovery action. */
async function onConflictChoice(resolution: WorkspaceConflictResolution): Promise<void> {
  if (resolution === WorkspaceConflictResolution.ExportLocalZip) {
    await draft.exportLocalZip(`${createForm.name || props.report?.name || 'workspace'}-conflict.zip`)
    return
  }
  await initialize()
}
/** Save dirty workspace state before running the workspace source. */
async function onRunWorkspace(): Promise<void> {
  if (draft.hasUnsavedChanges.value && !await onSave()) return
  await router.push({ path: `/calc-report/${props.reportOid}/run`, query: { source: 'workspace' } })
}
/** Download the active binary resource. */
function onDownloadSelected(): void {
  if (!selectedFile.value?.content) return
  const url = URL.createObjectURL(selectedFile.value.content)
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = selectedFile.value.path.split('/').pop() || 'resource'; anchor.click(); URL.revokeObjectURL(url)
}
/** Format a byte count for the file status bar. */
function formatBytes(size: number): string { return size < 1024 ? `${size} B` : size < 1048576 ? `${(size / 1024).toFixed(1)} KB` : `${(size / 1048576).toFixed(1)} MB` }

/** Confirm navigation while the current workspace has local changes. */
onBeforeRouteLeave(async () => !draft.hasUnsavedChanges.value || await confirmOperation(
  t('calcWorkspace.unsaved'),
  t('calcWorkspace.leaveWithoutSaving')
))
/** Prevent browser-level navigation from silently discarding local edits. */
function onBeforeUnload(event: BeforeUnloadEvent): void { if (draft.hasUnsavedChanges.value) event.preventDefault() }
/** Register the explicit save shortcut. */
function onKeydown(event: KeyboardEvent): void { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') { event.preventDefault(); void onSave() } }
onMounted(() => { window.addEventListener('beforeunload', onBeforeUnload); window.addEventListener('keydown', onKeydown) })
onUnmounted(() => { window.removeEventListener('beforeunload', onBeforeUnload); window.removeEventListener('keydown', onKeydown); if (objectUrl.value) URL.revokeObjectURL(objectUrl.value) })
</script>

<style scoped>
.workspace-pane {
  height: 100%;
  min-height: 620px;
  background: #f8fafc;
}

.workspace-toolbar {
  min-height: 56px;
  background: #fff;
  overflow-x: auto;
}

.workspace-toolbar__category {
  width: 180px;
}

.workspace-toolbar__name {
  width: 220px;
}

.workspace-toolbar__category-display {
  width: 140px;
  min-width: 100px;
}

.workspace-toolbar__name-display {
  width: 220px;
  min-width: 140px;
}

.workspace-body {
  min-height: 0;
}

.workspace-main {
  min-width: 0;
  background: #fff;
}

.workspace-filebar {
  min-height: 34px;
  background: #f8fafc;
}

.resource-preview {
  overflow: auto;
}

.resource-preview img {
  max-width: 90%;
  max-height: 75%;
  object-fit: contain;
}
</style>
