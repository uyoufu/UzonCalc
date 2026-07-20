<template>
  <div class="user-management row no-wrap full-height">
    <DepartmentTreePanel v-model="selectedDepartmentOid" :departments="departments" @changed="loadDepartments" />
    <ManagedUserTable class="col" :department-oid="selectedDepartmentOid" :departments="departments" />
  </div>
</template>

<script setup lang="ts">
/** Administrator page coordinating department filtering and managed users. */
import DepartmentTreePanel from './components/DepartmentTreePanel.vue'
import ManagedUserTable from './components/ManagedUserTable.vue'
import { listDepartments, type DepartmentNode } from 'src/api/adminUsers'

defineOptions({ name: 'UserManagementIndex' })
const departments = ref<DepartmentNode[]>([])
const selectedDepartmentOid = ref<string | null>(null)

/** Reload the flat organization tree after one confirmed mutation. */
async function loadDepartments(): Promise<void> {
  departments.value = (await listDepartments()).data || []
  if (selectedDepartmentOid.value && !departments.value.some((department) => department.departmentOid === selectedDepartmentOid.value)) {
    selectedDepartmentOid.value = null
  }
}
onMounted(loadDepartments)
</script>

<style scoped>
.user-management { min-height: 620px; height: 100%; overflow: hidden; background: #fff; }
</style>
