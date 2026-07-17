import { shallowMount } from '@vue/test-utils'
import { computed, nextTick, ref } from 'vue'
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'
import DraggableTree from 'src/components/draggableTree/DraggableTree.vue'

describe('draggable tree controlled state', () => {
  beforeAll(() => {
    vi.stubGlobal('computed', computed)
    vi.stubGlobal('nextTick', nextTick)
    vi.stubGlobal('ref', ref)
  })

  afterAll(() => vi.unstubAllGlobals())

  it('preserves expanded keys when tree data changes and emits explicit expansion updates', async () => {
    const onExpandedKeysUpdate = vi.fn()
    const wrapper = shallowMount(DraggableTree, {
      props: {
        data: [
          { id: 'src', parentId: null, label: 'src' },
          { id: 'src/main.py', parentId: 'src', label: 'main.py' }
        ],
        expandedKeys: ['src'],
        'onUpdate:expandedKeys': onExpandedKeysUpdate
      },
      global: {
        stubs: {
          ElTree: {
            name: 'ElTree',
            props: ['data', 'defaultExpandedKeys', 'currentNodeKey'],
            emits: ['node-click', 'node-expand', 'node-collapse', 'node-drop', 'check'],
            template: '<div />'
          }
        }
      }
    })
    const tree = wrapper.findComponent({ name: 'ElTree' })
    expect(tree.props('defaultExpandedKeys')).toEqual(['src'])

    tree.vm.$emit('node-expand', { id: 'resources' })
    expect(onExpandedKeysUpdate).toHaveBeenCalledWith(['src', 'resources'])

    await wrapper.setProps({
      data: [
        { id: 'src', parentId: null, label: 'src' },
        { id: 'src/main.py', parentId: 'src', label: 'main.py' },
        { id: 'src/helper.py', parentId: 'src', label: 'helper.py' }
      ]
    })
    expect(tree.props('defaultExpandedKeys')).toEqual(['src'])
  })
})
