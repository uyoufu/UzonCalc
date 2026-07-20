import { defineComponent, onMounted, ref, watch } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useQTable } from 'src/compositions/qTableUtils'

interface TestRow {
  oid: string
  name: string
}

describe('useQTable', () => {
  beforeEach(() => {
    vi.stubGlobal('ref', ref)
    vi.stubGlobal('watch', watch)
    vi.stubGlobal('onMounted', onMounted)
  })

  it('caches counts across pages and invalidates them on refresh', async () => {
    const getRowsNumberCount = vi.fn().mockResolvedValue(1)
    const onRequest = vi.fn().mockResolvedValue([{ oid: 'row-1', name: 'First' }])
    let table: ReturnType<typeof useQTable<TestRow>> | undefined
    const TestComponent = defineComponent({
      setup() {
        table = useQTable<TestRow>({
          rowsPerPage: 20,
          filterFactor: (filter) => ({ filter, categoryOid: 'category-1' }),
          getRowsNumberCount,
          onRequest
        })
        return {}
      },
      template: '<div />'
    })

    mount(TestComponent)
    await flushPromises()
    expect(getRowsNumberCount).toHaveBeenCalledTimes(1)
    expect(onRequest).toHaveBeenCalledTimes(1)
    expect(table?.pagination.value.rowsPerPage).toBe(20)

    await table?.onTableRequest({
      pagination: { ...table.pagination.value, page: 2 },
      filter: table.filter.value
    })
    expect(getRowsNumberCount).toHaveBeenCalledTimes(1)
    expect(onRequest).toHaveBeenCalledTimes(2)

    table?.refreshTable()
    await flushPromises()
    expect(getRowsNumberCount).toHaveBeenCalledTimes(2)
  })

  it('updates local rows with string identities', () => {
    let table: ReturnType<typeof useQTable<TestRow>> | undefined
    const TestComponent = defineComponent({
      setup() {
        table = useQTable<TestRow>({ preventRequestWhenMounted: true })
        return {}
      },
      template: '<div />'
    })

    mount(TestComponent)
    table?.addNewRow({ oid: 'row-1', name: 'First' }, 'oid')
    expect(table?.pagination.value.rowsNumber).toBe(1)
    expect(table?.updateExistOne({ oid: 'row-1', name: 'Updated' }, 'oid')).toBe(true)
    expect(table?.rows.value[0]?.name).toBe('Updated')

    table?.deleteRowById('row-1', 'oid')
    expect(table?.rows.value).toEqual([])
    expect(table?.pagination.value.rowsNumber).toBe(0)
  })
})
