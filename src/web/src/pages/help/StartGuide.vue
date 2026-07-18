<template>
  <iframe class="uzoncalc-help" :src="helpUrl" :title="t('routes.startGuide')" @error="onHelpLoadError" />
</template>

<script lang="ts" setup>
/** Load localized bundled help with a deterministic Chinese fallback. */
import { useUserInfoStore } from 'src/stores/user'
import { t } from 'src/i18n/helpers'

defineOptions({ name: 'StartGuide' })
const userStore = useUserInfoStore()
const supportedLocales = new Set(['zh-CN', 'en-US'])
const selectedLocale = ref(supportedLocales.has(userStore.locale) ? userStore.locale : 'zh-CN')
const helpUrl = computed(() => `/helps/help.${selectedLocale.value}.html`)
watch(() => userStore.locale, (locale) => { selectedLocale.value = supportedLocales.has(locale) ? locale : 'zh-CN' })

/** Fall back to the bundled Chinese document when localized loading fails. */
function onHelpLoadError(): void {
  selectedLocale.value = 'zh-CN'
}
</script>

<style scoped>
.uzoncalc-help { width: 100%; height: 100%; min-height: 620px; border: 0; }
</style>
