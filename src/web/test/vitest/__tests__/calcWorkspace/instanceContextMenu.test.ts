import { beforeEach, describe, expect, it, vi } from 'vitest'
import { computed, ref } from 'vue'
import type { CalcInstance, CalcInstanceCategory } from 'src/api/calc/types'
import { useInstanceContextMenu } from 'src/pages/calcReportInstance/list/components/useInstanceContextMenu'

const mocks = vi.hoisted(() => ({
  routerPush: vi.fn(),
  listInstanceCategories: vi.fn(),
  deleteInstance: vi.fn(),
  updateInstance: vi.fn(),
  confirmOperation: vi.fn(),
  openInstanceDialog: vi.fn()
}))

vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key }))
vi.mock('src/api/calc/categories', () => ({
  listInstanceCategories: mocks.listInstanceCategories
}))
vi.mock('src/api/calc/instances', () => ({
  deleteInstance: mocks.deleteInstance,
  updateInstance: mocks.updateInstance
}))
vi.mock('src/utils/dialog', () => ({ confirmOperation: mocks.confirmOperation }))
vi.mock('src/pages/calcReportInstance/list/compositions/useInstanceListDialogs', () => ({
  useInstanceListDialogs: () => ({ openInstanceDialog: mocks.openInstanceDialog })
}))

const instance = {
  instanceOid: 'instance-1',
  categoryOid: 'category-1',
  name: 'Saved calculation',
  description: '',
  revision: 2
} as CalcInstance

/**
 * Create isolated saved-instance menu dependencies for one test.
 *
 * @returns An instance-menu object with observable state capabilities.
 * @throws Propagates composable initialization errors.
 */
function createMenu() {
  const categories = ref<CalcInstanceCategory[]>([
    { categoryOid: 'category-1', name: 'Category 1' } as CalcInstanceCategory
  ])
  const updateInstanceRow = vi.fn(() => true)
  const deleteInstanceRow = vi.fn()
  const menu = useInstanceContextMenu({
    categories,
    updateInstanceRow,
    deleteInstanceRow
  })
  return { ...menu, categories, updateInstanceRow, deleteInstanceRow }
}

describe('instance context menu', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('computed', computed)
    vi.stubGlobal('useRouter', () => ({ push: mocks.routerPush }))
    mocks.listInstanceCategories.mockResolvedValue({ data: [] })
  })

  it('owns detail navigation and optimistic metadata editing', async () => {
    const menu = createMenu()
    const updatedInstance = { ...instance, name: 'Updated calculation', revision: 3 }
    mocks.openInstanceDialog.mockResolvedValue({
      categoryOid: 'category-1',
      name: 'Updated calculation',
      description: ''
    })
    mocks.updateInstance.mockResolvedValue({ data: updatedInstance })

    await menu.onOpenInstance(instance)
    await menu.items.find((item) => item.name === 'edit')?.onClick(instance)

    expect(mocks.routerPush).toHaveBeenCalledWith('/calc-report-instance/instance-1')
    expect(mocks.updateInstance).toHaveBeenCalledWith('instance-1', {
      revision: 2,
      categoryOid: 'category-1',
      name: 'Updated calculation',
      description: ''
    })
    expect(menu.updateInstanceRow).toHaveBeenCalledWith(updatedInstance, 'instanceOid')
  })

  it('deletes only after confirmation and refreshes derived category counts', async () => {
    const menu = createMenu()
    mocks.confirmOperation.mockResolvedValueOnce(false).mockResolvedValueOnce(true)

    await menu.items.find((item) => item.name === 'delete')?.onClick(instance)
    expect(mocks.deleteInstance).not.toHaveBeenCalled()

    await menu.items.find((item) => item.name === 'delete')?.onClick(instance)
    expect(mocks.deleteInstance).toHaveBeenCalledWith('instance-1')
    expect(menu.deleteInstanceRow).toHaveBeenCalledWith('instance-1', 'instanceOid')
    expect(mocks.listInstanceCategories).toHaveBeenCalledOnce()
    expect(menu.categories.value).toEqual([])
  })
})
