import { describe, expect, it, vi } from 'vitest'
import { useReportContextMenu } from 'src/pages/calcReport/list/components/useReportContextMenu'

vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key }))

describe('report context menu', () => {
  it('exposes workspace execution and publication only for pending workspace states', () => {
    const callback = vi.fn()
    const { items } = useReportContextMenu({ open: callback, run: callback, publish: callback, versions: callback, edit: callback, copy: callback, favorite: callback, share: callback, showInExplorer: callback, remove: callback, isDesktop: () => false })
    const report = { publishState: 'unpublished' } as never
    expect(items.some((item) => item.name === 'open')).toBe(true)
    expect(items.some((item) => item.name === 'versions')).toBe(true)
    expect(items.some((item) => item.name === 'share')).toBe(true)
    expect(items.find((item) => item.name === 'run')?.vif).toBeUndefined()
    expect(items.find((item) => item.name === 'publish')?.vif?.(report)).toBe(true)
    expect(items.find((item) => item.name === 'publish')?.vif?.({ publishState: 'unpublished_changes' } as never)).toBe(true)
    expect(items.find((item) => item.name === 'publish')?.vif?.({ publishState: 'published' } as never)).toBe(false)
    expect(items.find((item) => item.name === 'publish')?.vif?.({ publishState: 'workspace_version_mismatch' } as never)).toBe(false)
    expect(items.find((item) => item.name === 'explorer')?.vif?.(report)).toBe(false)
  })
})
