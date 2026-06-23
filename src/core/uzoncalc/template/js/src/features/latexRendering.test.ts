import { afterEach, describe, expect, test } from 'bun:test'

import { renderLatexElements } from './latexRendering'

interface KatexRenderOptions {
  displayMode: boolean
  throwOnError: boolean
  output: string
}

class FakeLatexElement {
  constructor(readonly textContent: string | null) {}
}

class FakeDocument {
  constructor(private readonly latexElements: FakeLatexElement[]) {}

  /** 查询测试关注的 LaTeX 元素。 */
  querySelectorAll(selector: string): FakeLatexElement[] {
    if (selector === 'latex.latex') {
      return this.latexElements
    }
    return []
  }
}

function installFakeDocument(latexElements: FakeLatexElement[]): void {
  ;(globalThis as { document: unknown }).document = new FakeDocument(latexElements)
}

afterEach(() => {
  delete (globalThis as { document?: unknown }).document
  delete (globalThis as { window?: unknown }).window
})

describe('renderLatexElements', () => {
  test('使用 KaTeX 渲染所有 latex 标签', () => {
    const firstElement = new FakeLatexElement('x_i^2')
    const secondElement = new FakeLatexElement(null)
    const renderCalls: Array<{
      source: string
      element: FakeLatexElement
      options: KatexRenderOptions
    }> = []
    installFakeDocument([firstElement, secondElement])
    ;(globalThis as { window: unknown }).window = {
      katex: {
        render(source: string, element: FakeLatexElement, options: KatexRenderOptions): void {
          renderCalls.push({ source, element, options })
        }
      }
    }

    renderLatexElements()

    expect(renderCalls).toEqual([
      {
        source: 'x_i^2',
        element: firstElement,
        options: {
          displayMode: true,
          throwOnError: false,
          output: 'htmlAndMathml'
        }
      },
      {
        source: '',
        element: secondElement,
        options: {
          displayMode: true,
          throwOnError: false,
          output: 'htmlAndMathml'
        }
      }
    ])
  })

  test('缺少 KaTeX 时静默跳过渲染', () => {
    installFakeDocument([new FakeLatexElement('x_i^2')])
    ;(globalThis as { window: unknown }).window = {}

    expect(() => renderLatexElements()).not.toThrow()
  })
})
