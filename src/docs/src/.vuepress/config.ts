import { defineUserConfig } from 'vuepress'
import { removeHtmlExtensionPlugin } from 'vuepress-plugin-remove-html-extension'

import theme from './theme.js'

export default defineUserConfig({
  base: '/',

  locales: {
    '/en/': {
      lang: 'en-US',
      title: 'UzonCalc',
      description: 'A AI-driven handwritten calculator'
    },
    '/': {
      lang: 'zh-CN',
      title: '宇正计算',
      description: '以 AI 为驱动的手写计算书软件'
    }
  },

  theme,

  plugins: [removeHtmlExtensionPlugin()]
  // Enable it with pwa
  // shouldPrefetch: false,
})
