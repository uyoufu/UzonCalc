/** Own fixed report-row commands and expose their context-menu presentation. */

import {
  ExecutionSourceType,
  PublishState,
  ReportOriginType,
  ReportSyncState,
  type CalcReport,
  type CalcReportCategory
} from 'src/api/calc/types'
import {
  copyCalcReport,
  deleteCalcReport,
  exportReportArchive,
  getCalcReport,
  setCalcReportFavorite,
  updateCalcReport
} from 'src/api/calc/reports'
import { listReportCategories } from 'src/api/calc/categories'
import { listVersions, publishVersion } from 'src/api/calc/versions'
import { showCalcReportInExplorer } from 'src/api/desktop'
import { synchronizeReport } from 'src/api/calc/shares'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import type {
  deleteRowByIdType,
  refreshTableType,
  updateExistOneType
} from 'src/compositions/qTableUtils'
import type { IQTablePagination } from 'src/compositions/types'
import { t } from 'src/i18n/helpers'
import { useSystemInfo } from 'src/stores/system'
import { confirmOperation, notifySuccess, notifyUntil } from 'src/utils/dialog'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { LowCodeFieldType } from 'src/components/lowCode/types'
import { useShareManagerDialog } from '../../shared/useShareManagerDialog'
import {
  ReportDialogMode,
  useCalcReportListDialogs
} from '../compositions/useCalcReportListDialogs'
import { usePublishVersionDialog } from '../compositions/usePublishVersionDialog'
import { FixedReportCategoryFilter, type ReportCategorySelection } from './reportCategoryFilter'

export interface ReportContextMenuOptions {
  categories: Ref<CalcReportCategory[]>
  selectedCategoryOid: Ref<ReportCategorySelection>
  filter: Ref<string>
  pagination: Ref<IQTablePagination>
  refreshTable: refreshTableType
  updateReportRow: updateExistOneType<CalcReport>
  deleteReportRow: deleteRowByIdType
}

/**
 * Create report-row commands and their context-menu items.
 *
 * @param options - Reactive list state and the minimum table mutation capabilities.
 * @returns Menu items plus commands reused by visible row controls.
 * @throws Propagates router, API, dialog, clipboard, and desktop integration errors.
 */
