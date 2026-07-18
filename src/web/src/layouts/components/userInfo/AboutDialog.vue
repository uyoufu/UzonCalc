<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="about-dialog">
      <q-card-section class="row items-center q-py-sm">
        <div class="text-subtitle1 text-weight-medium">UzonCalc</div>
        <q-space />
        <CommonBtn flat dense icon="close" :tooltip="t('global.close')" @click="onDialogCancel" />
      </q-card-section>
      <q-separator />
      <q-card-section>
        <dl class="about-dialog__details">
          <dt>{{ t('userMenu.clientVersion') }}</dt>
          <dd>{{ clientVersion }}</dd>
          <dt>{{ t('userMenu.apiVersion') }}</dt>
          <dd>{{ apiVersion || '-' }}</dd>
          <dt>{{ t('userMenu.author') }}</dt>
          <dd>uyoufu</dd>
          <dt>{{ t('userMenu.project') }}</dt>
          <dd><a href="https://github.com/uzoncalc/uzoncalc" target="_blank" rel="noopener noreferrer">GitHub</a></dd>
        </dl>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Display product identity, client/API versions, author, and project URL. */
import { useDialogPluginComponent } from 'quasar'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import { getServerVersion } from 'src/api/system'
import { useConfig } from 'src/config'
import { t } from 'src/i18n/helpers'

defineEmits([...useDialogPluginComponent.emits])
const { dialogRef, onDialogHide, onDialogCancel } = useDialogPluginComponent()
const clientVersion = useConfig().version || '-'
const apiVersion = ref('')
onMounted(async () => { apiVersion.value = (await getServerVersion()).data })
</script>

<style scoped>
.about-dialog {
  width: min(400px, 92vw);
}

.about-dialog__details {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 14px 28px;
  margin: 0;
}

.about-dialog__details dt {
  color: #66736d;
}

.about-dialog__details dd {
  margin: 0;
  text-align: right;
}
</style>
