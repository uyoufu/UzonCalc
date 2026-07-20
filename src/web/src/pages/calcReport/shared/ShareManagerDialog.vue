<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide" persistent>
    <q-card class="share-dialog">
      <q-card-section class="row items-center q-py-sm">
        <div class="text-subtitle1">{{ t('calcWorkspace.shareReport') }} · {{ reportName }}</div>
        <q-space />
        <CommonBtn flat dense icon="close" :tooltip="t('global.close')" @click="onDialogCancel" />
      </q-card-section>
      <q-separator />
      <q-card-section class="share-form">
        <div class="share-form__grid">
          <q-select v-model="versionName" dense options-dense outlined emit-value map-options
            :label="t('calcWorkspace.version')" :options="versionOptions" />
          <q-select v-model="accessType" dense options-dense outlined emit-value map-options
            :label="t('calcWorkspace.accessType')" :options="accessOptions" />
          <q-select v-if="accessType === ShareAccessType.SpecifiedUsers" v-model="recipientUserOids"
            class="share-form__wide" use-input use-chips multiple dense options-dense outlined emit-value map-options
            :loading="isSearchingUsers" :label="t('calcWorkspace.recipientUsers')" :options="userOptions"
            @filter="onFilterUsers" />
          <q-select v-if="accessType === ShareAccessType.SpecifiedDepartments" v-model="recipientDepartmentOids"
            class="share-form__wide" use-chips multiple dense options-dense outlined emit-value map-options
            :label="t('calcWorkspace.recipientDepartments')" :options="departmentOptions" />
          <div class="permission-band share-form__wide row items-center q-gutter-lg q-px-sm q-py-xs">
            <q-toggle v-model="canEdit" :label="t('calcWorkspace.canEdit')" />
            <q-toggle v-model="canShare" :label="t('calcWorkspace.canShare')" />
          </div>
          <q-input v-model="expiresAt" dense outlined type="datetime-local" :label="t('calcWorkspace.expiresAt')" />
          <q-input v-model.number="maxUseCount" dense outlined type="number" min="1"
            :label="t('calcWorkspace.maxUseCount')" />
          <q-input v-model="note" class="share-form__wide" dense outlined type="textarea" autogrow maxlength="500"
            :label="t('calcWorkspace.shareNote')" />
        </div>
        <div class="row justify-end q-gutter-sm q-mt-md">
          <CommonBtn v-if="editingShareOid" flat icon="close" :label="t('global.cancel')" @click="resetForm" />
          <CommonBtn :icon="editingShareOid ? 'save' : 'add_link'"
            :label="t(editingShareOid ? 'global.save' : 'calcWorkspace.createLink')" :loading="isSaving"
            :disable="!canSaveLink" @click="onSaveLink" />
        </div>
      </q-card-section>
      <q-separator />
      <q-list separator class="share-dialog__list">
        <q-item v-for="link in links" :key="link.shareOid">
          <q-item-section>
            <q-item-label>{{ link.versionName }} · {{ accessLabel(link.accessType) }}</q-item-label>
            <q-item-label caption>{{ permissionLabel(link) }} · {{ link.useCount }} / {{ link.maxUseCount ?? '∞' }}</q-item-label>
            <q-item-label v-if="link.note" caption>{{ link.note }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <div class="row no-wrap q-gutter-xs">
              <CommonBtn v-if="link.shareUrl" flat dense icon="content_copy" :tooltip="t('calcWorkspace.copyLink')"
                @click="onCopyLink(link.shareUrl)" />
              <CommonBtn flat dense icon="edit" :disable="Boolean(link.revokedAt)" :tooltip="t('global.edit')"
                @click="onEditLink(link)" />
              <CommonBtn flat dense icon="link_off" color="negative" :disable="Boolean(link.revokedAt)"
                :tooltip="t('calcWorkspace.revokeLink')" @click="onRevoke(link)" />
            </div>
          </q-item-section>
        </q-item>
        <q-item v-if="links.length === 0">
          <q-item-section class="text-grey-6">{{ t('calcWorkspace.noShareLinks') }}</q-item-section>
        </q-item>
      </q-list>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Manage version shares, audiences, permissions, notes, and generated URLs. */
import { useDialogPluginComponent } from 'quasar'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import { ShareAccessType, type CalcReportVersion, type ShareLink } from 'src/api/calc/types'
import {
  createShareLink, listShareDepartmentOptions, listShareLinks, listShareUserOptions, revokeShareLink, updateShareLink,
  type ShareDepartmentOption, type ShareLinkInput, type ShareUserOption
} from 'src/api/calc/shares'
import { listVersions } from 'src/api/calc/versions'
import { notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'
import { useConfig } from 'src/config'

const props = defineProps<{ reportOid: string; reportName: string }>()
defineEmits([...useDialogPluginComponent.emits])
const { dialogRef, onDialogHide, onDialogCancel } = useDialogPluginComponent()
const versions = ref<CalcReportVersion[]>([])
const links = ref<ShareLink[]>([])
const versionName = ref<string | null>(null)
const accessType = ref<ShareAccessType>(ShareAccessType.Public)
const recipientUserOids = ref<string[]>([])
const recipientDepartmentOids = ref<string[]>([])
const userOptions = ref<Array<{ label: string; value: string }>>([])
const departmentOptions = ref<Array<{ label: string; value: string }>>([])
const canEdit = ref(false)
const canShare = ref(false)
const expiresAt = ref('')
const maxUseCount = ref<number | null>(null)
const note = ref('')
const editingShareOid = ref('')
const isSaving = ref(false)
const isSearchingUsers = ref(false)

const versionOptions = computed(() => versions.value.map((version) => ({ label: version.versionName, value: version.versionName })))
const accessOptions = computed(() => [
  { label: t('calcWorkspace.accessPublic'), value: ShareAccessType.Public },
  { label: t('calcWorkspace.accessInternal'), value: ShareAccessType.Internal },
  { label: t('calcWorkspace.accessSpecifiedUsers'), value: ShareAccessType.SpecifiedUsers },
  { label: t('calcWorkspace.accessSpecifiedDepartments'), value: ShareAccessType.SpecifiedDepartments }
])
const canSaveLink = computed(() => Boolean(versionName.value)
  && (accessType.value !== ShareAccessType.SpecifiedUsers || recipientUserOids.value.length > 0)
  && (accessType.value !== ShareAccessType.SpecifiedDepartments || recipientDepartmentOids.value.length > 0))

/** Load every published version and current share link. */
async function initializeDialog(): Promise<void> {
  const [versionResponse, linkResponse] = await Promise.all([listVersions(props.reportOid), listShareLinks(props.reportOid)])
  versions.value = versionResponse.data || []
  links.value = linkResponse.data || []
  versionName.value = versionOptions.value[0]?.value || null
}
onMounted(initializeDialog)

watch(accessType, async (value) => {
  if (value !== ShareAccessType.SpecifiedUsers) recipientUserOids.value = []
  if (value !== ShareAccessType.SpecifiedDepartments) recipientDepartmentOids.value = []
  if (value !== ShareAccessType.SpecifiedDepartments || departmentOptions.value.length) return
  const response = await listShareDepartmentOptions()
  departmentOptions.value = (response.data || []).map((department: ShareDepartmentOption) => ({ label: department.name, value: department.departmentOid }))
})

/** Load selectable user labels for filtering or edit-form echo. */
async function loadUserOptions(query: string): Promise<void> {
  const response = await listShareUserOptions(query)
  userOptions.value = (response.data || []).map((user: ShareUserOption) => ({ label: user.nickName || user.username, value: user.userOid }))
}

/** Search selectable users as Quasar filters recipient options. */
function onFilterUsers(query: string, done: (callback: () => void) => void): void {
  isSearchingUsers.value = true
  void loadUserOptions(query).then(() => done(() => { isSearchingUsers.value = false }))
    .catch(() => { isSearchingUsers.value = false })
}

/** Create or replace a share and update only the affected local row. */
async function onSaveLink(): Promise<void> {
  if (!versionName.value) return
  isSaving.value = true
  try {
    const input: ShareLinkInput = {
      versionName: versionName.value, accessType: accessType.value, recipientUserOids: recipientUserOids.value,
      recipientDepartmentOids: recipientDepartmentOids.value, canEdit: canEdit.value, canShare: canShare.value,
      expiresAt: expiresAt.value ? new Date(expiresAt.value).toISOString() : null,
      maxUseCount: maxUseCount.value, note: note.value.trim() || null
    }
    if (editingShareOid.value) {
      const response = await updateShareLink(editingShareOid.value, input)
      const index = links.value.findIndex((link) => link.shareOid === editingShareOid.value)
      if (index >= 0) links.value[index] = { ...links.value[index], ...response.data }
      resetForm()
      notifySuccess(t('calcWorkspace.shareUpdated'))
      return
    }
    const response = await createShareLink(props.reportOid, input)
    if (response.data.token) {
      response.data.shareUrl = buildFrontendShareUrl(response.data.token)
      await navigator.clipboard.writeText(response.data.shareUrl)
      notifySuccess(t('calcWorkspace.linkCopied'))
    }
    links.value.unshift(response.data)
    resetForm()
  } finally {
    isSaving.value = false
  }
}

/** Build the browser-facing URL for a newly returned one-time token. */
function buildFrontendShareUrl(token: string): string {
  const config = useConfig()
  const backendUrl = new URL(`${config.baseUrl}${config.api}/calc-report/shared/${token}/preview`, window.location.origin).toString()
  const source = btoa(backendUrl).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '')
  const frontendUrl = new URL('/calc-report/shared/import', window.location.origin)
  frontendUrl.searchParams.set('linkType', 'frontend')
  frontendUrl.searchParams.set('source', source)
  return frontendUrl.toString()
}

/** Populate the form from an existing active share link. */
async function onEditLink(link: ShareLink): Promise<void> {
  editingShareOid.value = link.shareOid
  versionName.value = link.versionName
  accessType.value = link.accessType
  recipientUserOids.value = [...link.recipientUserOids]
  recipientDepartmentOids.value = [...link.recipientDepartmentOids]
  canEdit.value = link.canEdit
  canShare.value = link.canShare
  expiresAt.value = link.expiresAt ? link.expiresAt.slice(0, 16) : ''
  maxUseCount.value = link.maxUseCount
  note.value = link.note || ''
  if (link.accessType === ShareAccessType.SpecifiedUsers) await loadUserOptions('')
}

/** Reset share settings to defaults for creating another link. */
function resetForm(): void {
  editingShareOid.value = ''
  versionName.value = versionOptions.value[0]?.value || null
  accessType.value = ShareAccessType.Public
  recipientUserOids.value = []
  recipientDepartmentOids.value = []
  canEdit.value = false
  canShare.value = false
  expiresAt.value = ''
  maxUseCount.value = null
  note.value = ''
}

/** Copy a generated share URL without rotating its bearer token. */
async function onCopyLink(shareUrl: string): Promise<void> {
  await navigator.clipboard.writeText(shareUrl)
  notifySuccess(t('calcWorkspace.linkCopied'))
}

/** Revoke one link and update only its local row. */
async function onRevoke(link: ShareLink): Promise<void> {
  Object.assign(link, (await revokeShareLink(link.shareOid)).data)
}

/** Return the localized audience label. */
function accessLabel(value: ShareAccessType): string {
  return accessOptions.value.find((option) => option.value === value)?.label || value
}

/** Summarize inherited import permissions for one link row. */
function permissionLabel(link: ShareLink): string {
  return [link.canEdit ? t('calcWorkspace.canEdit') : '', link.canShare ? t('calcWorkspace.canShare') : ''].filter(Boolean).join(' · ') || t('calcWorkspace.runOnly')
}
</script>

<style scoped>
.share-dialog { width: min(760px, 94vw); max-width: 760px; }
.share-dialog__list { max-height: 260px; overflow: auto; }
.share-form__grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12px; }
.share-form__wide { grid-column: 1 / -1; min-width: 0; }
.permission-band { min-height: 42px; background: #f5f7f6; border-radius: 6px; }
@media (max-width: 600px) {
  .share-form__grid { grid-template-columns: minmax(0, 1fr); }
  .share-form__wide { grid-column: 1; }
}
</style>
