<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide" persistent>
    <q-card class="dependency-dialog column no-wrap">
      <q-card-section class="dependency-dialog__header row items-center">
        <q-icon name="account_tree" color="primary" size="22px" class="q-mr-sm" />
        <div class="text-subtitle1">{{ t('calcWorkspace.dependencies') }}</div>
        <span class="text-caption text-grey-7 q-ml-sm">{{ draftDependencies.length }}</span>
        <q-space />
        <CommonBtn flat dense icon="close" :tooltip="t('calcWorkspace.close')" @click="onDialogCancel" />
      </q-card-section>

      <q-separator />

      <div class="dependency-dialog__body row no-wrap col">
        <aside class="dependency-dialog__list column no-wrap">
          <div class="row items-center q-px-sm q-py-xs">
            <div class="text-subtitle2">{{ t('calcWorkspace.dependencies') }}</div>
            <q-space />
            <CommonBtn flat round dense icon="add" :tooltip="t('calcWorkspace.addDependency')"
              @click="onNewDependency" />
          </div>
          <q-separator />
          <q-list v-if="draftDependencies.length" class="dependency-dialog__items col scroll" dense>
            <q-item v-for="dependency in draftDependencies" :key="dependency.alias" clickable
              :active="editingAlias === dependency.alias" active-class="dependency-dialog__item--active"
              class="dependency-dialog__item" @click="onEditDependency(dependency)">
              <q-item-section>
                <div class="row items-center no-wrap q-gutter-x-xs">
                  <q-item-label class="text-weight-medium ellipsis">{{
                    dependency.alias
                  }}</q-item-label>
                  <q-badge outline color="primary" :label="dependencyVersionLabel(dependency)" />
                </div>
                <q-item-label caption class="row items-center no-wrap q-mt-xs">
                  <q-icon name="description" size="14px" class="q-mr-xs" />
                  <span class="ellipsis">{{ reportName(dependency.targetReportOid) }}</span>
                </q-item-label>
                <div class="dependency-dialog__reference row items-center no-wrap">
                  <q-icon name="terminal" size="14px" color="grey-7" class="q-mr-xs" />
                  <code class="dependency-dialog__reference-path">{{
                    dependencyReferencePath(dependency)
                  }}</code>
                  <CommonBtn flat round dense size="sm" icon="content_copy"
                    :tooltip="t('calcWorkspace.copyDependencyReference')"
                    @click.stop="onCopyDependencyReference(dependency)" />
                </div>
              </q-item-section>
              <q-item-section side top>
                <div class="dependency-dialog__actions row no-wrap">
                  <CommonBtn flat round dense size="sm" icon="edit" :tooltip="t('calcWorkspace.editDependency')"
                    @click.stop="onEditDependency(dependency)" />
                  <CommonBtn flat round dense size="sm" icon="delete" color="negative" :tooltip="t('global.delete')"
                    @click.stop="onDeleteDependency(dependency.alias)" />
                </div>
              </q-item-section>
            </q-item>
          </q-list>
          <div v-else class="col column items-center justify-center text-grey-6 q-pa-md">
            <q-icon name="account_tree" size="42px" />
            <div class="q-mt-sm text-caption">{{ t('calcWorkspace.noDependencies') }}</div>
          </div>
        </aside>

        <q-separator vertical />
        <section class="dependency-dialog__form col column no-wrap">
          <div class="text-subtitle2 q-px-md q-pt-md">
            {{
              editingAlias ? t('calcWorkspace.editDependency') : t('calcWorkspace.addDependency')
            }}
          </div>
          <LowCodeForm :key="formRevision" :fields="formFields" :validate="validateDependencyForm"
            :disable-default-btns="['cancel']" @ok="onDependencyFormConfirmed" />
        </section>
      </div>

      <q-separator />
      <q-card-actions align="right" class="dependency-dialog__footer">
        <CancelBtn @click="onDialogCancel" />
        <CommonBtn icon="done_all" :label="t('calcWorkspace.applyAndClose')" @click="onApply" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** Edit dependency aliases and versions in a detached LowCode draft. */
