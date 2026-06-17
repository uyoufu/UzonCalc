import { afterEach, describe, expect, test } from 'bun:test'

import { resolvePrintButton, setPrintButtonLoading } from './printButton'

class FakeButtonElement {
  disabled = false
  textContent = '🖨️'
  readonly attributes = new Map<string, string>([['aria-label', '打印文档']])

  /** 查询按钮属性。 */
  getAttribute(name: string): string | null {
    return this.attributes.get(name) ?? null
  }

  /** 写入按钮属性。 */
  setAttribute(name: string, value: string): void {
    this.attributes.set(name, value)
  }

  /** 删除按钮属性。 */
  removeAttribute(name: string): void {
    this.attributes.delete(name)
  }
}

class FakeDocument {
  readonly printButton = new FakeButtonElement()

  /** 查询打印按钮。 */
  querySelector(selector: string): FakeButtonElement | null {
    return selector === '.uz-print-button' ? this.printButton : null
  }
}

function installFakeDocument(): FakeDocument {
  const fakeDocument = new FakeDocument()
  ;(globalThis as { document: unknown }).document = fakeDocument
  return fakeDocument
}

afterEach(() => {
  delete (globalThis as { document?: unknown }).document
})

describe('printButton', () => {
  test('可定位模板打印按钮', () => {
    const fakeDocument = installFakeDocument()

    expect(resolvePrintButton()).toBe(fakeDocument.printButton)
  })

  test('loading 时仅保留 spinner 并恢复原始按钮状态', () => {
    const fakeDocument = installFakeDocument()

    setPrintButtonLoading(fakeDocument.printButton, true)

    expect(fakeDocument.printButton.disabled).toBe(true)
    expect(fakeDocument.printButton.getAttribute('data-loading')).toBe('true')
    expect(fakeDocument.printButton.getAttribute('aria-label')).toBe('正在准备打印')
    expect(fakeDocument.printButton.textContent).toBe('')

    setPrintButtonLoading(fakeDocument.printButton, false)

    expect(fakeDocument.printButton.disabled).toBe(false)
    expect(fakeDocument.printButton.getAttribute('data-loading')).toBeNull()
    expect(fakeDocument.printButton.getAttribute('aria-label')).toBe('打印文档')
    expect(fakeDocument.printButton.textContent).toBe('🖨️')
  })
})
