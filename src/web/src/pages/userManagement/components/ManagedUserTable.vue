<template>
  <q-table flat dense class="full-height" row-key="userOid" :rows="rows" :columns="columns" :loading="loading"
    v-model:pagination="pagination" :filter="filter" binary-state-sort @request="onTableRequest">
    <template #top-left>
      <CommonBtn icon="person_add" :label="t('userManagement.addUser')" @click="onCreateUser" />
    </template>
    <template #top-right>
      <SearchInput v-model="filter" />
    </template>
    <template #body-cell-status="tableProps">
      <q-td :props="tableProps"><q-chip dense square
          :color="tableProps.row.status === UserStatus.Active ? 'positive' : 'grey-7'" text-color="white">{{
            statusLabel(tableProps.row.status) }}</q-chip></q-td>
    </template>
    <template #body-cell-username="tableProps">
      <q-td :props="tableProps">{{ tableProps.row.username }}</q-td>
      <ContextMenu :items="contextMenuItems" :value="tableProps.row" />
    </template>
  </q-table>
</template>

<script setup lang="ts">
/** Paginated administrator user table with create, status, and reset actions. */
import type { QTableColumn } from 'quasar'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import SearchInput from 'src/components/searchInput/SearchInput.vue'
import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import { countManagedUsers, createManagedUser, listManagedUsers, resetManagedUserPassword, setManagedUserStatus, type DepartmentNode, type ManagedUser } from 'src/api/adminUsers'
import { UserStatus } from 'src/stores/types'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import { notifySuccess } from 'src/utils/dialog'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { useQTable } from 'src/compositions/qTableUtils'
import type { IRequestPagination, TTableFilterObject } from 'src/compositions/types'
import { t } from 'src/i18n/helpers'
import { formatDate } from 'src/utils/format'

const props = defineProps<{ departmentOid: string | null; departments: DepartmentNode[] }>()
const columns: ComputedRef<QTableColumn<ManagedUser>[]> = computed(() => [
  { name: 'username', label: t('userManagement.username'), field: 'username', align: 'left', sortable: true },
  { name: 'nickName', label: t('userPage.nickName'), field: (user) => user.nickName || '-', align: 'left', sortable: true },
  { name: 'status', label: t('userManagement.status'), field: 'status', align: 'left', sortable: true },
  { name: 'createdAt', label: t('userManagement.createdAt'), field: 'createdAt', format: (value) => formatDate(value), align: 'left', sortable: true }
])

/** Convert table text and selected subtree into API filters. */
function filterFactor(value: string): TTableFilterObject {
  return { filter: value, departmentOid: props.departmentOid || '' }
}

/** Count managed users matching the selected subtree and text. */
async function getRowsNumberCount(filters: TTableFilterObject): Promise<number> {
  return (await countManagedUsers({ query: typeof filters.filter === 'string' ? filters.filter : undefined, departmentOid: typeof filters.departmentOid === 'string' ? filters.departmentOid : undefined })).data || 0
}

/** Request one stable page of managed users. */
async function requestRows(filters: TTableFilterObject, page: IRequestPagination): Promise<ManagedUser[]> {
  return (await listManagedUsers({ query: typeof filters.filter === 'string' ? filters.filter : undefined, departmentOid: typeof filters.departmentOid === 'string' ? filters.departmentOid : undefined, ...page })).data || []
}

const { rows, pagination, filter, loading, onTableRequest, refreshTable, addNewRow, updateExistOne } = useQTable<ManagedUser>({
  sortBy: 'createdAt', descending: true, rowsPerPage: 20, filterFactor, getRowsNumberCount, onRequest: requestRows
})
watch(() => props.departmentOid, () => { pagination.value.page = 1; refreshTable() })

/** Collect credentials and memberships for a new managed user. */
async function onCreateUser(): Promise<void> {
  const result = await showDialog<{ username: string; nickName: string; password: string; departmentOids: string[] }>({
    title: t('userManagement.addUser'),
    oneColumn: true,
    fields: [
      { name: 'username', label: t('userManagement.username'), required: true },
      { name: 'nickName', label: t('userPage.nickName') },
      { name: 'password', label: t('userManagement.initialPassword'), type: LowCodeFieldType.password, required: true },
      { name: 'departmentOids', label: t('userManagement.departments'), type: LowCodeFieldType.selectMany, value: props.departmentOid ? [props.departmentOid] : [], options: props.departments.map((department) => ({ label: department.name, value: department.departmentOid })), optionLabel: 'label', optionValue: 'value', emitValue: true, mapOptions: true }
    ]
  })
  if (!result.ok) return
  addNewRow((await createManagedUser(result.data)).data, 'userOid')
}

/** Enable or disable one selected account and patch only its row. */
async function onSetStatus(user: ManagedUser, status: UserStatus): Promise<void> {
  updateExistOne((await setManagedUserStatus(user.userOid, status)).data, 'userOid')
}

/** Collect and submit a replacement password for one managed user. */
async function onResetPassword(user: ManagedUser): Promise<void> {
  const result = await showDialog<{ newPassword: string }>({ title: t('userManagement.resetPassword'), oneColumn: true, fields: [{ name: 'newPassword', label: t('userPage.newPassword'), type: LowCodeFieldType.password, required: true }] })
  if (!result.ok) return
  await resetManagedUserPassword(user.userOid, result.data.newPassword)
  notifySuccess(t('userManagement.passwordReset'))
}

const contextMenuItems: IContextMenuItem<ManagedUser>[] = [
  { name: 'disable', label: t('userManagement.disableUser'), icon: 'person_off', color: 'warning', vif: (user) => user.status === UserStatus.Active, onClick: (user) => onSetStatus(user, UserStatus.Forbidden_login) },
  { name: 'enable', label: t('userManagement.enableUser'), icon: 'person', color: 'positive', vif: (user) => user.status !== UserStatus.Active, onClick: (user) => onSetStatus(user, UserStatus.Active) },
  { name: 'reset-password', label: t('userManagement.resetPassword'), icon: 'password', color: 'primary', onClick: onResetPassword }
]

/** Return a localized account-state label. */
function statusLabel(status: UserStatus): string {
  return status === UserStatus.Active ? t('userManagement.enabled') : t('userManagement.disabled')
}
</script>