import { useDialogPluginComponent } from 'quasar'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import CancelBtn from 'src/components/quasarWrapper/buttons/CancelBtn.vue'
import LowCodeForm from 'src/components/lowCode/LowCodeForm.vue'
import { LowCodeFieldType, type ILowCodeField } from 'src/components/lowCode/types'
import {
  ReservedDependencySelectorKey,
  type CalcReport,
  type DependencySelector,
  type ReportDependency
} from 'src/api/calc/types'
import { listCalcReports } from 'src/api/calc/reports'
import { listVersions } from 'src/api/calc/versions'
import { getApiFailure } from '../../shared/apiFailure'
import { notifyError, notifySuccess } from 'src/utils/dialog'
import type { IFunctionResult } from 'src/types'
import { t } from 'src/i18n/helpers'

interface DependencyFormModel {
  alias: string
  targetReportOid: string
  dependencyVersion: string
}

interface SelectorOption {
  label: string
  value: string
  versionName: string | null
}

const props = defineProps<{ reportOid: string; dependencies: ReportDependency[] }>()
defineEmits([...useDialogPluginComponent.emits])
const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent()
const reports = ref<CalcReport[]>([])
const draftDependencies = ref<ReportDependency[]>([])
const editingAlias = ref<string | null>(null)
const formFields = ref<ILowCodeField[]>([])
const formRevision = ref(0)
let selectorRequestId = 0
const reportOptions = computed(() =>
  reports.value
    .filter((report) => report.reportOid !== props.reportOid && report.latestVersionName)
    .map((report) => ({ label: report.name, value: report.reportOid }))
)

/** Initialize the detached dependency list and available published reports. */
async function initializeDialog(): Promise<void> {
  draftDependencies.value = cloneDependencies(props.dependencies)
  try {
    const response = await listCalcReports({
      skip: 0,
      limit: 100,
      sortBy: 'name',
      descending: false
    })
    reports.value = response.data || []
  } catch (error) {
    notifyError(getApiFailure(error).message)
  }
  onNewDependency()
}
onMounted(initializeDialog)

/** Reset the LowCode editor to a new dependency. */
function onNewDependency(): void {
  selectorRequestId += 1
  editingAlias.value = null
  formFields.value = createDependencyFields(null, [latestSelectorOption()])
  formRevision.value += 1
}

/** Populate the LowCode editor from an existing dependency. */
async function onEditDependency(dependency: ReportDependency): Promise<void> {
  const requestId = ++selectorRequestId
  const options = await loadSelectorOptions(dependency.targetReportOid)
  if (requestId !== selectorRequestId) return
  editingAlias.value = dependency.alias
  formFields.value = createDependencyFields(dependency, options)
  formRevision.value += 1
}

/** Create the reactive LowCode field configuration for one dependency. */
function createDependencyFields(
  dependency: ReportDependency | null,
  selectorOptions: SelectorOption[]
): ILowCodeField[] {
  const dependencyVersion = dependency
    ? selectedDependencySelector(dependency)?.selectorKey || ReservedDependencySelectorKey.Latest
    : ReservedDependencySelectorKey.Latest
  return [
    {
      name: 'targetReportOid',
      label: t('calcWorkspace.targetReport'),
      type: LowCodeFieldType.selectOne,
      value: dependency?.targetReportOid || '',
      options: reportOptions.value,
      optionLabel: 'label',
      optionValue: 'value',
      mapOptions: true,
      emitValue: true,
      required: true,
      classes: 'col-12 col-md-6',
      onChanged: onTargetReportChanged
    },
    {
      name: 'alias',
      label: t('calcWorkspace.alias'),
      type: LowCodeFieldType.text,
      value: dependency?.alias || '',
      required: true,
      autofocus: true,
      classes: 'col-12 col-md-6'
    },
    {
      name: 'dependencyVersion',
      label: t('calcWorkspace.dependencyVersion'),
      type: LowCodeFieldType.selectOne,
      value: dependencyVersion,
      options: selectorOptions,
      optionLabel: 'label',
      optionValue: 'value',
      mapOptions: true,
      emitValue: true,
      required: true,
      classes: 'col-12'
    }
  ]
}

