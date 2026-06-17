import { resolvePrintButton, setPrintButtonLoading } from '../ui/printButton'

export const TOC_PAGE_NUMBERS_ROUTE = '/api/v1/calc/toc-page-numbers'

interface TocPageNumbersResponse {
  ok: boolean
  data?: Record<string, number> | null
  message?: string | null
  code: number
}

let lastResolvedDocumentUrl = ''
let activePrintPromise: Promise<void> | null = null

/** 清空 ToC 页码缓存，正文局部更新后应重新请求页码。 */
export function resetTocPageNumberCache(): void {
  lastResolvedDocumentUrl = ''
}

/** 读取当前文档 URL，局部更新后优先使用父页面传入的新地址。 */
function resolveDocumentUrl(): string {
  return (globalThis as { __uzoncalcDocumentUrl?: string }).__uzoncalcDocumentUrl || window.location.href
}

/** 读取父页面传入的 API 鉴权 token。 */
function resolveAuthHeaders(): Record<string, string> {
  const authToken = (globalThis as { __uzoncalcAuthToken?: string }).__uzoncalcAuthToken
  if (!authToken) {
    return {}
  }
  return { Authorization: `Bearer ${authToken}` }
}

/** 判断当前目录是否仍有需要回写的页码。 */
function hasTocPagePlaceholders(): boolean {
  return document.querySelectorAll('.toc-page[data-heading-id]').length > 0
}

/** 将页码映射写回当前文档目录。 */
export function applyTocPageNumbers(pageNumbers: Record<string, number>): void {
  const tocPageElements = document.querySelectorAll<HTMLElement>('.toc-page[data-heading-id]')

  tocPageElements.forEach((tocPageElement) => {
    const headingId = tocPageElement.getAttribute('data-heading-id')
    if (!headingId || pageNumbers[headingId] == null) {
      return
    }

    tocPageElement.textContent = String(pageNumbers[headingId])
    tocPageElement.removeAttribute('data-page-placeholder')
  })
}

/** 请求后端计算当前文档目录页码。 */
async function fetchTocPageNumbers(documentUrl: string): Promise<Record<string, number>> {
  const response = await fetch(TOC_PAGE_NUMBERS_ROUTE, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...resolveAuthHeaders()
    },
    body: JSON.stringify({ documentUrl })
  })

  const result = (await response.json()) as TocPageNumbersResponse
  if (!response.ok || !result.ok || !result.data) {
    throw new Error(result.message || `ToC page number request failed: ${response.status}`)
  }

  return result.data
}

function refreshPrintButtonLoadingState(isLoading: boolean): void {
  const printButton = resolvePrintButton()
  if (!printButton) {
    return
  }

  setPrintButtonLoading(printButton, isLoading)
}

/** 打印前按需刷新 ToC 页码，同一 URL 已刷新时不重复请求。 */
export async function printWithTocPageNumbers(): Promise<void> {
  if (activePrintPromise) {
    return activePrintPromise
  }

  activePrintPromise = (async () => {
    const documentUrl = resolveDocumentUrl()
    const shouldRefreshPageNumbers = hasTocPagePlaceholders() && lastResolvedDocumentUrl !== documentUrl

    if (shouldRefreshPageNumbers) {
      refreshPrintButtonLoadingState(true)

      try {
        const pageNumbers = await fetchTocPageNumbers(documentUrl)
        applyTocPageNumbers(pageNumbers)
        lastResolvedDocumentUrl = documentUrl
      } finally {
        refreshPrintButtonLoadingState(false)
      }
    }

    window.print()
  })()

  try {
    await activePrintPromise
  } finally {
    activePrintPromise = null
  }
}

/** 绑定模板打印按钮。 */
export function setupTocPageNumberPrintButton(): void {
  const printButton = resolvePrintButton()
  if (!printButton) {
    return
  }

  if (printButton.dataset.tocPageNumbersBound === 'true') {
    return
  }

  printButton.dataset.tocPageNumbersBound = 'true'
  printButton.addEventListener('click', () => {
    void printWithTocPageNumbers()
  })
}
