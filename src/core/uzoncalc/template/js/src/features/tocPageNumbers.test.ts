import { afterEach, describe, expect, test } from 'bun:test'

import {
  TOC_PAGE_NUMBERS_ROUTE,
  applyTocPageNumbers,
  printWithTocPageNumbers,
  resetTocPageNumberCache
} from './tocPageNumbers'

class FakeTocPageElement {
  textContent = '\u00a0'
  readonly attributes = new Map<string, string>()

  constructor(headingId: string) {
    this.attributes.set('data-heading-id', headingId)
    this.attributes.set('data-page-placeholder', 'true')
  }

  /** 读取属性。 */
  getAttribute(name: string): string | null {
    return this.attributes.get(name) ?? null
  }

  /** 删除属性。 */
  removeAttribute(name: string): void {
    this.attributes.delete(name)
  }
}

class FakeButtonElement {
  disabled = false
  textContent = '🖨️'
  readonly attributes = new Map<string, string>([['aria-label', '打印文档']])
  readonly dataset: Record<string, string> = {}

  /** 写入按钮属性。 */
  setAttribute(name: string, value: string): void {
    this.attributes.set(name, value)
  }

  /** 读取按钮属性。 */
  getAttribute(name: string): string | null {
    return this.attributes.get(name) ?? null
  }

  /** 删除按钮属性。 */
  removeAttribute(name: string): void {
    this.attributes.delete(name)
  }
}

class FakeDocument {
  readonly tocPages = [
    new FakeTocPageElement('heading-0'),
    new FakeTocPageElement('heading-1')
  ]
  readonly printButton = new FakeButtonElement()

  /** 查询测试所需元素集合。 */
  querySelectorAll(selector: string): FakeTocPageElement[] {
    if (selector === '.toc-page[data-heading-id]') {
      return this.tocPages
    }
    return []
  }

  /** 查询打印按钮。 */
  querySelector(selector: string): FakeButtonElement | null {
    return selector === '.uz-print-button' ? this.printButton : null
  }
}

function installFakeRuntime(fetchImpl: typeof fetch): FakeDocument {
  const fakeDocument = new FakeDocument()
  ;(globalThis as { document: unknown }).document = fakeDocument
  ;(globalThis as { window: unknown }).window = {
    location: { href: 'http://localhost/report.html' },
    print() {
      ;(globalThis as { printCount?: number }).printCount =
        ((globalThis as { printCount?: number }).printCount ?? 0) + 1
    }
  }
  ;(globalThis as { fetch: unknown }).fetch = fetchImpl
  return fakeDocument
}

afterEach(() => {
  resetTocPageNumberCache()
  delete (globalThis as { document?: unknown }).document
  delete (globalThis as { window?: unknown }).window
  delete (globalThis as { fetch?: unknown }).fetch
  delete (globalThis as { printCount?: number }).printCount
  delete (globalThis as { __uzoncalcDocumentUrl?: string }).__uzoncalcDocumentUrl
  delete (globalThis as { __uzoncalcAuthToken?: string }).__uzoncalcAuthToken
})

describe('applyTocPageNumbers', () => {
  test('更新目录页码并移除占位属性', () => {
    const fakeDocument = installFakeRuntime(async () => {
      throw new Error('fetch should not be called')
    })

    applyTocPageNumbers({ 'heading-0': 2 })

    expect(fakeDocument.tocPages[0]?.textContent).toBe('2')
    expect(fakeDocument.tocPages[0]?.getAttribute('data-page-placeholder')).toBeNull()
    expect(fakeDocument.tocPages[1]?.textContent).toBe('\u00a0')
  })
})

describe('printWithTocPageNumbers', () => {
  test('首次打印通过统一路由请求页码再触发打印', async () => {
    const requestedUrls: string[] = []
    const fakeDocument = installFakeRuntime(async (input, init) => {
      requestedUrls.push(String(input))
      expect(fakeDocument.printButton.disabled).toBe(true)
      expect(fakeDocument.printButton.getAttribute('data-loading')).toBe('true')
      expect(fakeDocument.printButton.getAttribute('aria-label')).toBe('正在准备打印')
      expect(fakeDocument.printButton.textContent).toBe('')
      expect(init?.method).toBe('POST')
      expect((init?.headers as Record<string, string>).Authorization).toBe('Bearer token-value')
      expect(JSON.parse(String(init?.body))).toEqual({
        documentUrl: 'http://localhost/report.html'
      })
      return new Response(
        JSON.stringify({
          ok: true,
          data: { 'heading-0': 3 },
          message: 'success',
          code: 200
        }),
        { headers: { 'Content-Type': 'application/json' } }
      )
    })
    ;(globalThis as { __uzoncalcAuthToken?: string }).__uzoncalcAuthToken = 'token-value'

    await printWithTocPageNumbers()

    expect(requestedUrls).toEqual([TOC_PAGE_NUMBERS_ROUTE])
    expect((globalThis as { printCount?: number }).printCount).toBe(1)
    expect(fakeDocument.printButton.disabled).toBe(false)
    expect(fakeDocument.printButton.getAttribute('data-loading')).toBeNull()
    expect(fakeDocument.printButton.getAttribute('aria-label')).toBe('打印文档')
    expect(fakeDocument.printButton.textContent).toBe('🖨️')
  })

  test('页码请求失败时恢复打印按钮状态且不触发打印', async () => {
    const fakeDocument = installFakeRuntime(async () => {
      expect(fakeDocument.printButton.disabled).toBe(true)
      expect(fakeDocument.printButton.getAttribute('data-loading')).toBe('true')
      return new Response(
        JSON.stringify({
          ok: false,
          data: null,
          message: 'page number service failed',
          code: 500
        }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      )
    })

    await expect(printWithTocPageNumbers()).rejects.toThrow('page number service failed')

    expect((globalThis as { printCount?: number }).printCount).toBeUndefined()
    expect(fakeDocument.printButton.disabled).toBe(false)
    expect(fakeDocument.printButton.getAttribute('data-loading')).toBeNull()
    expect(fakeDocument.printButton.getAttribute('aria-label')).toBe('打印文档')
    expect(fakeDocument.printButton.textContent).toBe('🖨️')
  })

  test('同一 URL 已有页码时不重复请求', async () => {
    let requestCount = 0
    ;(globalThis as { __uzoncalcDocumentUrl?: string }).__uzoncalcDocumentUrl =
      'http://localhost/report.html'
    installFakeRuntime(async () => {
      requestCount += 1
      return new Response(
        JSON.stringify({
          ok: true,
          data: { 'heading-0': 3 },
          message: 'success',
          code: 200
        })
      )
    })

    await printWithTocPageNumbers()
    await printWithTocPageNumbers()

    expect(requestCount).toBe(1)
    expect((globalThis as { printCount?: number }).printCount).toBe(2)
  })
})
