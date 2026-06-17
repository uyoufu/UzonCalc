import { resetTocPageNumberCache } from './tocPageNumbers'

const CONTENT_START_MARK = '<!--CONTENT_START_MARK-->'
const CONTENT_END_MARK = '<!--CONTENT_END_MARK-->'
const UPDATE_MESSAGE_TYPE = 'uzoncalc:update-content'
const RUNTIME_MESSAGE_TYPE = 'uzoncalc:update-runtime'

interface ContentPatchMessage {
  type: typeof UPDATE_MESSAGE_TYPE
  contentHtml: string
  documentUrl?: string
  authToken?: string
}

interface RuntimeMessage {
  type: typeof RUNTIME_MESSAGE_TYPE
  documentUrl?: string
  authToken?: string
}

/** 判断消息是否为正文增量更新消息。 */
function isContentPatchMessage(data: unknown): data is ContentPatchMessage {
  if (!data || typeof data !== 'object') {
    return false
  }

  const message = data as Partial<ContentPatchMessage>
  return message.type === UPDATE_MESSAGE_TYPE && typeof message.contentHtml === 'string'
}

/** 判断消息是否为 iframe 运行时信息更新消息。 */
function isRuntimeMessage(data: unknown): data is RuntimeMessage {
  if (!data || typeof data !== 'object') {
    return false
  }

  const message = data as Partial<RuntimeMessage>
  return message.type === RUNTIME_MESSAGE_TYPE
}

/** 保存父页面传入的运行时信息。 */
export function applyRuntimeMessage(data: RuntimeMessage): void {
  if (typeof data.documentUrl === 'string') {
    ;(globalThis as { __uzoncalcDocumentUrl?: string }).__uzoncalcDocumentUrl = data.documentUrl
  }

  if (typeof data.authToken === 'string') {
    ;(globalThis as { __uzoncalcAuthToken?: string }).__uzoncalcAuthToken = data.authToken
  }
}

/** 重新插入正文脚本，触发 innerHTML 写入后不会自动执行的初始化逻辑。 */
function reactivateContentScripts(contentElement: Element): void {
  const scriptElements = Array.from(contentElement.querySelectorAll('script'))

  for (const scriptElement of scriptElements) {
    const newScriptElement = document.createElement('script')
    for (const attribute of Array.from(scriptElement.attributes)) {
      newScriptElement.setAttribute(attribute.name, attribute.value)
    }
    newScriptElement.textContent = scriptElement.textContent
    scriptElement.replaceWith(newScriptElement)
  }
}

/** 应用正文增量消息，返回是否实际更新了页面。 */
export function applyContentPatchMessage(data: unknown): boolean {
  if (!isContentPatchMessage(data)) {
    return false
  }

  applyRuntimeMessage(data)

  const contentElement = document.querySelector('.content')
  if (!contentElement) {
    return false
  }

  // 保留模板正文标记，便于后续增量更新仍能定位正文边界
  contentElement.innerHTML = `${CONTENT_START_MARK}${data.contentHtml}${CONTENT_END_MARK}`
  reactivateContentScripts(contentElement)
  resetTocPageNumberCache()
  return true
}

/** 监听父窗口传入的正文补丁消息。 */
export function setupContentPatchMessaging(onUpdated: () => void): void {
  window.addEventListener('message', (event) => {
    if (event.source !== window.parent) {
      return
    }

    if (applyContentPatchMessage(event.data)) {
      onUpdated()
      return
    }

    if (isRuntimeMessage(event.data)) {
      applyRuntimeMessage(event.data)
    }
  })
}
