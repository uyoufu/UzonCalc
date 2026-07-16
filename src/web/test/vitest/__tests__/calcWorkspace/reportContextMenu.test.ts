import { describe, expect, it, vi } from 'vitest'
import { useReportContextMenu } from 'src/pages/calcReport/list/components/useReportContextMenu'

vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key }))

describe('report context menu', () => {
  it('exposes share and hides latest execution for unpublished reports', () => {
    const callback = vi.fn()
    const { items } = useReportContextMenu({ open: callback, run: callback, edit: callback, copy: callback, favorite: callback, share: callback, showInExplorer: callback, remove: callback, isDesktop: () => false })
    const report = { latestVersionName: null } as never
    expect(items.some((item) => item.name === 'share')).toBe(true)
    expect(items.find((item) => item.name === 'run')?.vif?.(report)).toBe(false)
    expect(items.find((item) => item.name === 'explorer')?.vif?.(report)).toBe(false)
  })
})
