import { afterEach, describe, expect, test } from 'bun:test'

import { collectDocumentHeadings } from './headingCollector'

class FakeHeadingElement {
  id: string
  readonly tagName: string
  readonly textContent: string
  readonly parentElement: FakeHeadingElement | null

  constructor(options: {
    tagName: string
    textContent: string
    id?: string
    parentElement?: FakeHeadingElement | null
  }) {
    this.tagName = options.tagName.toUpperCase()
    this.textContent = options.textContent
    this.id = options.id ?? ''
    this.parentElement = options.parentElement ?? null
  }

  /** 模拟 closest 查询，用于排除目录内部标题。 */
  closest(selector: string): FakeHeadingElement | null {
    let currentElement: FakeHeadingElement | null = this
    while (currentElement) {
      if (selector === '#toc' && currentElement.id === 'toc') {
        return currentElement
      }
      currentElement = currentElement.parentElement
    }
    return null
  }
}

class FakeDocument {
  constructor(private readonly headings: FakeHeadingElement[]) {}

  /** 模拟标题查询，只覆盖收集逻辑使用的选择器。 */
  querySelectorAll(selector: string): FakeHeadingElement[] {
    if (selector === 'h2, h3, h4, h5, h6') {
      return this.headings
    }
    return []
  }
}

function installFakeDocument(headings: FakeHeadingElement[]): void {
  ;(globalThis as { document: unknown }).document = new FakeDocument(headings)
}

afterEach(() => {
  delete (globalThis as { document?: unknown }).document
})

describe('collectDocumentHeadings', () => {
  test('为正文标题生成稳定编号和缺失 id', () => {
    const headings = [
      new FakeHeadingElement({ tagName: 'h2', textContent: '总则' }),
      new FakeHeadingElement({
        tagName: 'h3',
        textContent: '材料',
        id: 'material'
      }),
      new FakeHeadingElement({ tagName: 'h2', textContent: '计算' })
    ]
    installFakeDocument(headings)

    const items = collectDocumentHeadings()

    expect(items.map((item) => item.sectionNumber)).toEqual(['1', '1.1', '2'])
    expect(items.map((item) => item.heading.id)).toEqual(['heading-0', 'material', 'heading-2'])
    expect(items.map((item) => item.indentLevel)).toEqual([0, 1, 0])
  })

  test('收集标题时去掉 toc marker 前缀', () => {
    const headings = [
      new FakeHeadingElement({
        tagName: 'h2',
        textContent: 'UZONCALC_TOC_HEADING:heading-0|安装使用'
      })
    ]
    installFakeDocument(headings)

    const items = collectDocumentHeadings()

    expect(items[0]?.text).toBe('安装使用')
  })

  test('跳过目录内部标题', () => {
    const toc = new FakeHeadingElement({
      tagName: 'div',
      textContent: '',
      id: 'toc'
    })
    const headings = [
      new FakeHeadingElement({
        tagName: 'h2',
        textContent: '目录标题',
        parentElement: toc
      }),
      new FakeHeadingElement({ tagName: 'h2', textContent: '正文标题' })
    ]
    installFakeDocument(headings)

    const items = collectDocumentHeadings()

    expect(items).toHaveLength(1)
    expect(items[0]?.text).toBe('正文标题')
  })
})