/** Reload selector options when the target report changes. */
async function onTargetReportChanged(
  value: unknown,
  _oldValue: unknown,
  allValues: Record<string, unknown>,
  allFields: ILowCodeField[]
): Promise<void> {
  const requestId = ++selectorRequestId
  const versionField = fieldByName(allFields, DependencyFormFieldName.DependencyVersion)
  const latestOption = latestSelectorOption()
  allValues.dependencyVersion = latestOption.value
  versionField.options = [latestOption]
  versionField.disable = true
  if (typeof value !== 'string' || !value) {
    versionField.disable = false
    return
  }
  const options = await loadSelectorOptions(value)
  if (requestId !== selectorRequestId) return
  versionField.options = options
  versionField.disable = false
}

/** Validate one dependency form before it changes the detached list. */
function validateDependencyForm(values: Record<string, unknown>): Promise<IFunctionResult> {
  const alias = typeof values.alias === 'string' ? values.alias.trim() : ''
  if (!/^[A-Za-z_][A-Za-z0-9_]{0,63}$/.test(alias)) {
    return Promise.resolve({ ok: false, message: t('calcWorkspace.dependencyAliasInvalid') })
  }
  const duplicate = draftDependencies.value.some(
    (dependency) => dependency.alias === alias && dependency.alias !== editingAlias.value
  )
  if (duplicate)
    return Promise.resolve({ ok: false, message: t('calcWorkspace.dependencyAliasExists') })
  return Promise.resolve({ ok: true })
}

/** Add or replace one validated dependency in the detached list. */
function onDependencyFormConfirmed(values: Record<string, unknown>): void {
  const model = values as unknown as DependencyFormModel
  const selectorOptions = fieldByName(formFields.value, DependencyFormFieldName.DependencyVersion)
    .options as SelectorOption[]
  const selectedOption =
    selectorOptions.find((candidate) => candidate.value === model.dependencyVersion) ||
    latestSelectorOption()
  const dependency: ReportDependency = {
    alias: model.alias.trim(),
    targetReportOid: model.targetReportOid,
    selectors: [
      {
        selectorKey: selectedOption.value,
        versionName: selectedOption.versionName,
        isDefault: true
      }
    ]
  }
  const existingIndex = editingAlias.value
    ? draftDependencies.value.findIndex((candidate) => candidate.alias === editingAlias.value)
    : -1
  if (existingIndex >= 0) draftDependencies.value.splice(existingIndex, 1, dependency)
  else draftDependencies.value.push(dependency)
  onNewDependency()
}

/** Delete one dependency from the detached list without affecting the workspace. */
function onDeleteDependency(alias: string): void {
  draftDependencies.value = draftDependencies.value.filter(
    (dependency) => dependency.alias !== alias
  )
  if (editingAlias.value === alias) onNewDependency()
}

/** Load latest and explicit version selectors for one target report. */
async function loadSelectorOptions(reportOid: string): Promise<SelectorOption[]> {
  const options = [latestSelectorOption()]
  try {
    const response = await listVersions(reportOid)
    options.push(
      ...(response.data || []).map((version) => ({
        label: version.versionName,
        value: version.importSegment,
        versionName: version.versionName
      }))
    )
  } catch (error) {
    notifyError(getApiFailure(error).message)
  }
  return options
}

/** Return the reserved latest selector option. */
function latestSelectorOption(): SelectorOption {
  return {
    label: ReservedDependencySelectorKey.Latest,
    value: ReservedDependencySelectorKey.Latest,
    versionName: null
  }
}

/** Find a named field in the current LowCode form contract. */
function fieldByName(fields: ILowCodeField[], name: DependencyFormFieldName): ILowCodeField {
  const field = fields.find((candidate) => candidate.name === name)
  if (!field) throw new Error(`Dependency field not found: ${name}`)
  return field
}

