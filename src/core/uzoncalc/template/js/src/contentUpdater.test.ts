import { afterEach, describe, expect, test } from 'bun:test'

import { applyContentPatchMessage } from './contentUpdater'

class FakeResourceElement {
  private readonly attributes: Record<string, string>

  constructor(attributes: Record<string, string>) {
    this.attributes = { ...attributes }
  }

  /** 读取资源属性，模拟 DOM 元素接口。 */
  getAttribute(name: string): string | null {
    return this.attributes[name] ?? null
  }

  /** 写入资源属性，便于断言相对路径已被重写。 */
  setAttribute(name: string, value: string): void {
    this.attributes[name] = value
  }
}

class FakeScriptElement {
  textContent = ''
  replacedWith: FakeScriptElement | null = null
  private readonly scriptAttributes: Record<string, string>

  constructor(attributes: Record<string, string> = {}) {
    this.scriptAttributes = { ...attributes }
  }

  /** 读取属性列表，模拟浏览器脚本元素的 attributes 接口。 */
  get attributes(): Array<{ name: string; value: string }> {
    return Object.entries(this.scriptAttributes).map(([name, value]) => ({
      name,
      value
    }))
  }

  /** 写入脚本属性，用于验证新脚本保留原属性。 */
  setAttribute(name: string, value: string): void {
    this.scriptAttributes[name] = value
  }

  /** 读取脚本属性，便于断言外部脚本配置未丢失。 */
  getAttribute(name: string): string | null {
    return this.scriptAttributes[name] ?? null
  }

  /** 替换脚本节点，模拟浏览器执行新插入脚本的关键动作。 */
  replaceWith(element: FakeScriptElement): void {
    this.replacedWith = element
  }
}

class FakeContentElement {
  private contentHtml = ''
  readonly resources: FakeResourceElement[] = []
  readonly scripts: FakeScriptElement[] = []

  /** 写入正文 HTML，并解析测试关心的 src/href 属性。 */
  set innerHTML(value: string) {
    this.contentHtml = value
    this.resources.length = 0
    this.scripts.length = 0

    const resourcePattern = /\s(src|href)="([^"]+)"/g
    let match = resourcePattern.exec(value)
    while (match) {
      this.resources.push(new FakeResourceElement({ [match[1] ?? '']: match[2] ?? '' }))
      match = resourcePattern.exec(value)
    }

    const scriptPattern = /<script([^>]*)>([\s\S]*?)<\/script>/g
    let scriptMatch = scriptPattern.exec(value)
    while (scriptMatch) {
      const attributes: Record<string, string> = {}
      const attributePattern = /\s([a-zA-Z:-]+)="([^"]*)"/g
      let attributeMatch = attributePattern.exec(scriptMatch[1] ?? '')
      while (attributeMatch) {
        attributes[attributeMatch[1] ?? ''] = attributeMatch[2] ?? ''
        attributeMatch = attributePattern.exec(scriptMatch[1] ?? '')
      }

      const scriptElement = new FakeScriptElement(attributes)
      scriptElement.textContent = scriptMatch[2] ?? ''
      this.scripts.push(scriptElement)
      scriptMatch = scriptPattern.exec(value)
    }
  }

  get innerHTML(): string {
    return this.contentHtml
  }

  /** 查询正文内的资源元素。 */
  querySelectorAll(selector: string): Array<FakeResourceElement | FakeScriptElement> {
    if (selector === '[src], [href]') {
      return this.resources
    }
    if (selector === 'script') {
      return this.scripts
    }
    return []
  }
}

class FakeDocument {
  readonly contentElement = new FakeContentElement()
  readonly createdScripts: FakeScriptElement[] = []

  /** 查询正文容器。 */
  querySelector(selector: string): FakeContentElement | null {
    return selector === '.content' ? this.contentElement : null
  }

  /** 创建脚本节点，用于模拟重新插入脚本触发执行。 */
  createElement(tagName: string): FakeScriptElement {
    if (tagName !== 'script') {
      throw new Error(`Unexpected tag: ${tagName}`)
    }

    const scriptElement = new FakeScriptElement()
    this.createdScripts.push(scriptElement)
    return scriptElement
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

describe('applyContentPatchMessage', () => {
  test('仅更新正文且不改写相对资源路径', () => {
    const fakeDocument = installFakeDocument()

    const applied = applyContentPatchMessage({
      type: 'uzoncalc:update-content',
      contentHtml: '<h2>新结果</h2><img src="images/chart.png"><a href="#section">跳转</a>'
    })

    expect(applied).toBe(true)
    expect(fakeDocument.contentElement.innerHTML).toContain('CONTENT_START_MARK')
    expect(fakeDocument.contentElement.innerHTML).toContain('<h2>新结果</h2>')
    expect(fakeDocument.contentElement.resources[0]?.getAttribute('src')).toBe('images/chart.png')
    expect(fakeDocument.contentElement.resources[1]?.getAttribute('href')).toBe('#section')
  })

  test('忽略类型不匹配的消息', () => {
    const fakeDocument = installFakeDocument()

    const applied = applyContentPatchMessage({
      type: 'other-message',
      contentHtml: '<p>不会更新</p>'
    })

    expect(applied).toBe(false)
    expect(fakeDocument.contentElement.innerHTML).toBe('')
  })

  test('正文补丁中的内联脚本会被重新插入以触发执行', () => {
    const fakeDocument = installFakeDocument()

    const applied = applyContentPatchMessage({
      type: 'uzoncalc:update-content',
      contentHtml: '<figure><script>window.echartReady = true;</script></figure>'
    })

    const oldScript = fakeDocument.contentElement.scripts[0]
    const newScript = fakeDocument.createdScripts[0]
    expect(applied).toBe(true)
    expect(oldScript?.replacedWith).toBe(newScript)
    expect(newScript?.textContent).toBe('window.echartReady = true;')
  })

  test('重新插入脚本时保留原脚本属性', () => {
    const fakeDocument = installFakeDocument()

    applyContentPatchMessage({
      type: 'uzoncalc:update-content',
      contentHtml: '<script type="module" src="charts.js" data-chart-id="main"></script>'
    })

    const newScript = fakeDocument.createdScripts[0]
    expect(newScript?.getAttribute('type')).toBe('module')
    expect(newScript?.getAttribute('src')).toBe('charts.js')
    expect(newScript?.getAttribute('data-chart-id')).toBe('main')
  })
})
