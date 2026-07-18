<template>
  <div class="profile-page column no-wrap">
    <q-tabs v-model="activeTab" dense align="left" active-color="primary" indicator-color="primary">
      <q-tab name="basic" icon="person" :label="t('userPage.basicInfo')" />
      <q-tab name="security" icon="lock" :label="t('userPage.securitySettings')" />
    </q-tabs>
    <q-separator />
    <q-tab-panels v-model="activeTab" animated class="col">
      <q-tab-panel name="basic" class="profile-panel">
        <div class="row items-center q-gutter-lg">
          <button type="button" class="avatar-button" :aria-label="t('userPage.changeAvatar')"
            @click="onChangeUserAvatar">
            <UserAvatar size="88px" />
            <q-icon name="photo_camera" class="avatar-button__icon" />
          </button>
          <div>
            <div class="text-subtitle1 text-weight-medium">{{ profile?.username }}</div>
            <div class="text-caption text-grey-7">{{ roleLabel }}</div>
          </div>
        </div>
        <q-input v-model="nickName" dense outlined class="profile-field q-mt-xl" :label="t('userPage.nickName')"
          maxlength="50" counter />
        <div class="text-caption text-grey-7 q-mt-sm">{{ t('userPage.registeredAt') }} · {{ createdAt }}</div>
        <div class="row q-mt-lg">
          <CommonBtn icon="save" :label="t('global.save')" :loading="isSavingProfile" :disable="!nickName.trim()"
            @click="onSaveProfile" />
        </div>
      </q-tab-panel>
      <q-tab-panel name="security" class="profile-panel">
        <div class="text-subtitle1 text-weight-medium">{{ t('userPage.changePassword') }}</div>
        <div class="text-body2 text-grey-7 q-mt-xs">{{ t('userPage.passwordSecurity') }}</div>
        <CommonBtn class="q-mt-lg" icon="password" :label="t('userPage.changePassword')"
          @click="onChangeUserPassword" />
      </q-tab-panel>
    </q-tab-panels>
  </div>
</template>

<script setup lang="ts">
/** Current-user profile with basic information and security settings. */
import dayjs from 'dayjs'
import UserAvatar from 'src/components/userAvatar/UserAvatar.vue'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import ImageCropper from 'src/components/imageCropper/ImageCropper.vue'
import { changeUserPassword, getCurrentUserProfile, updateCurrentUserProfile, updateUserAvatar, type IUserInfoDetail } from 'src/api/user'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import { notifySuccess } from 'src/utils/dialog'
import { showComponentDialog, showDialog } from 'src/components/lowCode/PopupDialog'
import { openFileSelector } from 'src/utils/file'
import { useUserInfoStore } from 'src/stores/user'
import { t } from 'src/i18n/helpers'

defineOptions({ name: 'profileIndex' })
const userStore = useUserInfoStore()
const activeTab = ref('basic')
const profile = ref<IUserInfoDetail | null>(null)
const nickName = ref('')
const isSavingProfile = ref(false)
const createdAt = computed(() => profile.value ? dayjs(profile.value.createdAt).format('YYYY-MM-DD') : '')
const roleLabel = computed(() => profile.value?.roles.includes('admin') ? t('userPage.administrator') : t('userPage.regularUser'))

/** Load the authenticated user's safe profile. */
async function initializeProfile(): Promise<void> {
  profile.value = (await getCurrentUserProfile()).data
  nickName.value = profile.value.nickName || profile.value.username
}
onMounted(initializeProfile)

/** Persist the edited nickname and update session display state. */
async function onSaveProfile(): Promise<void> {
  isSavingProfile.value = true
  try {
    profile.value = (await updateCurrentUserProfile(nickName.value.trim())).data
    userStore.updateNickName(profile.value.nickName || profile.value.username)
    notifySuccess(t('userPage.profileSaved'))
  } finally {
    isSavingProfile.value = false
  }
}

/** Select, crop, normalize, and upload a new avatar. */
async function onChangeUserAvatar(): Promise<void> {
  const buffer = await openFileSelector(false, 'image/png,image/jpeg,image/webp')
  if (!buffer) return
  const cropResult = await showComponentDialog(ImageCropper, { img: new Blob([buffer as ArrayBuffer]) })
  if (!cropResult.ok) return
  const avatarUrl = (await updateUserAvatar(cropResult.data as Blob)).data
  userStore.updateUserAvatar(avatarUrl)
  if (profile.value) profile.value.avatar = avatarUrl
}

/** Verify the current password and submit a replacement. */
async function onChangeUserPassword(): Promise<void> {
  const result = await showDialog<{ oldPassword: string; newPassword: string }>({
    title: t('userPage.changePassword'),
    oneColumn: true,
    fields: [
      { name: 'oldPassword', label: t('userPage.oldPassword'), type: LowCodeFieldType.password, required: true },
      { name: 'newPassword', label: t('userPage.newPassword'), type: LowCodeFieldType.password, required: true }
    ],
    onOkMain: async (value) => (await changeUserPassword(value.oldPassword, value.newPassword)).data
  })
  if (result.ok) notifySuccess(t('userPage.passwordChanged'))
}
</script>

<style scoped>
.profile-page {
  height: 100%;
  min-height: 580px;
  background: #fff;
}

.profile-panel {
  max-width: 680px;
  padding: 32px;
}

.profile-field {
  max-width: 250px;
}

.avatar-button {
  position: relative;
  border: 0;
  padding: 0;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
}

.avatar-button__icon {
  position: absolute;
  right: -2px;
  bottom: 2px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: white;
  background: var(--q-primary);
}
</style>
