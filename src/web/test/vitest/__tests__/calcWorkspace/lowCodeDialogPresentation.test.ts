import { flushPromises, shallowMount } from '@vue/test-utils'
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

  it('invokes field linkage callbacks when a LowCode value changes', async () => {
    const onChanged = vi.fn()
    const wrapper = shallowMount(LowCodeForm, {
      props: {
        fields: [{
          name: 'target',
          label: 'Target',
          type: LowCodeFieldType.text,
          value: 'before',
          onChanged
        }]
      },
      global: {
        stubs: {
          QInput: {
            name: 'QInput',
            props: ['modelValue'],
            emits: ['update:modelValue'],
            template: '<input class="linkage-input" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)">'
          }
        }
      }
    })

    await wrapper.get('.linkage-input').setValue('after')
    await flushPromises()

    expect(onChanged).toHaveBeenCalledWith('after', 'before', expect.objectContaining({ target: 'after' }), expect.any(Array))
  })
})

