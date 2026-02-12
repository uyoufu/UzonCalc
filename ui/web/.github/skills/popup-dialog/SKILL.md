---
name: popup-dialog
description: popup dialog for creating or modifying items
---

# Popup Dialog Skill

This skill provides a reusable popup dialog component that can be used for creating or modifying items.

# Implementation Steps

1. Build a `IPopupDialogParams` object to specify the dialog's title, fields, and other options.
2. Call `showDialog` with the `IPopupDialogParams` object to display the dialog and get the result.


# Example Usage

``` ts
import type { ILowCodeField, IPopupDialogParams } from 'src/components/lowCode/types'
import type { LowCodeFieldType } from 'src/components/lowCode/types'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { confirmOperation, notifySuccess } from 'src/utils/dialog'

function buildCategoryFields(category?: ICategoryInfo) {
  const fields: ILowCodeField[] = [
    {
      name: 'name',
      label: t('categoryList.field_name'),
      value: category ? category.name : '',
      type: LowCodeFieldType.text,
      required: true,
      validate: (value: string) => {
        // 必须仅包含字母、数字、下划线且不能以数字开头
        const valid = /^[A-Za-z_][A-Za-z0-9_]*$/.test(value)
        if (!valid) {
          return {
            ok: false,
            message: t('categoryList.onlyLettersNumbersUnderscoresAndCannotStartWithNumber')
          }
        }
        return { ok: true }
      }
    },
    {
      name: 'description',
      label: t('categoryList.field_description'),
      value: category ? category.description || '' : '',
      type: LowCodeFieldType.textarea
    }
  ]

  return fields
}

// 新增分类
async function onCreateCategory() {
  const popupParams: IPopupDialogParams = {
    title: t('categoryList.newCategory'),
    fields: buildCategoryFields(),
    oneColumn: true
  }
  const result = await showDialog<ICategoryInfo>(popupParams)
  if (!result.ok) return

  // 添加默认的 icon
  const newCategory = await props.createCategory(result.data)

  categoryItems.value.push({
    ...newCategory,
    active: false
  })

  // 设置新组为当前组
  activeCategory(categoryItems.value[categoryItems.value.length - 1] as ICategoryInfo)

  // 新增组
  notifySuccess(t('categoryList.newCategorySuccess'))
}

async function onModifyCategory(categoryDetails: Record<string, any>) {
  const categoryInfo = categoryDetails as ICategoryInfo
  const popupParams: IPopupDialogParams = {
    title: t('categoryList.modifyCategory'),
    fields: buildCategoryFields(categoryInfo),
    oneColumn: true
  }
  const result = await showDialog<ICategoryInfo>(popupParams)
  if (!result.ok) return

  // 指定 id 和 oid
  result.data.id = categoryInfo.id
  result.data.oid = categoryInfo.oid

  await props.updateCategory(result.data)

  // 更新数据
  categoryInfo.name = result.data.name
  categoryInfo.description = result.data.description

  // 修改分类成功
  notifySuccess(t('categoryList.modifyCategorySuccess'))
}
```
