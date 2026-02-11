---
name: context-menu
description: right-click context menu for table rows
---

# Context Menu Skill

该技能为表格行提供右键菜单功能，允许用户在表格行上点击右键以访问特定于该行的操作选项。

# 实现步骤

1. 从 `import ContextMenu from 'src/components/contextMenu/ContextMenu.vue'` 导入 ContextMenu 组件。
2. 在 q-table 的 body-cell 插槽中，添加 ContextMenu 组件：

```vue
<template v-slot:body-cell-index="props">
  <QTableIndex :props="props" />
  <ContextMenu :items="itemContextMenuItems" :value="props.row"></ContextMenu>
</template>
```

3. 定义 `itemContextMenuItems`，这是一个包含菜单项的数组，其值应为 `ComputedRef<IContextMenuItem[]>`：

```ts
const itemContextMenuItems: ComputedRef<IContextMenuItem[]> = computed(() => [
  {
    name: 'modify',
    label: tGlobal('modify'),
    tooltip: t('categoryList.modifyCategory'),
    onClick: onModifyCategory
  }
])
```
