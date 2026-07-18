import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { CalcInstance, CalcReport, CalcReportVersion } from 'src/api/calc/types'
import type { IPopupDialogParams } from 'src/components/lowCode/types'
import { useInstanceListDialogs } from 'src/pages/calcReportInstance/list/compositions/useInstanceListDialogs'
import { useCalcReportListDialogs } from 'src/pages/calcReport/list/compositions/useCalcReportListDialogs'
import { useSaveInstanceDialog } from 'src/pages/calcExecution/compositions/useSaveInstanceDialog'
import { usePublishVersionDialog } from 'src/pages/calcReport/list/compositions/usePublishVersionDialog'
import { useWorkspaceConflictDialog } from 'src/pages/calcReport/workbench/workspace/useWorkspaceConflictDialog'
import { WorkspaceConflictResolution } from 'src/pages/calcReport/workbench/workspace/workspaceConflict'

const mocks = vi.hoisted(() => ({
  showDialog: vi.fn(),
  showComponentDialog: vi.fn(),
  listInstanceCategories: vi.fn(),
  ensureDefaultInstanceCategory: vi.fn()
}))

vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key, tButton: (key: string) => key }))
vi.mock('src/components/lowCode/PopupDialog', () => ({
  showDialog: mocks.showDialog,
  showComponentDialog: mocks.showComponentDialog
}))
vi.mock('src/api/calc/categories', () => ({
  listInstanceCategories: mocks.listInstanceCategories,
  ensureDefaultInstanceCategory: mocks.ensureDefaultInstanceCategory
}))

describe('calculation workspace dialog workflows', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('validates and returns normalized report-category metadata', async () => {
    mocks.showDialog.mockImplementation(async (params: IPopupDialogParams) => {
      const nameField = params.fields.find((field) => field.name === 'name')
      expect((await nameField?.validate?.('   ', '   ', {}))?.ok).toBe(false)
      expect(params.onOkMain).toBeUndefined()
      return { ok: true, data: { name: 'Category', description: 'Description' } }
    })

    const { openCategoryDialog } = useCalcReportListDialogs()
    await expect(openCategoryDialog(undefined)).resolves.toEqual({
      name: 'Category',
      description: 'Description'
    })
  })

  it('returns report metadata without a submission callback', async () => {
    mocks.showDialog.mockResolvedValue({
      ok: true,
      data: { categoryOid: 'category-2', name: 'Updated report', description: 'Description' }
    })

    const { openReportDialog } = useCalcReportListDialogs()
    const report = {
      categoryOid: 'category-1',
      name: 'Report',
      description: ''
    } as CalcReport

    await expect(
      openReportDialog(report, 'edit', [{ label: 'Category', value: 'category-2' }])
    ).resolves.toEqual({
      categoryOid: 'category-2',
      name: 'Updated report',
      description: 'Description'
    })
    expect(mocks.showDialog.mock.calls[0]?.[0].onOkMain).toBeUndefined()
  })

  it('returns instance category and metadata after confirmation', async () => {
    mocks.showDialog
      .mockResolvedValueOnce({
        ok: true,
        data: { name: 'Instances', description: 'Saved calculations' }
      })
      .mockResolvedValueOnce({
        ok: true,
        data: { categoryOid: 'category-2', name: 'Updated instance', description: '' }
      })

    const { openCategoryDialog, openInstanceDialog } = useInstanceListDialogs()
    await expect(openCategoryDialog(undefined)).resolves.toEqual({
      name: 'Instances',
      description: 'Saved calculations'
    })
    await expect(
      openInstanceDialog(
        { categoryOid: 'category-1', name: 'Instance', description: '' } as CalcInstance,
        [{ label: 'Category', value: 'category-2' }]
      )
    ).resolves.toEqual({
      categoryOid: 'category-2',
      name: 'Updated instance',
      description: ''
    })

    expect(mocks.showDialog.mock.calls[0]?.[0].onOkMain).toBeUndefined()
    expect(mocks.showDialog.mock.calls[1]?.[0].onOkMain).toBeUndefined()
  })

  it('keeps semantic-version validation and returns publication input', async () => {
    const versions = [{ versionName: '1.0.0' }] as CalcReportVersion[]
    mocks.showDialog
      .mockImplementationOnce(async (params: IPopupDialogParams) => {
        const versionField = params.fields.find((field) => field.name === 'versionName')
        expect(versionField?.hint).toBe('MAJOR.MINOR.PATCH')
        expect((await versionField?.validate?.('1.0.0', '1.0.0', {}))?.ok).toBe(false)
        expect((await versionField?.validate?.('1.0.1', '1.0.1', {}))?.ok).toBe(true)
        expect(params.onOkMain).toBeUndefined()
        return { ok: true, data: { versionName: '1.0.1', description: '' } }
      })

    const { openPublishVersionDialog } = usePublishVersionDialog()
    await expect(openPublishVersionDialog(versions)).resolves.toEqual({
      versionName: '1.0.1',
      description: ''
    })
    expect(mocks.showDialog.mock.calls[0]?.[0].onOkMain).toBeUndefined()
  })

  it('creates a default category before returning save-instance metadata', async () => {
    mocks.listInstanceCategories.mockResolvedValue({ data: [] })
    mocks.ensureDefaultInstanceCategory.mockResolvedValue({
      data: { categoryOid: 'category-1', name: 'Default' }
    })
    mocks.showDialog.mockImplementation((params: IPopupDialogParams) => {
      expect(params.onOkMain).toBeUndefined()
      return {
        ok: true,
        data: { categoryOid: 'category-1', name: 'Instance', description: '' }
      }
    })

    const { openSaveInstanceDialog } = useSaveInstanceDialog()
    await expect(openSaveInstanceDialog('Instance')).resolves.toEqual({
      categoryOid: 'category-1',
      name: 'Instance',
      description: ''
    })
    expect(mocks.ensureDefaultInstanceCategory).toHaveBeenCalledOnce()
  })

  it('returns UZC import input without passing a submission callback', async () => {
    const archive = new File(['archive'], 'report.uzc')
    mocks.showComponentDialog.mockResolvedValue({
      ok: true,
      data: { categoryOid: 'category-1', name: 'Imported report', archive }
    })

    const { openImportDialog } = useCalcReportListDialogs()
    await expect(openImportDialog([{ label: 'Category', value: 'category-1' }])).resolves.toEqual({
      categoryOid: 'category-1',
      name: 'Imported report',
      archive
    })
    expect(mocks.showComponentDialog.mock.calls[0]?.[1]).toEqual({
      categoryOptions: [{ label: 'Category', value: 'category-1' }]
    })
  })

  it('returns null after cancellation', async () => {
    mocks.showDialog.mockResolvedValue({ ok: false, data: {} })

    const { openCategoryDialog } = useCalcReportListDialogs()
    await expect(openCategoryDialog(undefined)).resolves.toBeNull()
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
