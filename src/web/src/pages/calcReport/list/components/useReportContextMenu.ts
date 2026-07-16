/** Build report-row context actions without coupling them to table rendering. */

import type { CalcReport } from 'src/api/calc/types'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import { t } from 'src/i18n/helpers'

export interface ReportContextActions {
  open: (report: CalcReport) => void | Promise<void>
  run: (report: CalcReport) => void | Promise<void>
  publish: (report: CalcReport) => void | Promise<void>
  versions: (report: CalcReport) => void | Promise<void>
  edit: (report: CalcReport) => void | Promise<void>
  copy: (report: CalcReport) => void | Promise<void>
  favorite: (report: CalcReport) => void | Promise<void>
  share: (report: CalcReport) => void | Promise<void>
  showInExplorer: (report: CalcReport) => void | Promise<void>
  remove: (report: CalcReport) => void | Promise<void>
  isDesktop: () => boolean
}

/** Return context-menu items for one report row. */
export function useReportContextMenu(actions: ReportContextActions) {
  const items: IContextMenuItem<CalcReport>[] = [
    { name: 'open', label: t('calcWorkspace.openWorkspace'), icon: 'code', color: 'grey-9', onClick: actions.open },
    { name: 'run', label: t('calcWorkspace.run'), icon: 'play_arrow', color: 'positive', onClick: actions.run },
    { name: 'publish', label: t('calcWorkspace.publishVersion'), icon: 'publish', color: 'primary', vif: (report) => ['unpublished', 'unpublished_changes'].includes(report.publishState), onClick: actions.publish },
    { name: 'versions', label: t('calcWorkspace.versions'), icon: 'history', color: 'grey-9', onClick: actions.versions },
    { name: 'edit', label: t('calcWorkspace.editMetadata'), icon: 'edit', color: 'grey-9', onClick: actions.edit },
    { name: 'favorite', label: t('calcWorkspace.toggleFavorite'), icon: 'star', color: 'warning', onClick: actions.favorite },
    { name: 'copy', label: t('calcWorkspace.copyReport'), icon: 'content_copy', color: 'grey-9', onClick: actions.copy },
    { name: 'share', label: t('calcWorkspace.share'), icon: 'share', color: 'primary', onClick: actions.share },
    { name: 'explorer', label: t('calcWorkspace.showInExplorer'), icon: 'folder_open', color: 'grey-9', vif: actions.isDesktop, onClick: actions.showInExplorer },
    { name: 'delete', label: t('global.delete'), icon: 'delete', color: 'negative', onClick: actions.remove }
  ]
  return { items }
}
