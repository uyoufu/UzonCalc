import { describe, expect, test } from 'bun:test'

import floatingButtonStyles from './floatingButton.css' with { type: 'text' }

describe('floatingButtonStyles', () => {
  test('统一大纲和打印浮动按钮的玻璃样式', () => {
    expect(floatingButtonStyles).toContain('.uz-outline-toggle,')
    expect(floatingButtonStyles).toContain('.uz-print-button')
    expect(floatingButtonStyles).toContain('rgba(255, 255, 255, 0.82)')
    expect(floatingButtonStyles).toContain('backdrop-filter: blur(14px) saturate(1.2)')
  })

  test('打印按钮 loading 时显示纯 spinner', () => {
    expect(floatingButtonStyles).toContain('.uz-print-button[data-loading="true"]::before')
    expect(floatingButtonStyles).toContain('animation: uz-print-spinner')
    expect(floatingButtonStyles).toContain('@keyframes uz-print-spinner')
  })
})
