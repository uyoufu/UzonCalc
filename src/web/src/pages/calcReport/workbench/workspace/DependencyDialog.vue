<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide" persistent>
    <q-card class="dependency-dialog">
      <q-card-section class="row items-center">
        <div class="text-subtitle1">{{ t('calcWorkspace.dependencies') }}</div><q-space /><q-btn flat round dense
          icon="close" @click="onDialogCancel" />
      </q-card-section>
      <q-separator />
      <q-card-section class="q-gutter-md">
        <div class="row q-col-gutter-sm">
          <q-input v-model="alias" class="col" dense outlined :label="t('calcWorkspace.alias')" />
          <q-select v-model="targetReportOid" class="col" dense outlined emit-value map-options :options="reportOptions"
            :label="t('calcWorkspace.targetReport')" @update:model-value="onTargetChanged" />
        </div>
        <q-select v-model="selectedSelectors" dense outlined multiple use-chips emit-value map-options
          :options="selectorOptions" :label="t('calcWorkspace.selectors')" />
        <q-select v-model="defaultSelector" dense outlined emit-value map-options :options="selectedSelectorOptions"
          :label="t('calcWorkspace.defaultSelector')" />
        <div class="row justify-end">
          <CommonBtn icon="add" :label="t('global.add')" :disable="!canAdd" @click="onAdd" />
        </div>
      </q-card-section>
      <q-separator />
      <q-list separator class="dependency-dialog__list">
        <q-item v-for="dependency in draftDependencies" :key="dependency.alias">
          <q-item-section><q-item-label>{{ dependency.alias }}</q-item-label><q-item-label caption>{{
            reportName(dependency.targetReportOid) }} · {{dependency.selectors.map((selector) =>
                selector.selectorKey).join(', ') }}</q-item-label></q-item-section>
          <q-item-section side><q-btn flat round dense icon="delete" color="negative"
              @click="removeDependency(dependency.alias)" /></q-item-section>
        </q-item>
      </q-list>
      <q-card-actions align="right">
        <CancelBtn @click="onDialogCancel" />
        <OkBtn @click="onApply" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Edit report dependency aliases and version selectors as one atomic value. */
import { useDialogPluginComponent } from 'quasar'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import CancelBtn from 'src/components/quasarWrapper/buttons/CancelBtn.vue'
import OkBtn from 'src/components/quasarWrapper/buttons/OkBtn.vue'
import type { CalcReport, ReportDependency } from 'src/api/calc/types'
import { listCalcReports } from 'src/api/calc/reports'
import { listVersions } from 'src/api/calc/versions'
import { t } from 'src/i18n/helpers'

const props = defineProps<{ reportOid: string; dependencies: ReportDependency[] }>()
defineEmits([...useDialogPluginComponent.emits])
const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent()
const reports = ref<CalcReport[]>([])
const draftDependencies = ref<ReportDependency[]>([])
const alias = ref('')
const targetReportOid = ref<string | null>(null)
const selectedSelectors = ref<string[]>(['latest'])
const defaultSelector = ref('latest')
const selectorOptions = ref<Array<{ label: string; value: string; versionName: string | null }>>([{ label: 'latest', value: 'latest', versionName: null }])
const reportOptions = computed(() => reports.value.filter((report) => report.reportOid !== props.reportOid && report.latestVersionName).map((report) => ({ label: report.name, value: report.reportOid })))
const selectedSelectorOptions = computed(() => selectorOptions.value.filter((option) => selectedSelectors.value.includes(option.value)))
const canAdd = computed(() => /^[A-Za-z_][A-Za-z0-9_]{0,63}$/.test(alias.value) && Boolean(targetReportOid.value) && selectedSelectors.value.length > 0 && selectedSelectors.value.includes(defaultSelector.value) && !draftDependencies.value.some((dependency) => dependency.alias === alias.value))

/** Initialize a detached dependency draft and its report choices. */
async function initializeDialog(): Promise<void> {
  draftDependencies.value = structuredClone(props.dependencies)
  const response = await listCalcReports({ skip: 0, limit: 100, sortBy: 'name', descending: false })
  reports.value = response.data || []
}
onMounted(initializeDialog)

/** Load explicit version selector options for the selected dependency report. */
async function onTargetChanged(reportOid: string | null): Promise<void> {
  selectedSelectors.value = ['latest']
  defaultSelector.value = 'latest'
  selectorOptions.value = [{ label: 'latest', value: 'latest', versionName: null }]
  if (!reportOid) return
  const response = await listVersions(reportOid)
  selectorOptions.value.push(...(response.data || []).map((version) => ({ label: version.importSegment, value: version.importSegment, versionName: version.versionName })))
}
/** Add the current dependency form to the draft list. */
function onAdd(): void {
  if (!canAdd.value || !targetReportOid.value) return
  draftDependencies.value.push({
    alias: alias.value,
    targetReportOid: targetReportOid.value,
    selectors: selectedSelectors.value.map((key) => {
      const option = selectorOptions.value.find((candidate) => candidate.value === key)!
      return { selectorKey: key, versionName: option.versionName, isDefault: key === defaultSelector.value }
    })
  })
  alias.value = ''
}
/** Remove one dependency alias. */
function removeDependency(value: string): void { draftDependencies.value = draftDependencies.value.filter((dependency) => dependency.alias !== value) }
/** Resolve a report OID into its display name. */
function reportName(reportOid: string): string { return reports.value.find((report) => report.reportOid === reportOid)?.name || reportOid }
/** Return a detached dependency draft to the calling workspace. */
function onApply(): void { onDialogOK(structuredClone(draftDependencies.value)) }
</script>

<style
  scoped>
  .dependency-dialog {
    width: min(780px, 92vw);
    max-width: 780px;
  }

  .dependency-dialog__list {
    max-height: 300px;
    overflow: auto;
  }
</style>
