<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="workspace-conflict-dialog">
      <q-card-section class="text-subtitle1 text-primary text-bold">
        {{ t('calcWorkspace.revisionConflict') }}
      </q-card-section>
      <q-card-section>
        <div class="q-mb-md">{{ t('calcWorkspace.revisionConflictMessage') }}</div>
        <q-option-group v-model="resolution" type="radio" color="primary" :options="resolutionOptions" />
      </q-card-section>
      <q-card-actions align="right">
        <CancelBtn @click="onDialogCancel" />
        <OkBtn @click="onConfirm" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Present non-destructive recovery choices for a workspace revision conflict. */
import { useDialogPluginComponent } from 'quasar'
import CancelBtn from 'src/components/quasarWrapper/buttons/CancelBtn.vue'
import OkBtn from 'src/components/quasarWrapper/buttons/OkBtn.vue'
import { t } from 'src/i18n/helpers'
import { WorkspaceConflictResolution } from './workspaceConflict'

defineEmits([...useDialogPluginComponent.emits])
const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent()
const resolution = ref(WorkspaceConflictResolution.ExportLocalZip)
const resolutionOptions = [
  { label: t('calcWorkspace.exportLocalZip'), value: WorkspaceConflictResolution.ExportLocalZip },
  { label: t('calcWorkspace.discardAndReload'), value: WorkspaceConflictResolution.DiscardAndReload }
]

/** Return the selected recovery action to the workspace. */
function onConfirm(): void {
  onDialogOK(resolution.value)
}
</script>

<style scoped>
.workspace-conflict-dialog {
  width: min(520px, 92vw);
  max-width: 520px;
}
</style>
