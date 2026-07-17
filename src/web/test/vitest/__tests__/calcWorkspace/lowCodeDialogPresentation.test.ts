import { shallowMount } from '@vue/test-utils'
import { computed, onMounted, ref, toRefs, watch } from 'vue'
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'
import LowCodeForm from 'src/components/lowCode/LowCodeForm.vue'
import { LowCodeFieldType } from 'src/components/lowCode/types'

vi.mock('src/i18n/helpers', () => ({ t: (key: string) => key, tButton: (key: string) => key }))
vi.mock('src/utils/dialog', () => ({ notifyError: vi.fn() }))

describe('lowCode dialog presentation', () => {
  beforeAll(() => {
    vi.stubGlobal('computed', computed)
    vi.stubGlobal('onMounted', onMounted)
    vi.stubGlobal('ref', ref)
    vi.stubGlobal('toRefs', toRefs)
    vi.stubGlobal('watch', watch)
  })

  afterAll(() => {
    vi.unstubAllGlobals()
  })

  it('passes hint and autofocus to input fields', () => {
    const wrapper = shallowMount(LowCodeForm, {
      props: {
        fields: [
          {
            name: 'versionName',
            label: 'Version',
            type: LowCodeFieldType.text,
            hint: 'MAJOR.MINOR.PATCH',
            autofocus: true
          }
        ]
      },
      global: {
        stubs: {
          QInput: {
            name: 'QInput',
            props: ['hint', 'autofocus'],
            template: '<input class="test-input" :data-hint="hint" :data-autofocus="autofocus">'
          }
        }
      }
    })

    const input = wrapper.get('.test-input')
    expect(input.attributes('data-hint')).toBe('MAJOR.MINOR.PATCH')
    expect(input.attributes('data-autofocus')).toBe('true')
  })
})

