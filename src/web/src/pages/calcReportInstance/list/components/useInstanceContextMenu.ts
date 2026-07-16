/** Build saved-instance row actions separately from table rendering. */

import type { CalcInstance } from 'src/api/calc/types'
import type { IContextMenuItem } from 'src/components/contextMenu/types'
import { t } from 'src/i18n/helpers'

/** Create context-menu items for saved calculation instances. */
export function useInstanceContextMenu(actions: { open: (value: CalcInstance) => void | Promise<void>; edit: (value: CalcInstance) => void | Promise<void>; remove: (value: CalcInstance) => void | Promise<void> }) {
  return { items: [
    { name: 'open', label: t('global.view'), icon: 'visibility', color: 'grey-9', onClick: actions.open },
    { name: 'edit', label: t('global.edit'), icon: 'edit', color: 'grey-9', onClick: actions.edit },
    { name: 'delete', label: t('global.delete'), icon: 'delete', color: 'negative', onClick: actions.remove }
  ] as IContextMenuItem<CalcInstance>[] }
}
