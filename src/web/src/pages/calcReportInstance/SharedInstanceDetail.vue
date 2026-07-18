<template>
  <div class="shared-instance column no-wrap">
    <header class="shared-instance__header q-px-md row items-center">
      <div>
        <div class="text-subtitle1">{{ instance?.name }}</div>
        <div class="text-caption text-grey-7">{{ instance?.reportName }}</div>
      </div>
    </header>
    <q-separator />
    <div class="row no-wrap col shared-instance__body">
      <q-scroll-area v-if="instance?.inputWindows.length" class="shared-instance__inputs">
        <div class="q-pa-sm q-gutter-md">
          <section v-for="windowInfo in instance.inputWindows" :key="windowInfo.title">
            <div class="text-subtitle2 q-mb-xs">{{ windowInfo.title }}</div>
            <LowCodeForm :fields="windowInfo.fields" sync-value one-column :disable="true" :disable-default-btns="['ok', 'cancel']" />
          </section>
        </div>
      </q-scroll-area>
      <q-separator v-if="instance?.inputWindows.length" vertical />
      <iframe v-if="resultUrl" class="col" :src="resultUrl" :title="t('calcWorkspace.sharedInstance')" />
    </div>
  </div>
</template>

<script setup lang="ts">
/** Anonymous read-only view of one explicitly shared saved instance. */
import LowCodeForm from 'src/components/lowCode/LowCodeForm.vue'
import type { CalcInstance } from 'src/api/calc/types'
import { getSharedInstance } from 'src/api/calc/instances'
import { useConfig } from 'src/config'
import { t } from 'src/i18n/helpers'

defineOptions({ name: 'CalcReportInstanceShared' })
const route = useRoute()
const instance = ref<CalcInstance | null>(null)
const resultUrl = computed(() => instance.value?.resultPath ? new URL(instance.value.resultPath, `${useConfig().baseUrl}${useConfig().api}/`).toString() : '')
onMounted(async () => { instance.value = (await getSharedInstance(String(route.params.token))).data })
</script>

<style scoped>
.shared-instance { min-height: 620px; height: 100%; background: #fff; }
.shared-instance__header { min-height: 58px; }
.shared-instance__body { min-height: 0; }
.shared-instance__inputs { width: 330px; min-width: 330px; }
.shared-instance iframe { width: 100%; height: 100%; border: 0; }
@media (max-width: 760px) {
  .shared-instance__body { flex-direction: column; }
  .shared-instance__inputs { width: 100%; min-width: 0; height: 360px; }
}
</style>
