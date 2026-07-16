# 表格组件使用说明

通用表格优先使用 Quasar `q-table`，并通过 `src/compositions/qTableUtils` 管理分页、加载、筛选和行级更新。新页面可以先复制 `tableExample.vue` 的结构，再按业务接口替换列定义和请求函数。

## 基本用法

```vue
<template>
  <q-table
    :rows="rows"
    :columns="columns"
    row-key="id"
    v-model:pagination="pagination"
    :loading="loading"
    :filter="filter"
    @request="onTableRequest"
  >
    <template #body-cell-index="props">
      <QTableIndex :props="props" />
    </template>
  </q-table>
</template>

<script lang="ts" setup>
import type { QTableColumn } from 'quasar'
import { useQTable, useQTableIndex } from 'src/compositions/qTableUtils'
import type { IRequestPagination, TTableFilterObject } from 'src/compositions/types'

const { indexColumn, QTableIndex } = useQTableIndex()

const columns: ComputedRef<QTableColumn[]> = computed(() => [
  indexColumn,
  { name: 'name', label: '名称', field: 'name', align: 'left', sortable: true }
])

async function getRowsNumberCount(filterObj: TTableFilterObject) {
  return (await requestPageCount(filterObj)).data
}

async function requestTableRows(filterObj: TTableFilterObject, pagination: IRequestPagination) {
  return (
    await requestPageRows({
      filter: filterObj.filter,
      skip: pagination.skip,
      limit: pagination.limit
    })
  ).data.rows
}

const { rows, pagination, filter, loading, onTableRequest, refreshTable } = useQTable({
  getRowsNumberCount,
  onRequest: requestTableRows
})
</script>
```

`tableExample.vue` 是骨架模板，其中 `getRowsNumberCount` 返回 `0`、`onRequest` 返回空数组；复制后必须替换为真实业务接口。

## useQTable 参数

| 参数                        | 类型                                                                                               | 说明                                                                                         |
| --------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `sortBy`                    | `string`                                                                                           | 初始排序字段，默认 `id`。                                                                    |
| `descending`                | `boolean`                                                                                          | 初始是否倒序，默认 `true`。                                                                  |
| `rowsPerPage`               | `number`                                                                                           | 初始每页行数，默认 `10`。                                                                    |
| `filterFactor`              | `(filter: string) => TTableFilterObject \| Promise<TTableFilterObject>`                            | 将 `q-table` 的 `filter` 转换为业务查询对象；返回值会自动合并内部 `refreshCounter`。          |
| `getRowsNumberCount`        | `(filterObj: TTableFilterObject) => number \| Promise<number>`                                     | 获取符合筛选条件的数据总数。                                                                 |
| `onRequest`                 | `(filterObj: TTableFilterObject, pagination: IRequestPagination) => object[] \| Promise<object[]>` | 获取当前页数据。只有总数大于 `0` 时才会调用。                                                |
| `preventRequestWhenMounted` | `boolean`                                                                                          | 设为 `true` 时阻止组件挂载后自动请求，适合需要先加载筛选条件再手动 `refreshTable()` 的页面。 |

`IRequestPagination` 中的 `skip` 和 `limit` 用于后端分页。`rowsPerPage` 为 `0` 时表示请求全部数据，此时 `limit` 会等于当前总数。

## 返回值

| 返回值                              | 说明                                                |
| ----------------------------------- | --------------------------------------------------- |
| `rows`                              | 表格行数据，绑定到 `q-table` 的 `:rows`。           |
| `pagination`                        | 分页状态，绑定到 `v-model:pagination`。             |
| `filter`                            | 筛选触发值，绑定到 `q-table` 的 `:filter`。         |
| `loading`                           | 请求加载状态，绑定到 `:loading`。                   |
| `selectedRows`                      | 已选行容器，可绑定到 `q-table` 选择状态。           |
| `onTableRequest`                    | 传给 `q-table` 的 `@request`。                      |
| `refreshTable()`                    | 重新按当前分页和筛选请求数据。                      |
| `addNewRow(newRow, idField?)`       | 新增一行；若相同 `idField` 已存在，则合并更新该行。 |
| `updateExistOne(newData, idField?)` | 只更新已存在的行，成功返回 `true`。                 |
| `deleteRowById(id, idField?)`       | 按字符串或数字 id 删除行，并减少总数；`id` 为空时不处理。 |
| `getSelectedRows(cursorData)`       | 若存在多选行则返回多选行，否则返回当前行。          |

当只有单个数据项变化时，优先使用 `addNewRow`、`updateExistOne`、`deleteRowById` 更新本地行，不要刷新整个表格。

## 筛选和刷新

- 简单搜索可以直接把搜索框绑定到 `filter`。
- 多条件搜索推荐在页面中维护独立查询状态，并通过 `filterFactor` 转换为后端请求对象。
- 需要点击按钮触发搜索时，先把 `pagination.value.page` 设为 `1`，再更新 `filter.value` 或调用 `refreshTable()`。
- `getRowsNumberCount` 内部会按 `JSON.stringify(filterObj)` 缓存总数；若筛选对象没有变化，不会重复请求总数。

## 索引列

使用 `useQTableIndex()` 可以获得统一序号列：

```ts
const { indexColumn, QTableIndex } = useQTableIndex()

const columns = computed(() => [
  indexColumn
  // other columns
])
```

模板中必须提供 `body-cell-index` 插槽：

```vue
<template #body-cell-index="props">
  <QTableIndex :props="props" />
</template>
```

## 多语言列

需要支持多语言切换的表格，`columns` 必须使用 `computed` 返回，并在 `label` 中调用对应翻译函数：

```ts
const columns: ComputedRef<QTableColumn[]> = computed(() => [
  { name: 'username', label: translateSystemSettings('user.username'), field: 'username', align: 'left' }
])
```

## 注意事项

- `row-key` 默认优先使用 `id`，若业务主键不是 `id`，行级更新方法也要传入相同的 `idField`。
- `onRequest` 负责返回当前页行数据，不要在其中修改 `rows`、`pagination` 或 `loading`。
- `filterFactor` 返回业务筛选对象即可；`useQTable` 会自动合并内部刷新计数，使 `refreshTable()` 强制重新请求总数。
- `deleteRowById` 会直接减少 `pagination.rowsNumber`，只有后端删除成功后再调用。

