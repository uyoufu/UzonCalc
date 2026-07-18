<template>
  <q-dialog ref="dialogRef" persistent>
    <q-card class="image-cropper-card column no-wrap">
      <Cropper ref="cropperRef" class="image-cropper" :src="sourceUrl" :stencil-props="{ aspectRatio: 1 }"
        image-restriction="stencil" />
      <div class="row justify-end q-pa-sm q-gutter-sm">
        <CancelBtn @click="onDialogCancel" />
        <OkBtn @click="onOkClick" />
      </div>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Crop an uploaded avatar to a normalized square PNG blob. */
import { useDialogPluginComponent } from 'quasar'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'
import OkBtn from '../quasarWrapper/buttons/OkBtn.vue'
import CancelBtn from '../quasarWrapper/buttons/CancelBtn.vue'

const props = defineProps<{ img: Blob | string }>()
defineEmits([...useDialogPluginComponent.emits])
const { dialogRef, onDialogOK, onDialogCancel } = useDialogPluginComponent()
const cropperRef = ref<InstanceType<typeof Cropper>>()
const objectUrl = ref<string | null>(null)
const sourceUrl = computed(() => {
  if (typeof props.img === 'string') return props.img
  objectUrl.value ||= URL.createObjectURL(props.img)
  return objectUrl.value
})
onBeforeUnmount(() => {
  if (objectUrl.value) URL.revokeObjectURL(objectUrl.value)
})

/** Convert the current crop canvas into the uploaded PNG. */
async function onOkClick(): Promise<void> {
  const canvas = cropperRef.value?.getResult().canvas
  if (!canvas) return
  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png', 0.1))
  if (blob) onDialogOK(blob)
}
</script>

<style scoped>
.image-cropper-card {
  width: min(560px, 94vw);
  height: min(620px, 86vh);
}

.image-cropper {
  flex: 1;
  min-height: 360px;
  background: #161b19;
}
</style>
