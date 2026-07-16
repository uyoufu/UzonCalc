import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { CalcReportVersion } from 'src/api/calc/types'
import type { IPopupDialogParams } from 'src/components/lowCode/types'
import { useCalcReportListDialogs } from 'src/pages/calcReport/list/compositions/useCalcReportListDialogs'
import { useSaveInstanceDialog } from 'src/pages/calcReport/workbench/execution/useSaveInstanceDialog'
import { useVersionDialogs } from 'src/pages/calcReport/workbench/version/useVersionDialogs'
import { useWorkspaceConflictDialog } from 'src/pages/calcReport/workbench/workspace/useWorkspaceConflictDialog'
import { WorkspaceConflictResolution } from 'src/pages/calcReport/workbench/workspace/workspaceConflict'

const mocks = vi.hoisted(() => ({
  showDialog: vi.fn(),
  showComponentDialog: vi.fn(),
  listInstanceCategories: vi.fn(),
  ensureDefaultInstanceCategory: vi.fn(),
  createInstance: vi.fn(),
  notifySuccess: vi.fn()
}))

vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key, tButton: (key: string) => key }))
vi.mock('src/utils/dialog', () => ({
  notifySuccess: mocks.notifySuccess
}))
vi.mock('src/components/lowCode/PopupDialog', () => ({
  showDialog: mocks.showDialog,
  showComponentDialog: mocks.showComponentDialog
}))
vi.mock('src/api/calc/categories', () => ({
  listInstanceCategories: mocks.listInstanceCategories,
  ensureDefaultInstanceCategory: mocks.ensureDefaultInstanceCategory
}))
vi.mock('src/api/calc/instances', () => ({ createInstance: mocks.createInstance }))

describe('calculation workspace dialog workflows', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('validates and submits report-category metadata inside the dialog', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    mocks.showDialog.mockImplementation(async (params: IPopupDialogParams) => {
      const nameField = params.fields.find((field) => field.name === 'name')
      expect((await nameField?.validate?.('   ', '   ', {}))?.ok).toBe(false)
      await params.onOkMain?.({ name: 'Category', description: 'Description' })
      return { ok: true, data: {} }
    })

    const { openCategoryDialog } = useCalcReportListDialogs()
    await expect(openCategoryDialog(undefined, onSubmit)).resolves.toBe(true)
    expect(onSubmit).toHaveBeenCalledWith({ name: 'Category', description: 'Description' })
  })

  it('keeps semantic-version validation and submits a new version', async () => {
    const versions = [{ versionName: '1.0.0' }] as CalcReportVersion[]
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    mocks.showDialog.mockImplementation(async (params: IPopupDialogParams) => {
      const versionField = params.fields.find((field) => field.name === 'versionName')
      expect(versionField?.hint).toBe('MAJOR.MINOR.PATCH')
      expect((await versionField?.validate?.('1.0.0', '1.0.0', {}))?.ok).toBe(false)
      expect((await versionField?.validate?.('1.0.1', '1.0.1', {}))?.ok).toBe(true)
      await params.onOkMain?.({ versionName: '1.0.1', description: '' })
      return { ok: true, data: {} }
    })

    const { openPublishDialog } = useVersionDialogs()
    await expect(openPublishDialog(versions, onSubmit)).resolves.toBe(true)
    expect(onSubmit).toHaveBeenCalledWith({ versionName: '1.0.1', description: '' })
  })

  it('creates a default category before saving an instance when none exist', async () => {
    mocks.listInstanceCategories.mockResolvedValue({ data: [] })
    mocks.ensureDefaultInstanceCategory.mockResolvedValue({
      data: { categoryOid: 'category-1', name: 'Default' }
    })
    mocks.createInstance.mockResolvedValue({ data: {} })
    mocks.showDialog.mockImplementation(async (params: IPopupDialogParams) => {
      await params.onOkMain?.({ categoryOid: 'category-1', name: 'Instance', description: '' })
      return { ok: true, data: {} }
    })

    const { openSaveInstanceDialog } = useSaveInstanceDialog()
    await expect(openSaveInstanceDialog('execution-1', 'Instance')).resolves.toBe(true)
    expect(mocks.ensureDefaultInstanceCategory).toHaveBeenCalledOnce()
    expect(mocks.createInstance).toHaveBeenCalledWith({
      executionId: 'execution-1',
      categoryOid: 'category-1',
      name: 'Instance',
      description: ''
    })
    expect(mocks.notifySuccess).toHaveBeenCalledOnce()
  })

  it('returns the selected workspace-conflict action and null after cancellation', async () => {
    mocks.showComponentDialog
      .mockResolvedValueOnce({ ok: true, data: WorkspaceConflictResolution.DiscardAndReload })
      .mockResolvedValueOnce({ ok: false, data: {} })

    const { openWorkspaceConflictDialog } = useWorkspaceConflictDialog()
    await expect(openWorkspaceConflictDialog()).resolves.toBe(
      WorkspaceConflictResolution.DiscardAndReload
    )
    await expect(openWorkspaceConflictDialog()).resolves.toBeNull()
  })
})

