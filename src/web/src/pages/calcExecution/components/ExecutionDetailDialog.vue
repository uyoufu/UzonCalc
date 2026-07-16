<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="execution-detail-dialog">
      <q-card-section class="row items-center">
        <div class="text-subtitle1">{{ execution.executionId }}</div>
        <q-space />
        <q-btn flat round dense icon="close" @click="onDialogCancel" />
      </q-card-section>
      <q-separator />
      <q-card-section class="execution-detail-dialog__content">
        <dl>
          <template v-for="field in detailFields" :key="field">
            <dt>{{ field }}</dt>
            <dd>{{ execution[field] }}</dd>
          </template>
        </dl>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Display immutable provenance and status fields for one managed execution. */
import { useDialogPluginComponent } from 'quasar'
import type { CalcExecution } from 'src/api/calc/types'

defineProps<{ execution: CalcExecution }>()
defineEmits([...useDialogPluginComponent.emits])

const { dialogRef, onDialogHide, onDialogCancel } = useDialogPluginComponent()
const detailFields: Array<keyof CalcExecution> = [
  'reportOid',
  'sourceType',
  'resolvedVersion',
  'sourceArtifactHash',
  'executionArtifactHash',
  'bundleHash',
  'runtimeFingerprint',
  'executorType',
  'backendMode',
  'status',
  'createdAt',
  'completedAt'
]
</script>

<style scoped>
.execution-detail-dialog {
  width: min(760px, 92vw);
  max-width: 760px;
}

.execution-detail-dialog__content dl {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 8px 16px;
}

.execution-detail-dialog__content dt {
  color: #667085;
}

.execution-detail-dialog__content dd {
  margin: 0;
  overflow-wrap: anywhere;
}
</style>
