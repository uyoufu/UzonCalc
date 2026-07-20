import { config, flushPromises, shallowMount } from '@vue/test-utils'
import { computed, onMounted, ref } from 'vue'
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import DependencyDialog from 'src/pages/calcReport/workbench/workspace/DependencyDialog.vue'
import LowCodeForm from 'src/components/lowCode/LowCodeForm.vue'
import CommonBtn from 'src/components/quasarWrapper/buttons/CommonBtn.vue'
import type { ILowCodeField } from 'src/components/lowCode/types'

const mocks = vi.hoisted(() => ({
  listCalcReports: vi.fn(),
  listVersions: vi.fn(),
  notifyError: vi.fn(),
  notifySuccess: vi.fn(),
  writeText: vi.fn()
}))

vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key, tButton: (key: string) => key }))
vi.mock('src/utils/dialog', () => ({
  notifyError: mocks.notifyError,
  notifySuccess: mocks.notifySuccess
}))
vi.mock('src/api/calc/reports', () => ({ listCalcReports: mocks.listCalcReports }))
vi.mock('src/api/calc/versions', () => ({ listVersions: mocks.listVersions }))

describe('dependency dialog', () => {
  beforeAll(() => {
    config.global.renderStubDefaultSlot = true
    vi.stubGlobal('computed', computed)
    vi.stubGlobal('onMounted', onMounted)
    vi.stubGlobal('ref', ref)
    vi.stubGlobal('navigator', { clipboard: { writeText: mocks.writeText } })
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
    mocks.writeText.mockResolvedValue(undefined)
  })

  it('loads one dependency version and emits one default selector', async () => {
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
      dependencyVersion: 'latest'
    }

    expect(fields.map((field) => field.name)).toEqual([
      'targetReportOid',
      'alias',
      'dependencyVersion'
    ])
    if (typeof targetField.onChanged !== 'function')
      throw new Error('Target report linkage is not configured')
    await targetField.onChanged('report-2', '', values, fields)
    expect(mocks.listVersions).toHaveBeenCalledWith('report-2')
    expect(fields.find((field) => field.name === 'dependencyVersion')?.options).toEqual([
      { label: 'latest', value: 'latest', versionName: null },
      { label: '2.0.0', value: 'v_2_0_0', versionName: '2.0.0' }
    ])

    values.dependencyVersion = 'v_2_0_0'
    form.vm.$emit('ok', values)
    await flushPromises()
    expect(wrapper.text()).toContain('target')
    expect(wrapper.text()).toContain('Target')
    expect(wrapper.text()).toContain('calcdeps.target.v_2_0_0')

    Object.defineProperty(wrapper.findComponent({ name: 'QDialog' }).vm, 'hide', { value: vi.fn() })
    const applyButton = wrapper
      .findAllComponents(CommonBtn)
      .find((button) => button.props('icon') === 'done_all')!
    await applyButton.trigger('click')
    expect(wrapper.emitted('ok')?.[0]).toEqual([
      [
        {
          alias: 'target',
          targetReportOid: 'report-2',
          selectors: [{ selectorKey: 'v_2_0_0', versionName: '2.0.0', isDefault: true }]
        }
      ]
    ])
  })

  it('uses the legacy default selector when editing a multi-selector dependency', async () => {
    const wrapper = shallowMount(DependencyDialog, {
      props: {
        reportOid: 'report-1',
        dependencies: [
          {
            alias: 'target',
            targetReportOid: 'report-2',
            selectors: [
              { selectorKey: 'latest', versionName: null, isDefault: false },
              { selectorKey: 'v_2_0_0', versionName: '2.0.0', isDefault: true }
            ]
          }
        ]
      }
    })
    await flushPromises()

    const editButton = wrapper
      .findAllComponents(CommonBtn)
      .find((button) => button.props('icon') === 'edit')!
    await editButton.trigger('click')
    await flushPromises()

    const fields = wrapper.findComponent(LowCodeForm).props('fields') as ILowCodeField[]
    expect(fields.find((field) => field.name === 'dependencyVersion')?.value).toBe('v_2_0_0')
  })

  it('copies latest and explicit dependency reference paths and reports failures', async () => {
    const wrapper = shallowMount(DependencyDialog, {
      props: {
        reportOid: 'report-1',
        dependencies: [
          {
            alias: 'latest_target',
            targetReportOid: 'report-2',
            selectors: [{ selectorKey: 'latest', versionName: null, isDefault: true }]
          },
          {
            alias: 'pinned_target',
            targetReportOid: 'report-2',
            selectors: [{ selectorKey: 'v_2_0_0', versionName: '2.0.0', isDefault: true }]
          }
        ]
      }
    })
    await flushPromises()

    const copyButtons = wrapper
      .findAllComponents(CommonBtn)
      .filter((button) => button.props('icon') === 'content_copy')
    await copyButtons[0]!.trigger('click')
    await copyButtons[1]!.trigger('click')
    expect(mocks.writeText).toHaveBeenNthCalledWith(1, 'calcdeps.latest_target')
    expect(mocks.writeText).toHaveBeenNthCalledWith(2, 'calcdeps.pinned_target.v_2_0_0')
    expect(mocks.notifySuccess).toHaveBeenCalledTimes(2)

    mocks.writeText.mockRejectedValueOnce(new Error('clipboard unavailable'))
    await copyButtons[0]!.trigger('click')
    expect(mocks.notifyError).toHaveBeenCalledWith('calcWorkspace.dependencyReferenceCopyFailed')
  })
})
