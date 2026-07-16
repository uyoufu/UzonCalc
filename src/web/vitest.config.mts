/** Vitest configuration for Vue, Quasar, aliases, and existing test layout. */
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  test: {
    environment: 'happy-dom',
    setupFiles: 'test/vitest/setup-file.ts',
    include: [
      'src/**/*.vitest.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      'test/vitest/__tests__/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'
    ]
  },
  plugins: [
    vue({ template: { transformAssetUrls } }),
    quasar({ sassVariables: 'src/css/quasar.variables.scss' }),
    tsconfigPaths()
  ]
})
