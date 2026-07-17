import { config, flushPromises, shallowMount } from '@vue/test-utils'
import { computed, onMounted, ref } from 'vue'
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import DependencyDialog from 'src/pages/calcReport/workbench/workspace/DependencyDialog.vue'
import LowCodeForm from 'src/components/lowCode/LowCodeForm.vue'
import type { ILowCodeField } from 'src/components/lowCode/types'

const mocks = vi.hoisted(() => ({
  listCalcReports: vi.fn(),
  listVersions: vi.fn(),
  notifyError: vi.fn()
}))

vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key, tButton: (key: string) => key }))
vi.mock('src/utils/dialog', () => ({ notifyError: mocks.notifyError }))
vi.mock('src/api/calc/reports', () => ({ listCalcReports: mocks.listCalcReports }))
vi.mock('src/api/calc/versions', () => ({ listVersions: mocks.listVersions }))

describe('dependency dialog', () => {
  beforeAll(() => {
    config.global.renderStubDefaultSlot = true
    vi.stubGlobal('computed', computed)
    vi.stubGlobal('onMounted', onMounted)
    vi.stubGlobal('ref', ref)
  })

  afterAll(() => {
    config.global.renderStubDefaultSlot = false
    vi.unstubAllGlobals()
  })

  beforeEach(() => {
    vi.clearAllMocks()
    mocks.listCalcReports.mockResolvedValue({
      data: [
        { reportOid: 'report-1', name: 'Current', latestVersionName: '1.0.0' },
        { reportOid: 'report-2', name: 'Target', latestVersionName: '2.0.0' }
      ]
    })
    mocks.listVersions.mockResolvedValue({
      data: [{ importSegment: 'v_2_0_0', versionName: '2.0.0' }]
    })
  })

  it('loads selectors through LowCode field linkage and adds a detached dependency', async () => {
    const wrapper = shallowMount(DependencyDialog, {
      props: { reportOid: 'report-1', dependencies: [] }
    })
    await flushPromises()
    const form = wrapper.findComponent(LowCodeForm)
    const fields = form.props('fields') as ILowCodeField[]
    const targetField = fields.find((field) => field.name === 'targetReportOid')!
    const values: Record<string, unknown> = {
      alias: 'target',
      targetReportOid: 'report-2',
      selectors: ['latest'],
      defaultSelector: 'latest'
    }

    if (typeof targetField.onChanged !== 'function') throw new Error('Target report linkage is not configured')
    await targetField.onChanged('report-2', '', values, fields)
    expect(mocks.listVersions).toHaveBeenCalledWith('report-2')
    expect(fields.find((field) => field.name === 'selectors')?.options).toEqual([
      { label: 'latest', value: 'latest', versionName: null },
      { label: 'v_2_0_0', value: 'v_2_0_0', versionName: '2.0.0' }
    ])

    form.vm.$emit('ok', values)
    await flushPromises()
    expect(wrapper.text()).toContain('target')
    expect(wrapper.text()).toContain('Target')
  })
})
