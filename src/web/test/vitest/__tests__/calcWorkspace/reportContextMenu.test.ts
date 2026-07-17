import { describe, expect, it, vi } from 'vitest'
import { useReportContextMenu } from 'src/pages/calcReport/list/components/useReportContextMenu'
import { PublishState, type CalcReport } from 'src/api/calc/types'

vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key }))

describe('report context menu', () => {
  it('exposes workspace execution and publication only for pending workspace states', () => {
    const callback = vi.fn()
    const { items } = useReportContextMenu({ open: callback, run: callback, publish: callback, versions: callback, edit: callback, copy: callback, favorite: callback, share: callback, showInExplorer: callback, remove: callback, isDesktop: () => false })
    const report = { publishState: PublishState.Unpublished } as CalcReport
    expect(items.some((item) => item.name === 'open')).toBe(true)
    expect(items.some((item) => item.name === 'versions')).toBe(true)
    expect(items.some((item) => item.name === 'share')).toBe(true)
    expect(items.find((item) => item.name === 'run')?.vif).toBeUndefined()
    expect(items.find((item) => item.name === 'publish')?.vif?.(report)).toBe(true)
    expect(items.find((item) => item.name === 'publish')?.vif?.({ publishState: PublishState.UnpublishedChanges } as CalcReport)).toBe(true)
    expect(items.find((item) => item.name === 'publish')?.vif?.({ publishState: PublishState.Published } as CalcReport)).toBe(false)
    expect(items.find((item) => item.name === 'publish')?.vif?.({ publishState: PublishState.WorkspaceVersionMismatch } as CalcReport)).toBe(false)
    expect(items.find((item) => item.name === 'explorer')?.vif?.(report)).toBe(false)
  })
})
