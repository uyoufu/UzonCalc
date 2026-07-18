<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide" persistent>
    <q-card class="share-dialog">
      <q-card-section class="row items-center q-py-sm">
        <div class="text-subtitle1">{{ t('calcWorkspace.shareReport') }} · {{ reportName }}</div>
        <q-space />
        <CommonBtn flat dense icon="close" :tooltip="t('global.close')" @click="onDialogCancel" />
      </q-card-section>
      <q-separator />
      <q-card-section class="q-gutter-md">
        <div class="row q-col-gutter-sm">
          <q-select v-model="versionName" class="col-12 col-sm-6" dense options-dense outlined emit-value map-options
            :label="t('calcWorkspace.version')" :options="versionOptions" />
          <q-select v-model="accessType" class="col-12 col-sm-6" dense options-dense outlined emit-value map-options
            :label="t('calcWorkspace.accessType')" :options="accessOptions" />
        </div>
        <q-select v-if="accessType === ShareAccessType.SpecifiedUsers" v-model="recipientUserOids" use-input use-chips
          multiple dense options-dense outlined emit-value map-options :loading="isSearchingUsers"
          :label="t('calcWorkspace.recipientUsers')" :options="userOptions" @filter="onFilterUsers" />
        <q-select v-if="accessType === ShareAccessType.SpecifiedDepartments" v-model="recipientDepartmentOids" use-chips
          multiple dense options-dense outlined emit-value map-options :label="t('calcWorkspace.recipientDepartments')"
          :options="departmentOptions" />
        <div class="permission-band row items-center q-gutter-lg q-px-sm q-py-xs">
          <q-toggle v-model="canEdit" :label="t('calcWorkspace.canEdit')" />
          <q-toggle v-model="canShare" :label="t('calcWorkspace.canShare')" />
        </div>
        <div class="row q-col-gutter-sm">
          <q-input v-model="expiresAt" class="col-12 col-sm-6" dense outlined type="datetime-local"
            :label="t('calcWorkspace.expiresAt')" />
          <q-input v-model.number="maxUseCount" class="col-12 col-sm-6" dense outlined type="number" min="1"
            :label="t('calcWorkspace.maxUseCount')" />
        </div>
        <div class="row justify-end">
          <CommonBtn icon="add_link" :label="t('calcWorkspace.createLink')" :loading="isCreating"
            :disable="!canCreateLink" @click="onCreateLink" />
        </div>
      </q-card-section>
      <q-separator />
      <q-list separator class="share-dialog__list">
        <q-item v-for="link in links" :key="link.shareOid">
          <q-item-section>
            <q-item-label>{{ link.versionName }} · {{ accessLabel(link.accessType) }}</q-item-label>
            <q-item-label caption>{{ permissionLabel(link) }} · {{ link.useCount }} / {{ link.maxUseCount ?? '∞' }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <CommonBtn flat dense icon="link_off" color="negative" :disable="Boolean(link.revokedAt)"
              :tooltip="t('calcWorkspace.revokeLink')" @click="onRevoke(link)" />
          </q-item-section>
        </q-item>
        <q-item v-if="links.length === 0"><q-item-section class="text-grey-6">{{ t('calcWorkspace.noShareLinks') }}</q-item-section></q-item>
      </q-list>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Manage version shares, audiences, and inherited import permissions. */
import { useDialogPluginComponent } from 'quasar'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import { ShareAccessType, type CalcReportVersion, type ShareLink } from 'src/api/calc/types'
import { createShareLink, listShareDepartmentOptions, listShareLinks, listShareUserOptions, revokeShareLink, type ShareDepartmentOption, type ShareUserOption } from 'src/api/calc/shares'
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
const isCreating = ref(false)
const isSearchingUsers = ref(false)

const versionOptions = computed(() => versions.value.map((version) => ({ label: version.versionName, value: version.versionName })))
const accessOptions = computed(() => [
  { label: t('calcWorkspace.accessPublic'), value: ShareAccessType.Public },
  { label: t('calcWorkspace.accessInternal'), value: ShareAccessType.Internal },
  { label: t('calcWorkspace.accessSpecifiedUsers'), value: ShareAccessType.SpecifiedUsers },
  { label: t('calcWorkspace.accessSpecifiedDepartments'), value: ShareAccessType.SpecifiedDepartments }
])
const canCreateLink = computed(() => Boolean(versionName.value) &&
  (accessType.value !== ShareAccessType.SpecifiedUsers || recipientUserOids.value.length > 0) &&
  (accessType.value !== ShareAccessType.SpecifiedDepartments || recipientDepartmentOids.value.length > 0))

/** Load every published version and current share link. */
async function initializeDialog(): Promise<void> {
  const [versionResponse, linkResponse] = await Promise.all([listVersions(props.reportOid), listShareLinks(props.reportOid)])
  versions.value = versionResponse.data || []
  links.value = linkResponse.data || []
  versionName.value = versionOptions.value[0]?.value || null
}
onMounted(initializeDialog)

watch(accessType, async (value) => {
  if (value !== ShareAccessType.SpecifiedDepartments || departmentOptions.value.length) return
  const response = await listShareDepartmentOptions()
  departmentOptions.value = (response.data || []).map((department: ShareDepartmentOption) => ({ label: department.name, value: department.departmentOid }))
})

/** Search selectable users as Quasar filters recipient options. */
function onFilterUsers(query: string, done: (callback: () => void) => void): void {
  isSearchingUsers.value = true
  void listShareUserOptions(query).then((response) => {
    done(() => {
      userOptions.value = (response.data || []).map((user: ShareUserOption) => ({ label: user.nickName || user.username, value: user.userOid }))
      isSearchingUsers.value = false
    })
  }).catch(() => { isSearchingUsers.value = false })
}

/** Create a share and copy its frontend URL containing the backend URL. */
async function onCreateLink(): Promise<void> {
  if (!versionName.value) return
  isCreating.value = true
  try {
    const response = await createShareLink(props.reportOid, {
      versionName: versionName.value,
      accessType: accessType.value,
      recipientUserOids: recipientUserOids.value,
      recipientDepartmentOids: recipientDepartmentOids.value,
      canEdit: canEdit.value,
      canShare: canShare.value,
      expiresAt: expiresAt.value ? new Date(expiresAt.value).toISOString() : null,
      maxUseCount: maxUseCount.value
    })
    links.value.unshift(response.data)
    if (response.data.token) {
      const config = useConfig()
      const backendUrl = new URL(`${config.baseUrl}${config.api}/calc-report/shared/${response.data.token}/preview`, window.location.origin).toString()
      const source = btoa(backendUrl).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '')
      const frontendUrl = new URL('/calc-report/shared/import', window.location.origin)
      frontendUrl.searchParams.set('linkType', 'frontend')
      frontendUrl.searchParams.set('source', source)
      await navigator.clipboard.writeText(frontendUrl.toString())
      notifySuccess(t('calcWorkspace.linkCopied'))
    }
  } finally {
    isCreating.value = false
  }
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
.permission-band { min-height: 42px; background: #f5f7f6; border-radius: 6px; }
</style>
