<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="import-uzc-dialog">
      <q-card-section class="text-subtitle1">{{ t('calcWorkspace.importUzc') }}</q-card-section>
      <q-card-section class="q-gutter-md">
        <q-select v-model="categoryOid" dense outlined emit-value map-options :options="categoryOptions"
          :label="t('calcWorkspace.categoryName')" />
        <q-input v-model="name" dense outlined :label="t('calcWorkspace.reportName')" />
        <q-file v-model="archive" dense outlined accept=".uzc" :label="t('calcWorkspace.uzcFile')" />
      </q-card-section>
      <q-card-actions align="right">
        <CancelBtn @click="onDialogCancel" />
        <OkBtn :loading="isImporting" :disable="!canImport" @click="onImport" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Import one UZC archive through a Quasar component dialog. */
import { useDialogPluginComponent } from 'quasar'
import CancelBtn from 'src/components/quasarWrapper/buttons/CancelBtn.vue'
import OkBtn from 'src/components/quasarWrapper/buttons/OkBtn.vue'
import type { DialogSelectOption } from '../../shared/dialogForm'
import { t } from 'src/i18n/helpers'

interface ImportUzcInput {
  categoryOid: string
  name: string
  archive: File
}

const props = defineProps<{
  categoryOptions: DialogSelectOption[]
  onSubmit: (input: ImportUzcInput) => Promise<void>
}>()

defineEmits([...useDialogPluginComponent.emits])

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent()
const categoryOid = ref('')
const name = ref('')
const archive = ref<File | null>(null)
const isImporting = ref(false)
const canImport = computed(() => Boolean(categoryOid.value && name.value.trim() && archive.value))

/** Submit the selected archive and close only after a successful import. */
async function onImport(): Promise<void> {
  if (!archive.value || !canImport.value) return
  isImporting.value = true
  try {
    await props.onSubmit({ categoryOid: categoryOid.value, name: name.value, archive: archive.value })
    onDialogOK()
  } finally {
    isImporting.value = false
  }
}
</script>

<style scoped>
.import-uzc-dialog {
  width: min(520px, 92vw);
  max-width: 520px;
}
</style>
