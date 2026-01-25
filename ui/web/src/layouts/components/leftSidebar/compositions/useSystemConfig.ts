import logger from 'loglevel'
import type { ISystemConfig } from 'src/api/system'
import { translateGlobal } from "src/i18n/helpers"
import { useI18n } from "vue-i18n"

// TODO: 后续改成后端返回名称
export function useSystemConfig () {
  const systemConfig: Ref<ISystemConfig> = ref({
    name: translateGlobal('appName'),
    loginWelcome: 'Welcome to UzonCalc',
    icon: '',
    copyright: '© 2023 UzonCalc',
    icpInfo: '粤ICP备2023000000号',
  })

  onMounted(async () => {
  })

  const { locale } = useI18n()
  watch(locale, () => {
    logger.debug('[useSystemConfig] Locale changed, update app name')
    systemConfig.value.name = translateGlobal('appName')
  })

  return { systemConfig }
}
