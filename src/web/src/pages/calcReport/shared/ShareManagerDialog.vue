<template>
  <q-dialog ref="dialogRef" persistent @hide="onDialogHide">
    <q-card class="column no-wrap" style="width: min(980px, 96vw); max-width: 980px; height: min(760px, 92vh)">
      <q-card-section class="row items-center no-wrap q-px-md q-py-sm">
        <div class="col text-subtitle1 ellipsis">{{ t('calcWorkspace.shareReport') }} · {{ reportName }}</div>
        <CommonBtn flat dense icon="close" :tooltip="t('global.close')" @click="onDialogCancel" />
      </q-card-section>
      <q-separator />

      <div v-if="isInitializing" class="col flex flex-center">
        <q-spinner size="36px" color="primary" />
      </div>
      <div v-else class="col no-wrap overflow-hidden" :class="$q.screen.lt.md ? 'column' : 'row'">
        <section class="column no-wrap"
          :style="$q.screen.lt.md ? 'min-height: 52%;' : 'width: 390px; min-width: 390px;'">
          <q-scroll-area class="col">
            <div class="column q-pa-md">
              <div class="row q-col-gutter-sm">
                <q-select v-model="versionName" class="col-12 col-sm-6" dense options-dense outlined emit-value
                  map-options :label="t('calcWorkspace.version')" :options="versionOptions" />

                <q-select v-model="accessType" class="col-12 col-sm-6" dense options-dense outlined emit-value
                  map-options :label="t('calcWorkspace.accessType')" :options="accessOptions" />
              </div>

              <q-select class="q-mt-md" v-if="accessType === ShareAccessType.SpecifiedUsers" v-model="recipientUserOids"
                use-input use-chips multiple dense options-dense outlined emit-value map-options
                :loading="isSearchingUsers" :label="t('calcWorkspace.recipientUsers')" :options="userOptions"
                @filter="onFilterUsers" />

              <q-select class="q-mt-md" v-if="accessType === ShareAccessType.SpecifiedDepartments"
                v-model="recipientDepartmentOids" use-chips multiple dense options-dense outlined emit-value map-options
                :label="t('calcWorkspace.recipientDepartments')" :options="departmentOptions" />

              <div class="row items-center q-mt-md">
                <q-toggle dense v-model="canEdit" :label="t('calcWorkspace.canEdit')" />
                <q-toggle dense v-model="canShare" :label="t('calcWorkspace.canShare')" />
              </div>

              <div class="row q-col-gutter-sm q-mt-md">
                <q-input v-model="expiresAt" class="col-12 col-sm-6" dense outlined type="datetime-local"
                  :label="t('calcWorkspace.expiresAt')" />
                <q-input v-model.number="maxUseCount" class="col-12 col-sm-6" dense outlined type="number" min="1"
                  :label="t('calcWorkspace.maxUseCount')" />
              </div>

              <q-input class="q-mt-md" v-model="note" dense outlined type="textarea" autogrow maxlength="500"
                :label="t('calcWorkspace.shareNote')" />
            </div>
          </q-scroll-area>

          <q-separator />
          <div class="row justify-end q-gutter-sm q-pa-sm">
            <CancelBtn v-if="editingShareOid" flat icon="close" :label="t('global.cancel')" @click="resetForm" />
            <OkBtn :icon="editingShareOid ? 'save' : 'add_link'"
              :label="t(editingShareOid ? 'global.save' : 'calcWorkspace.createLink')" :loading="isSaving"
              :disable="!canSaveLink" @click="onSaveLink" />
          </div>
        </section>

        <q-separator :vertical="$q.screen.gt.sm" />

        <section class="col column no-wrap overflow-hidden">
          <div class="row items-center q-px-md q-py-sm">
            <div class="text-subtitle2">{{ t('calcWorkspace.shareLinks') }}</div>
            <q-space />
            <q-badge color="grey-7" :label="links.length" />
          </div>
          <q-separator />
          <q-scroll-area class="col">
            <q-list separator>
              <q-item v-for="link in links" :key="link.shareOid" :class="{ 'text-grey-6': Boolean(link.revokedAt) }">
                <q-item-section>
                  <q-item-label class="row items-center q-gutter-xs">
                    <span>{{ link.versionName }}</span>
                    <q-badge outline color="primary" :label="accessLabel(link.accessType)" />
                  </q-item-label>
                  <q-item-label caption>{{ permissionLabel(link) }}</q-item-label>
                  <q-item-label caption>{{ link.useCount }} / {{ link.maxUseCount ?? '∞' }}</q-item-label>
                  <q-item-label v-if="link.note" caption lines="2">{{ link.note }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <div class="row no-wrap q-gutter-xs">
                    <CommonBtn size="sm" flat dense icon="content_copy" :tooltip="t('calcWorkspace.copyLink')"
                      @click="onCopyLink(link.token)" />
                    <CommonBtn size="sm" flat dense icon="edit" :disable="Boolean(link.revokedAt)"
                      :tooltip="t('global.edit')" @click="onEditLink(link)" />
                    <CommonBtn size="sm" flat dense icon="link_off" color="negative" :disable="Boolean(link.revokedAt)"
                      :tooltip="t('calcWorkspace.revokeLink')" @click="onRevoke(link)" />
                  </div>
                </q-item-section>
              </q-item>
              <q-item v-if="links.length === 0">
                <q-item-section class="text-grey-6 text-center q-py-xl">{{ t('calcWorkspace.noShareLinks')
                }}</q-item-section>
              </q-item>
            </q-list>
          </q-scroll-area>
        </section>
      </div>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Manage stable version-share links and their audience settings. */
import { useDialogPluginComponent } from 'quasar'
import { ShareAccessType, type CalcReportVersion, type ShareLink } from 'src/api/calc/types'
import {
  buildFrontendShareUrl,
  createShareLink,
  listShareDepartmentOptions,
  listShareLinks,
  listShareUserOptions,
  revokeShareLink,
  updateShareLink,
  type ShareDepartmentOption,
  type ShareLinkInput,
  type ShareUserOption
} from 'src/api/calc/shares'
import { listVersions } from 'src/api/calc/versions'
import { notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'

const props = defineProps<{ reportOid: string; reportName: string }>()
defineEmits([...useDialogPluginComponent.emits])
const { dialogRef, onDialogHide, onDialogCancel } = useDialogPluginComponent()
const $q = useQuasar()
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
const isInitializing = ref(true)
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

/** Load published versions and every owner-managed share link. */
async function initializeDialog(): Promise<void> {
  try {
    const [versionResponse, linkResponse] = await Promise.all([listVersions(props.reportOid), listShareLinks(props.reportOid)])
    versions.value = versionResponse.data || []
    links.value = linkResponse.data || []
    versionName.value = versionOptions.value[0]?.value || null
  } finally {
    isInitializing.value = false
  }
}
onMounted(initializeDialog)

watch(accessType, async (value) => {
  if (value !== ShareAccessType.SpecifiedUsers) recipientUserOids.value = []
  if (value !== ShareAccessType.SpecifiedDepartments) recipientDepartmentOids.value = []
  if (value !== ShareAccessType.SpecifiedDepartments || departmentOptions.value.length) return
  const response = await listShareDepartmentOptions()
  departmentOptions.value = (response.data || []).map((department: ShareDepartmentOption) => ({
    label: department.name,
    value: department.departmentOid
  }))
})

/** Load selectable user labels for filtering or edit-form echo. */
async function loadUserOptions(query: string): Promise<void> {
  const response = await listShareUserOptions(query)
  userOptions.value = (response.data || []).map((user: ShareUserOption) => ({
    label: user.nickName || user.username,
    value: user.userOid
  }))
}

/** Search selectable users as Quasar filters recipient options. */
function onFilterUsers(query: string, done: (callback: () => void) => void): void {
  isSearchingUsers.value = true
  void loadUserOptions(query)
    .then(() => done(() => { isSearchingUsers.value = false }))
    .catch(() => done(() => { isSearchingUsers.value = false }))
}

/** Create or replace one share and update only its local row. */
async function onSaveLink(): Promise<void> {
  if (!versionName.value) return
  isSaving.value = true
  try {
    const input: ShareLinkInput = {
      versionName: versionName.value,
      accessType: accessType.value,
      recipientUserOids: recipientUserOids.value,
      recipientDepartmentOids: recipientDepartmentOids.value,
      canEdit: canEdit.value,
      canShare: canShare.value,
      expiresAt: expiresAt.value ? new Date(expiresAt.value).toISOString() : null,
      maxUseCount: maxUseCount.value,
      note: note.value.trim() || null
    }
    if (editingShareOid.value) {
      const response = await updateShareLink(editingShareOid.value, input)
      const index = links.value.findIndex((link) => link.shareOid === editingShareOid.value)
      if (index >= 0) links.value[index] = response.data
      resetForm()
      notifySuccess(t('calcWorkspace.shareUpdated'))
      return
    }
    const response = await createShareLink(props.reportOid, input)
    links.value.unshift(response.data)
    await onCopyLink(response.data.token)
    resetForm()
  } finally {
    isSaving.value = false
  }
}

/** Populate the form from one existing active share link. */
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

/** Copy one stable browser-facing share URL. */
async function onCopyLink(token: string): Promise<void> {
  await navigator.clipboard.writeText(buildFrontendShareUrl(token))
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
  return [link.canEdit ? t('calcWorkspace.canEdit') : '', link.canShare ? t('calcWorkspace.canShare') : '']
    .filter(Boolean)
    .join(' · ') || t('calcWorkspace.runOnly')
}
</script>
