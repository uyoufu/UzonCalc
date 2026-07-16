<template>
  <q-dialog v-model="isOpen" persistent>
    <q-card class="share-dialog">
      <q-card-section class="row items-center">
        <div class="text-subtitle1">{{ t('calcWorkspace.shareReport') }} · {{ reportName }}</div>
        <q-space /><q-btn flat round dense icon="close" @click="isOpen = false" />
      </q-card-section>
      <q-separator />
      <q-card-section class="q-gutter-md">
        <div class="row q-col-gutter-sm">
          <q-select v-model="versionName" class="col" dense outlined emit-value map-options
            :label="t('calcWorkspace.version')" :options="approvedVersionOptions" />
          <q-select v-model="accessType" class="col" dense outlined emit-value map-options
            :label="t('calcWorkspace.accessType')" :options="accessOptions" />
        </div>
        <q-select v-if="accessType === 'specified_users'" v-model="recipients" use-input use-chips multiple dense outlined
          :label="t('calcWorkspace.recipientUsernames')" :options="[]" @new-value="onRecipientAdded" />
        <div class="row q-col-gutter-sm">
          <q-input v-model="expiresAt" class="col" dense outlined type="datetime-local" :label="t('calcWorkspace.expiresAt')" />
          <q-input v-model.number="maxUseCount" class="col" dense outlined type="number" min="1" :label="t('calcWorkspace.maxUseCount')" />
        </div>
        <div class="row justify-end">
          <CommonBtn icon="add_link" :label="t('calcWorkspace.createLink')" :loading="isCreating"
            :disable="!versionName" @click="onCreateLink" />
        </div>
      </q-card-section>
      <q-separator />
      <q-list separator class="share-dialog__list">
        <q-item v-for="link in links" :key="link.shareOid">
          <q-item-section>
            <q-item-label>{{ link.versionName }} · {{ accessLabel(link.accessType) }}</q-item-label>
            <q-item-label caption>{{ link.useCount }} / {{ link.maxUseCount ?? '∞' }} · {{ link.revokedAt ? t('calcWorkspace.revoked') : t('calcWorkspace.active') }}</q-item-label>
          </q-item-section>
          <q-item-section side><q-btn flat round dense icon="link_off" color="negative" :disable="Boolean(link.revokedAt)" @click="onRevoke(link)" /></q-item-section>
        </q-item>
        <q-item v-if="links.length === 0"><q-item-section class="text-grey-6">{{ t('calcWorkspace.noShareLinks') }}</q-item-section></q-item>
      </q-list>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Manage approved-version share links for a report. */
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import type { CalcReportVersion, ShareAccessType, ShareLink } from 'src/api/calc/types'
import { createShareLink, listShareLinks, revokeShareLink } from 'src/api/calc/shares'
import { listVersions } from 'src/api/calc/versions'
import { getUserInfo } from 'src/api/user'
import { notifyError, notifySuccess } from 'src/utils/dialog'
import { t } from 'src/i18n/helpers'

const props = defineProps<{ modelValue: boolean; reportOid: string; reportName: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()
const isOpen = computed({ get: () => props.modelValue, set: (value) => emit('update:modelValue', value) })
const versions = ref<CalcReportVersion[]>([])
const links = ref<ShareLink[]>([])
const versionName = ref<string | null>(null)
const accessType = ref<ShareAccessType>('link')
const recipients = ref<Array<{ label: string; value: string }>>([])
const expiresAt = ref('')
const maxUseCount = ref<number | null>(null)
const isCreating = ref(false)

const approvedVersionOptions = computed(() => versions.value.filter((version) => version.reviewStatus === 'approved').map((version) => ({ label: version.versionName, value: version.versionName })))
const accessOptions = computed(() => [
  { label: t('calcWorkspace.accessLink'), value: 'link' },
  { label: t('calcWorkspace.accessPublic'), value: 'public' },
  { label: t('calcWorkspace.accessSpecified'), value: 'specified_users' }
])

watch(() => [props.modelValue, props.reportOid] as const, async ([open, reportOid]) => {
  if (!open || !reportOid) return
  const [versionResponse, linkResponse] = await Promise.all([listVersions(reportOid), listShareLinks(reportOid)])
  versions.value = versionResponse.data || []
  links.value = linkResponse.data || []
  versionName.value = approvedVersionOptions.value[0]?.value || null
}, { immediate: true })

/** Resolve an exact username into the recipient OID stored by the backend. */
async function onRecipientAdded(username: string, done: (value?: unknown, mode?: 'add' | 'add-unique' | 'toggle') => void): Promise<void> {
  try {
    const response = await getUserInfo(username.trim())
    done({ label: username.trim(), value: response.data.oid }, 'add-unique')
  } catch {
    notifyError(t('calcWorkspace.userNotFound'))
    done()
  }
}

/** Create a link and copy the one-time token URL. */
async function onCreateLink(): Promise<void> {
  if (!versionName.value) return
  isCreating.value = true
  try {
    const response = await createShareLink(props.reportOid, {
      versionName: versionName.value,
      accessType: accessType.value,
      recipientUserOids: recipients.value.map((recipient) => recipient.value),
      expiresAt: expiresAt.value ? new Date(expiresAt.value).toISOString() : null,
      maxUseCount: maxUseCount.value
    })
    links.value.unshift(response.data)
    if (response.data.token) {
      const url = new URL(`/calc-report/shared/${response.data.token}/import`, window.location.origin).toString()
      await navigator.clipboard.writeText(url)
      notifySuccess(t('calcWorkspace.linkCopied'))
    }
  } finally {
    isCreating.value = false
  }
}

/** Revoke a link and update the local row only. */
async function onRevoke(link: ShareLink): Promise<void> {
  const response = await revokeShareLink(link.shareOid)
  Object.assign(link, response.data)
}

/** Return the translated label for one access mode. */
function accessLabel(value: ShareAccessType): string {
  return accessOptions.value.find((option) => option.value === value)?.label || value
}
</script>

<style scoped>
.share-dialog { width: min(760px, 92vw); max-width: 760px; }
.share-dialog__list { max-height: 280px; overflow: auto; }
</style>
