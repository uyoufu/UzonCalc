import { beforeEach, describe, expect, it, vi } from 'vitest'
import { computed, ref } from 'vue'
import { useReportContextMenu } from 'src/pages/calcReport/list/components/useReportContextMenu'
import {
  BuildStatus,
  PublishState,
  type CalcReport,
  type CalcReportCategory
} from 'src/api/calc/types'
import { FixedReportCategoryFilter } from 'src/pages/calcReport/list/components/reportCategoryFilter'

const mocks = vi.hoisted(() => ({
  routerPush: vi.fn(),
  listReportCategories: vi.fn(),
  copyCalcReport: vi.fn(),
  deleteCalcReport: vi.fn(),
  exportReportArchive: vi.fn(),
  getCalcReport: vi.fn(),
  setCalcReportFavorite: vi.fn(),
  updateCalcReport: vi.fn(),
  listVersions: vi.fn(),
  publishVersion: vi.fn(),
  showCalcReportInExplorer: vi.fn(),
  confirmOperation: vi.fn(),
  notifySuccess: vi.fn(),
  notifyUntil: vi.fn(),
  showDialog: vi.fn(),
  openReportDialog: vi.fn(),
  openPublishVersionDialog: vi.fn(),
  openShareManagerDialog: vi.fn(),
  systemInfo: { isLocalhost: false }
}))

vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key }))
vi.mock('src/stores/system', () => ({ useSystemInfo: () => mocks.systemInfo }))
vi.mock('src/api/calc/categories', () => ({
  listReportCategories: mocks.listReportCategories
}))
vi.mock('src/api/calc/reports', () => ({
  copyCalcReport: mocks.copyCalcReport,
  deleteCalcReport: mocks.deleteCalcReport,
  exportReportArchive: mocks.exportReportArchive,
  getCalcReport: mocks.getCalcReport,
  setCalcReportFavorite: mocks.setCalcReportFavorite,
  updateCalcReport: mocks.updateCalcReport
}))
vi.mock('src/api/calc/versions', () => ({
  listVersions: mocks.listVersions,
  publishVersion: mocks.publishVersion
}))
vi.mock('src/api/desktop', () => ({
  showCalcReportInExplorer: mocks.showCalcReportInExplorer
}))
vi.mock('src/utils/dialog', () => ({
  confirmOperation: mocks.confirmOperation,
  notifySuccess: mocks.notifySuccess,
  notifyUntil: mocks.notifyUntil
}))
vi.mock('src/components/lowCode/PopupDialog', () => ({ showDialog: mocks.showDialog }))
vi.mock('src/pages/calcReport/list/compositions/useCalcReportListDialogs', () => ({
  ReportDialogMode: { Edit: 'edit', Copy: 'copy' },
  useCalcReportListDialogs: () => ({ openReportDialog: mocks.openReportDialog })
}))
vi.mock('src/pages/calcReport/list/compositions/usePublishVersionDialog', () => ({
  usePublishVersionDialog: () => ({
    openPublishVersionDialog: mocks.openPublishVersionDialog
  })
}))
vi.mock('src/pages/calcReport/shared/useShareManagerDialog', () => ({
  useShareManagerDialog: () => ({ openShareManagerDialog: mocks.openShareManagerDialog })
}))

const report = {
  reportOid: 'report-1',
  categoryOid: 'category-1',
  name: 'Report',
  description: '',
  publishState: PublishState.Unpublished,
  buildStatus: BuildStatus.NotRequested,
  isFavorite: false,
  latestVersionName: '1.0.0',
  canEdit: true,
  canShare: true
} as CalcReport

/**
 * Create isolated reactive list state and table capabilities for one test.
 *
 * @returns A report-menu instance with observable state capabilities.
 * @throws Propagates composable initialization errors.
 */
function createMenu() {
  const categories = ref<CalcReportCategory[]>([
    { categoryOid: 'category-1', name: 'Category 1' } as CalcReportCategory
  ])
  const selectedCategoryOid = ref<string | null>(null)
  const filter = ref('')
  const pagination = ref({
    sortBy: 'updatedAt',
    descending: true,
    page: 2,
    rowsPerPage: 20,
    rowsNumber: 1
  })
  const refreshTable = vi.fn()
  const updateReportRow = vi.fn(() => true)
  const deleteReportRow = vi.fn()
  const menu = useReportContextMenu({
    categories,
    selectedCategoryOid,
    filter,
    pagination,
    refreshTable,
    updateReportRow,
    deleteReportRow
  })
  return {
    ...menu,
    categories,
    selectedCategoryOid,
    filter,
    pagination,
    refreshTable,
    updateReportRow,
    deleteReportRow
  }
}

