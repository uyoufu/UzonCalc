import { describe, expect, it, vi } from 'vitest'
import { useReportContextMenu } from 'src/pages/calcReport/list/components/useReportContextMenu'

vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key }))

describe('report context menu', () => {
  it('exposes share and hides latest execution for unpublished reports', () => {
    const callback = vi.fn()
    const { items } = useReportContextMenu({ open: callback, run: callback, versions: callback, edit: callback, copy: callback, favorite: callback, share: callback, showInExplorer: callback, remove: callback, isDesktop: () => false })
    const report = { latestVersionName: null } as never
    expect(items.some((item) => item.name === 'open')).toBe(true)
    expect(items.some((item) => item.name === 'versions')).toBe(true)
    expect(items.some((item) => item.name === 'share')).toBe(true)
    expect(items.find((item) => item.name === 'run')?.vif?.(report)).toBe(false)
    expect(items.find((item) => item.name === 'run')?.vif?.({ latestVersionName: 'v1.0.0' } as never)).toBe(true)
    expect(items.find((item) => item.name === 'explorer')?.vif?.(report)).toBe(false)
  })
})