export function useReportContextMenu(options: ReportContextMenuOptions) {
  const router = useRouter()
  const systemInfo = useSystemInfo()
  const { openReportDialog } = useCalcReportListDialogs()
  const { openPublishVersionDialog } = usePublishVersionDialog()
  const { openShareManagerDialog } = useShareManagerDialog()
  const categoryOptions = computed(() =>
    options.categories.value.map((category) => ({
      label: category.name,
      value: category.categoryOid
    }))
  )

  /**
   * Refresh category metadata after a report mutation changes derived counts.
   *
   * @returns A promise that resolves after categories are replaced.
   * @throws Propagates category API errors.
   */
  async function refreshCategories(): Promise<void> {
    const response = await listReportCategories()
    options.categories.value = response.data || []
  }

  /**
   * Open the selected report workspace.
   *
   * @param report - Report selected by a row control.
   * @returns A promise that resolves after navigation.
   * @throws Propagates router navigation errors.
   */
  async function onOpenReport(report: CalcReport): Promise<void> {
    if (!report.canEdit) {
      await onRunReport(report)
      return
    }
    await router.push({
      path: `/calc-report/${report.reportOid}/workspace`,
      query: { tagName: `${report.name} · ${t('calcWorkspace.workspace')}` }
    })
  }

  /**
   * Open workspace execution for the selected report.
   *
   * @param report - Report selected by the menu.
   * @returns A promise that resolves after navigation.
   * @throws Propagates router navigation errors.
   */
  async function onRunReport(report: CalcReport): Promise<void> {
    if (report.syncState === ReportSyncState.UpdateAvailable) {
      const shouldUpdate = await confirmOperation(t('calcWorkspace.syncUpdateAvailable'), t('calcWorkspace.syncBeforeRun'))
      if (shouldUpdate) {
        await synchronizeReport(report.reportOid)
        options.updateReportRow((await getCalcReport(report.reportOid)).data, 'reportOid')
      }
    }
    await router.push({
      path: `/calc-report/${report.reportOid}/run`,
      query: {
        source: report.originType === ReportOriginType.ShareSync ? ExecutionSourceType.Latest : ExecutionSourceType.Workspace,
        tagName: `${report.name} · ${t('calcWorkspace.run')}`
      }
    })
  }

  /**
   * Open immutable versions for the selected report.
   *
   * @param report - Report selected by the menu.
   * @returns A promise that resolves after navigation.
   * @throws Propagates router navigation errors.
   */
  async function onOpenVersions(report: CalcReport): Promise<void> {
    await router.push({
      path: `/calc-report/${report.reportOid}/versions`,
      query: { tagName: `${report.name} · ${t('calcWorkspace.versions')}` }
    })
  }

  /**
   * Publish a confirmed version and patch the authoritative report row.
   *
   * @param report - Report whose workspace will be published.
   * @returns A promise that resolves after publication or dialog cancellation.
   * @throws Propagates version, report, and dialog errors.
   */
  async function onPublishVersion(report: CalcReport): Promise<void> {
    const versions = (await listVersions(report.reportOid)).data || []
    const input = await openPublishVersionDialog(versions)
    if (!input) return

    await publishVersion(report.reportOid, input.versionName, input.description || null)
    options.updateReportRow((await getCalcReport(report.reportOid)).data, 'reportOid')
    notifySuccess(t('calcWorkspace.versionPublished'))
  }

  /**
   * Persist report metadata editing or copying and synchronize list state.
   *
   * @param report - Source report for the operation.
   * @param mode - Editing or copy mode selected by the menu item.
   * @returns A promise that resolves after persistence or dialog cancellation.
   * @throws Propagates report, category, and dialog errors.
   */
  async function onOpenReportDialog(report: CalcReport, mode: ReportDialogMode): Promise<void> {
    const input = await openReportDialog(report, mode, categoryOptions.value)
    if (!input) return

    const updatedReport =
      mode === ReportDialogMode.Copy
        ? (await copyCalcReport(report.reportOid, input)).data
        : (await updateCalcReport(report.reportOid, input)).data
    await refreshCategories()
    const hasCategoryMismatch = Boolean(
      options.selectedCategoryOid.value &&
      updatedReport.categoryOid !== options.selectedCategoryOid.value
    )
    if (mode === ReportDialogMode.Copy || options.filter.value || hasCategoryMismatch) {
      options.pagination.value.page = 1
      options.refreshTable()
      return
    }
    options.updateReportRow(updatedReport, 'reportOid')
  }

  /**
   * Toggle favorite state and patch or remove the affected row.
   *
   * @param report - Report whose favorite state will change.
   * @returns A promise that resolves after the row is synchronized.
   * @throws Propagates favorite API errors.
   */
  async function onToggleFavorite(report: CalcReport): Promise<void> {
    const response = await setCalcReportFavorite(report.reportOid, !report.isFavorite)
    if (
      options.selectedCategoryOid.value === FixedReportCategoryFilter.Favorites &&
      !response.data.isFavorite
    ) {
      options.deleteReportRow(report.reportOid, 'reportOid')
      return
    }
    options.updateReportRow(response.data, 'reportOid')
  }

  /**
   * Open share-link management for the selected report.
   *
   * @param report - Report whose links will be managed.
   * @returns A promise that resolves after the dialog closes.
   * @throws Propagates dialog errors.
   */
  async function onShareReport(report: CalcReport): Promise<void> {
    await openShareManagerDialog(report.reportOid, report.name)
  }

  /**
   * Reveal the selected report in the desktop file explorer.
   *
   * @param report - Report to reveal.
   * @returns A promise that resolves after the desktop command completes.
   * @throws Propagates desktop integration errors.
   */
  async function onShowReportInExplorer(report: CalcReport): Promise<void> {
    await showCalcReportInExplorer(report.reportOid)
  }

  /** Download the report's latest published portable closure. */
  async function onExportReport(report: CalcReport): Promise<void> {
    const permissionResult = await showDialog<{ canEdit: boolean; canShare: boolean }>({
      title: t('calcWorkspace.exportPermissions'),
      oneColumn: true,
      fields: [
        { name: 'canEdit', label: t('calcWorkspace.canEdit'), type: LowCodeFieldType.boolean, value: false },
        { name: 'canShare', label: t('calcWorkspace.canShare'), type: LowCodeFieldType.boolean, value: false }
      ]
    })
    if (!permissionResult.ok) return
    const response = await notifyUntil(
      async () => await exportReportArchive(report.reportOid, permissionResult.data.canEdit, permissionResult.data.canShare),
      t('calcWorkspace.exportingArchive')
    )
    if (!response) return
    downloadArchiveBlob(response.data, `${report.name}.png`)
  }

  /**
   * Delete a confirmed report and synchronize row and category state.
   *
   * @param report - Report selected for deletion.
   * @returns A promise that resolves after deletion or confirmation cancellation.
   * @throws Propagates confirmation, report, and category errors.
   */
  async function onDeleteReport(report: CalcReport): Promise<void> {
    if (!(await confirmOperation(t('global.deleteConfirmation'), report.name))) return
    await deleteCalcReport(report.reportOid)
    options.deleteReportRow(report.reportOid, 'reportOid')
    await refreshCategories()
  }

  const items: IContextMenuItem<CalcReport>[] = [
    {
      name: 'open',
      label: t('calcWorkspace.openWorkspace'),
      icon: 'code',
      color: 'grey-9',
      vif: (report) => report.canEdit,
      onClick: onOpenReport
    },
    {
      name: 'run',
      label: t('calcWorkspace.run'),
      icon: 'play_arrow',
      color: 'positive',
      onClick: onRunReport
    },
    {
      name: 'publish',
      label: t('calcWorkspace.publishVersion'),
      icon: 'publish',
      color: 'primary',
      vif: (report) =>
        report.canEdit && ([PublishState.Unpublished, PublishState.UnpublishedChanges] as PublishState[]).includes(
          report.publishState
        ),
      onClick: onPublishVersion
    },
    {
      name: 'versions',
      label: t('calcWorkspace.versions'),
      icon: 'history',
      color: 'grey-9',
      onClick: onOpenVersions
    },
    {
      name: 'edit',
      label: t('calcWorkspace.editMetadata'),
      icon: 'edit',
      color: 'grey-9',
      onClick: (report) => onOpenReportDialog(report, ReportDialogMode.Edit)
    },
    {
      name: 'favorite',
      label: t('calcWorkspace.toggleFavorite'),
      icon: 'star',
      color: 'warning',
      onClick: onToggleFavorite
    },
    {
      name: 'copy',
      label: t('calcWorkspace.copyReport'),
      icon: 'content_copy',
      color: 'grey-9',
      onClick: (report) => onOpenReportDialog(report, ReportDialogMode.Copy)
    },
    {
      name: 'share',
      label: t('calcWorkspace.share'),
      icon: 'share',
      color: 'primary',
      vif: (report) => report.canShare,
      onClick: onShareReport
    },
    {
      name: 'export',
      label: t('global.export'),
      icon: 'download',
      color: 'secondary',
      vif: (report) => Boolean(report.latestVersionName),
      onClick: onExportReport
    },
    {
      name: 'explorer',
      label: t('calcWorkspace.showInExplorer'),
      icon: 'folder_open',
      color: 'grey-9',
      vif: () => systemInfo.isLocalhost,
      onClick: onShowReportInExplorer
    },
    {
      name: 'delete',
      label: t('global.delete'),
      icon: 'delete',
      color: 'negative',
      onClick: onDeleteReport
    }
  ]

  return { items, onOpenReport, onToggleFavorite }
}

/** Trigger a browser download and release its temporary object URL. */
function downloadArchiveBlob(blob: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(objectUrl)
}
