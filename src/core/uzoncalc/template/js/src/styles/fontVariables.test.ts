import { describe, expect, test } from 'bun:test'

import { templateStyles } from './index'
import variablesStyles from './variables.css' with { type: 'text' }

describe('font variables', () => {
  test('模板字体族集中定义在变量样式中', () => {
    expect(variablesStyles).toContain('--uz-font-body:')
    expect(variablesStyles).toContain('--uz-font-page:')
    expect(templateStyles).toContain('--uz-font-body:')
    expect(templateStyles).toContain('--uz-font-page:')
  })
})