const DependencyFormFieldName = {
  Alias: 'alias',
  TargetReportOid: 'targetReportOid',
  DependencyVersion: 'dependencyVersion'
} as const
type DependencyFormFieldName =
  (typeof DependencyFormFieldName)[keyof typeof DependencyFormFieldName]

/** Resolve a report OID into its display name. */
function reportName(reportOid: string): string {
  return reports.value.find((report) => report.reportOid === reportOid)?.name || reportOid
}

/** Return the declared default selector, falling back to the first legacy selector. */
function selectedDependencySelector(dependency: ReportDependency): DependencySelector | null {
  return (
    dependency.selectors.find((selector) => selector.isDefault) || dependency.selectors[0] || null
  )
}

/** Format the selected dependency version for display. */
function dependencyVersionLabel(dependency: ReportDependency): string {
  const selector = selectedDependencySelector(dependency)
  return selector?.versionName || selector?.selectorKey || ReservedDependencySelectorKey.Latest
}

/** Build the public namespace prefix used to import one dependency. */
function dependencyReferencePath(dependency: ReportDependency): string {
  const selectorKey = selectedDependencySelector(dependency)?.selectorKey
  if (!selectorKey || selectorKey === ReservedDependencySelectorKey.Latest)
    return `calcdeps.${dependency.alias}`
  return `calcdeps.${dependency.alias}.${selectorKey}`
}

/** Copy one dependency namespace prefix and report clipboard failures. */
async function onCopyDependencyReference(dependency: ReportDependency): Promise<void> {
  try {
    await navigator.clipboard.writeText(dependencyReferencePath(dependency))
    notifySuccess(t('calcWorkspace.dependencyReferenceCopied'))
  } catch {
    notifyError(t('calcWorkspace.dependencyReferenceCopyFailed'))
  }
}

/** Return the complete detached dependency list to the workspace. */
function onApply(): void {
  onDialogOK(cloneDependencies(draftDependencies.value))
}

/** Copy dependency DTOs without carrying Vue reactive proxies into dialog state. */
function cloneDependencies(dependencies: ReportDependency[]): ReportDependency[] {
  return dependencies.map((dependency) => ({
    alias: dependency.alias,
    targetReportOid: dependency.targetReportOid,
    selectors: dependency.selectors.map((selector) => ({ ...selector }))
  }))
}
</script>

<style scoped>
.dependency-dialog {
  width: min(960px, 94vw);
  height: min(680px, 86vh);
  max-width: 960px;
}

.dependency-dialog__header {
  min-height: 54px;
}

.dependency-dialog__body {
  min-height: 0;
}

.dependency-dialog__list {
  width: 340px;
  min-width: 340px;
}

.dependency-dialog__items {
  padding: 8px;
}

.dependency-dialog__item {
  min-height: 112px;
  margin-bottom: 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 6px;
}

.dependency-dialog__item:last-child {
  margin-bottom: 0;
}

.dependency-dialog__item--active {
  color: inherit;
  background: #eef6ff;
  border-color: #90caf9;
}

.dependency-dialog__reference {
  min-width: 0;
  margin-top: 6px;
  padding: 3px 2px 3px 8px;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 4px;
}

.dependency-dialog__reference-path {
  min-width: 0;
  overflow: hidden;
  color: #424242;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dependency-dialog__actions {
  gap: 2px;
}

.dependency-dialog__form {
  min-width: 0;
  overflow-y: auto;
}

.dependency-dialog__footer {
  min-height: 56px;
}

@media (max-width: 760px) {
  .dependency-dialog__body {
    flex-direction: column;
    overflow-y: auto;
  }

  .dependency-dialog__list {
    width: 100%;
    min-width: 0;
    min-height: 220px;
    max-height: 260px;
  }

  .dependency-dialog__body>.q-separator--vertical {
    display: none;
  }
}
</style>
