<template>
  <div class="full-height column card-like">
    <q-splitter v-model="splitterModel" class="full-height col no-wrap">
      <template #before>
        <CalcInputForm v-model="fullHtmlUrl" :report-oid="reportOid" :file-path="filePath" :is-silent="isSilent">
        </CalcInputForm>
      </template>

      <template #after>
        <div class="full-height overflow-hidden">
          <div v-if="!fullHtmlUrl" class="full-height text-grey-6 column justify-center">
            <div class="text-center">
              <q-icon name="article" size="xl" />
              <div>{{ tCalcReportPageViewer('pleaseStartExecution') }}</div>
            </div>
          </div>
          <iframe v-else :src="fullHtmlUrl" class="full-height full-width" frameborder="0"></iframe>
        </div>
      </template>
    </q-splitter>
  </div>
</template>

<script lang="ts" setup>
import { tCalcReportPageViewer } from 'src/i18n/helpers'
import CalcInputForm from './components/CalcInputForm.vue'

defineProps({
  // 报告的 oid
  reportOid: {
    type: String,
    required: false,
    default: null
  },

  // 指定的文件路径
  filePath: {
    type: String,
    required: false,
    default: ''
  },

  // 是否静默执行
  isSilent: {
    type: Boolean,
    required: false,
    default: true
  }
})

const splitterModel = ref(30)

const fullHtmlUrl = ref('')
</script>

<style lang="scss" scoped></style>