describe('report context menu', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('computed', computed)
    vi.stubGlobal('useRouter', () => ({ push: mocks.routerPush }))
    mocks.systemInfo.isLocalhost = false
    mocks.listReportCategories.mockResolvedValue({ data: [] })
    mocks.notifyUntil.mockImplementation(async (runFunc) => await runFunc())
  })

  it('exposes fixed actions with publication and desktop visibility rules', () => {
    const { items } = createMenu()
    expect(items.map((item) => item.name)).toEqual([
      'open',
      'run',
      'publish',
      'versions',
      'edit',
      'favorite',
      'copy',
      'share',
      'export',
      'explorer',
      'delete'
    ])
    expect(items.find((item) => item.name === 'publish')?.vif?.(report)).toBe(true)
    expect(items.find((item) => item.name === 'publish')?.vif?.({
      ...report,
      publishState: PublishState.Published
    })).toBe(false)
    expect(items.find((item) => item.name === 'explorer')?.vif?.(report)).toBe(false)
    mocks.systemInfo.isLocalhost = true
    expect(items.find((item) => item.name === 'explorer')?.vif?.(report)).toBe(true)
  })

  it('owns report navigation, sharing, and desktop reveal behavior', async () => {
    const { items, onOpenReport } = createMenu()
    await onOpenReport(report)
    await items.find((item) => item.name === 'run')?.onClick(report)
    await items.find((item) => item.name === 'versions')?.onClick(report)
    await items.find((item) => item.name === 'share')?.onClick(report)
    await items.find((item) => item.name === 'explorer')?.onClick(report)

    expect(mocks.routerPush).toHaveBeenNthCalledWith(1, {
      path: '/calc-report/report-1/workspace',
      query: { tagName: 'Report · calcWorkspace.workspace' }
    })
    expect(mocks.routerPush).toHaveBeenNthCalledWith(2, {
      path: '/calc-report/report-1/run',
      query: {
        source: 'workspace',
        tagName: 'Report · calcWorkspace.run'
      }
    })
    expect(mocks.routerPush).toHaveBeenNthCalledWith(3, {
      path: '/calc-report/report-1/versions',
      query: { tagName: 'Report · calcWorkspace.versions' }
    })
    expect(mocks.openShareManagerDialog).toHaveBeenCalledWith('report-1', 'Report')
    expect(mocks.showCalcReportInExplorer).toHaveBeenCalledWith('report-1')
  })

  it('collects archive permissions before exporting a published report', async () => {
    const { items } = createMenu()
    const archive = new Blob(['archive'], { type: 'image/png' })
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    vi.stubGlobal('URL', {
      createObjectURL: vi.fn(() => 'blob:archive'),
      revokeObjectURL: vi.fn()
    })
    mocks.showDialog.mockResolvedValue({ ok: true, data: { canEdit: true, canShare: false } })
    mocks.exportReportArchive.mockResolvedValue({ data: archive })

    await items.find((item) => item.name === 'export')?.onClick(report)

    expect(mocks.exportReportArchive).toHaveBeenCalledWith('report-1', true, false)
    expect(clickSpy).toHaveBeenCalledOnce()
    clickSpy.mockRestore()
    vi.unstubAllGlobals()
  })

  it('publishes and edits rows while preserving incremental and refresh semantics', async () => {
    const menu = createMenu()
    const publishedReport = { ...report, publishState: PublishState.Published }
    const editedReport = { ...report, name: 'Edited report' }
    mocks.listVersions.mockResolvedValue({ data: [{ versionName: '1.0.0' }] })
    mocks.openPublishVersionDialog.mockResolvedValue({
      versionName: '1.0.1',
      description: 'Release'
    })
    mocks.getCalcReport.mockResolvedValue({ data: publishedReport })
    mocks.openReportDialog.mockResolvedValue({
      categoryOid: 'category-1',
      name: 'Edited report',
      description: ''
    })
    mocks.updateCalcReport.mockResolvedValue({ data: editedReport })

    await menu.items.find((item) => item.name === 'publish')?.onClick(report)
    await menu.items.find((item) => item.name === 'edit')?.onClick(report)

    expect(mocks.publishVersion).toHaveBeenCalledWith('report-1', '1.0.1', 'Release')
    expect(menu.updateReportRow).toHaveBeenNthCalledWith(1, publishedReport, 'reportOid')
    expect(menu.updateReportRow).toHaveBeenNthCalledWith(2, editedReport, 'reportOid')
    expect(menu.refreshTable).not.toHaveBeenCalled()

    menu.selectedCategoryOid.value = 'category-2'
    await menu.items.find((item) => item.name === 'edit')?.onClick(report)
    expect(menu.pagination.value.page).toBe(1)
    expect(menu.refreshTable).toHaveBeenCalledOnce()

    mocks.copyCalcReport.mockResolvedValue({ data: { ...report, reportOid: 'report-2' } })
    await menu.items.find((item) => item.name === 'copy')?.onClick(report)
    expect(menu.pagination.value.page).toBe(1)
    expect(menu.refreshTable).toHaveBeenCalledTimes(2)
  })

  it('removes unfavorited and deleted rows only after confirmed API changes', async () => {
    const menu = createMenu()
    mocks.setCalcReportFavorite.mockResolvedValueOnce({
      data: { ...report, isFavorite: true }
    })
    await menu.onToggleFavorite(report)
    expect(menu.updateReportRow).toHaveBeenCalledWith(
      { ...report, isFavorite: true },
      'reportOid'
    )

    menu.selectedCategoryOid.value = FixedReportCategoryFilter.Favorites
    mocks.setCalcReportFavorite.mockResolvedValueOnce({
      data: { ...report, isFavorite: false }
    })
    mocks.confirmOperation.mockResolvedValueOnce(false).mockResolvedValueOnce(true)

    await menu.onToggleFavorite({ ...report, isFavorite: true })
    await menu.items.find((item) => item.name === 'delete')?.onClick(report)
    expect(mocks.deleteCalcReport).not.toHaveBeenCalled()

    await menu.items.find((item) => item.name === 'delete')?.onClick(report)
    expect(menu.deleteReportRow).toHaveBeenNthCalledWith(1, 'report-1', 'reportOid')
    expect(menu.deleteReportRow).toHaveBeenNthCalledWith(2, 'report-1', 'reportOid')
    expect(mocks.deleteCalcReport).toHaveBeenCalledWith('report-1')
    expect(mocks.listReportCategories).toHaveBeenCalledOnce()
  })
})
