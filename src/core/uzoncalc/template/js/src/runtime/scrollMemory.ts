const STORAGE_PREFIX = 'uzoncalc:scroll:'
const BOTTOM_THRESHOLD_PX = 8
const SAVE_THROTTLE_MS = 150
const FOLLOW_UP_RESTORE_DELAY_MS = 120
let isScrollMemorySetup = false

type ScrollState = {
  scrollTop: number
  stickToBottom: boolean
}

function getQueryScrollKey(): string {
  const scrollKey = new URLSearchParams(window.location.search).get('scrollKey')
  return scrollKey?.trim() ?? ''
}

function getStorageKey(): string {
  const queryScrollKey = getQueryScrollKey()
  if (queryScrollKey) {
    return `${STORAGE_PREFIX}${queryScrollKey}`
  }

  return `${STORAGE_PREFIX}${[
    window.location.pathname || '',
    window.location.search || '',
    document.title || ''
  ].join(':')}`
}

function getScrollRoot(): Element {
  return document.scrollingElement ?? document.documentElement
}

function getMaxScrollTop(): number {
  return Math.max(0, getScrollRoot().scrollHeight - window.innerHeight)
}

function isAtBottom(): boolean {
  return getMaxScrollTop() - window.scrollY <= BOTTOM_THRESHOLD_PX
}

function saveScrollState(): void {
  try {
    const scrollState: ScrollState & { updatedAt: number } = {
      scrollTop: Math.max(0, Math.round(window.scrollY)),
      stickToBottom: isAtBottom(),
      updatedAt: Date.now()
    }

    window.localStorage.setItem(getStorageKey(), JSON.stringify(scrollState))
  } catch {
    // Ignore storage failures in restricted browser contexts.
  }
}

function loadScrollState(): ScrollState | null {
  try {
    const rawState = window.localStorage.getItem(getStorageKey())
    if (!rawState) {
      return null
    }

    const parsedState = JSON.parse(rawState)
    if (!parsedState || typeof parsedState !== 'object') {
      return null
    }

    return {
      scrollTop: Number.isFinite(parsedState.scrollTop) ? parsedState.scrollTop : 0,
      stickToBottom: Boolean(parsedState.stickToBottom)
    }
  } catch {
    return null
  }
}

function restoreScrollPosition(): void {
  const scrollState = loadScrollState()
  if (!scrollState) {
    return
  }

  const targetTop = scrollState.stickToBottom
    ? getMaxScrollTop()
    : Math.min(Math.max(0, scrollState.scrollTop), getMaxScrollTop())

  window.scrollTo(0, targetTop)
}

export function setupScrollMemory(): void {
  if (isScrollMemorySetup) {
    return
  }
  isScrollMemorySetup = true

  let saveTimer: number | null = null

  const scheduleSave = (): void => {
    if (saveTimer !== null) {
      return
    }

    saveTimer = window.setTimeout(() => {
      saveTimer = null
      saveScrollState()
    }, SAVE_THROTTLE_MS)
  }

  const runRestore = (): void => {
    restoreScrollPosition()
    window.setTimeout(restoreScrollPosition, FOLLOW_UP_RESTORE_DELAY_MS)
  }

  window.addEventListener('scroll', scheduleSave, { passive: true })
  window.addEventListener('beforeunload', saveScrollState)
  window.addEventListener('pagehide', saveScrollState)

  if (document.readyState === 'complete') {
    runRestore()
    return
  }

  window.addEventListener('load', runRestore, { once: true })
}
