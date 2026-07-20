import { describe, expect, test } from 'bun:test'

import scrollStyles from './scroll.css' with { type: 'text' }

describe('scrollStyles', () => {
  test('滚动条使用稳定命中区域并在滑块悬停时加粗变色', () => {
    expect(scrollStyles).not.toContain('::-webkit-scrollbar:hover')
    expect(scrollStyles).toContain('width: 8px')
    expect(scrollStyles).toContain('height: 8px')
    expect(scrollStyles).toContain('background-clip: content-box')
    expect(scrollStyles).toContain('border: 2px solid transparent')
    expect(scrollStyles).toContain('&:hover::-webkit-scrollbar-thumb:hover')
    expect(scrollStyles).toContain('border: 0')
    expect(scrollStyles).toContain('background-color: #9aa6b2')
  })
})
