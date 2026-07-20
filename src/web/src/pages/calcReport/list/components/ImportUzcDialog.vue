<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="import-uzc-dialog">
      <q-card-section class="text-subtitle1">{{ t('calcWorkspace.importArchive') }}</q-card-section>
      <q-card-section class="q-gutter-md">
        <q-select v-model="categoryOid" dense options-dense outlined emit-value map-options :options="categoryOptions"
          :label="t('calcWorkspace.categoryName')" />
        <q-input v-model="name" dense outlined :label="t('calcWorkspace.reportName')" />
        <q-file v-model="archive" dense outlined accept=".png,.uzc" :label="t('calcWorkspace.archiveFile')" />
      </q-card-section>
      <q-card-actions align="right">
        <CancelBtn @click="onDialogCancel" />
        <OkBtn :disable="!canImport" @click="onImport" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Import one portable v3 archive through a Quasar component dialog. */
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
  defaultCategoryOid?: string
}>()

defineEmits([...useDialogPluginComponent.emits])

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent()
const categoryOid = ref(props.defaultCategoryOid || '')
const name = ref('')
const archive = ref<File | null>(null)
const canImport = computed(() => Boolean(categoryOid.value && name.value.trim() && archive.value))

/** Return the validated archive selection to the page entrypoint. */
function onImport(): void {
  if (!archive.value || !canImport.value) return
  const input: ImportUzcInput = {
    categoryOid: categoryOid.value,
    name: name.value,
    archive: archive.value
  }
  onDialogOK(input)
}
</script>

<style scoped>
.import-uzc-dialog {
  width: min(520px, 92vw);
  max-width: 520px;
}
</style>
