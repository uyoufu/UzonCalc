import { describe, expect, test } from 'bun:test'

import printStyles from './print.css' with { type: 'text' }

describe('printStyles', () => {
  test('打印时保留模板颜色和背景', () => {
    expect(printStyles).toContain('print-color-adjust: exact')
    expect(printStyles).toContain('-webkit-print-color-adjust: exact')
  })

  test('打印时统一强制内容文本颜色', () => {
    expect(printStyles).toContain('.content *')
    expect(printStyles).toContain('.content *::before')
    expect(printStyles).toContain('.content *::after')
    expect(printStyles).toContain('.content *::marker')
    expect(printStyles).toContain('color: var(--uz-text-color-print) !important')
  })

  test('打印时不维护局部文本颜色补丁', () => {
    expect(printStyles).not.toContain('math .function-name')
    expect(printStyles).not.toContain('math .unit')
  })

  test('打印时公式斜体使用正文变量字体', () => {
    expect(printStyles).toContain('font-family: var(--uz-font-body) !important')
  })

  test('打印时允许代码块跨页显示', () => {
    expect(printStyles).not.toMatch(/pre,\s*blockquote,\s*\.plot-container/)
    expect(printStyles).toContain('blockquote,\n  .plot-container')
  })
})
