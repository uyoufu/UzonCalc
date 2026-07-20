<template>
  <UserAvatar>
    <HoverableTip class="shadow-1 bg-white text-grey-8" anchor="bottom right" self="top right" :offset="[0, 8]">
      <q-list class="user-info-menu" separator dense>
        <q-item clickable @click="onOpenAbout" class="active-item">
          <q-item-section avatar>
            <q-icon name="info_outline" />
          </q-item-section>
          <q-item-section>{{ t('userMenu.about') }}</q-item-section>
        </q-item>
        <q-item clickable @click="onGoToProfile" class="active-item">
          <q-item-section avatar>
            <q-icon name="account_circle" />
          </q-item-section>
          <q-item-section>{{ t('userMenu.profile') }}</q-item-section>
        </q-item>
        <q-item v-if="!isDesktopApi" clickable class="text-negative active-item" @click="onLogout">
          <q-item-section avatar>
            <q-icon name="exit_to_app" />
          </q-item-section>
          <q-item-section>{{ t('userMenu.logout') }}</q-item-section>
        </q-item>
      </q-list>
    </HoverableTip>
  </UserAvatar>
</template>

<script lang="ts" setup>
/** Localized user menu with profile, about, and deployment-aware logout. */
import UserAvatar from 'src/components/userAvatar/UserAvatar.vue'
import HoverableTip from 'src/components/hoverableTip/HoverableTip.vue'
import AboutDialog from './AboutDialog.vue'
import { useUserInfoStore } from 'src/stores/user'
import { usePermission } from 'src/compositions/permission'
import { showComponentDialog } from 'src/components/lowCode/PopupDialog'
import { t } from 'src/i18n/helpers'

const userInfoStore = useUserInfoStore()
const router = useRouter()
const { isDesktopApi } = usePermission()

/** End the web session. */
async function onLogout(): Promise<void> {
  await userInfoStore.logout()
}

/** Navigate to current-user profile settings. */
async function onGoToProfile(): Promise<void> {
  await router.push('/user/profile')
}

/** Open product and version information. */
async function onOpenAbout(): Promise<void> {
  await showComponentDialog(AboutDialog, {})
}
</script>

<style lang="scss" scoped>
.user-info-menu {
  overflow: hidden;
  font-size: 14px;

  .active-item {
    &:hover {
      // 放大
      scale: 1.1;
      transition: all 0.3s;
    }
  }
}
</style>
