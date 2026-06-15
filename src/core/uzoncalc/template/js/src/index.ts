import { setupContentPatchMessaging } from './contentUpdater'
import { setupScrollMemory } from './scrollMemory'
import { ensureTemplateStyles } from './styleInjector'
import { generateToc } from './toc'
import { setupOutlinePreview } from './outlinePreview'
import { applyFigureLabels } from './figureLabels'

declare const hljs: { highlightAll?: () => void } | undefined

function rerunHighlight(): void {
  // 正文替换后重新执行代码高亮，兼容无 highlight.js 的离线测试环境
  if (typeof hljs !== 'undefined' && typeof hljs.highlightAll === 'function') {
    hljs.highlightAll()
  }
}

function bootstrap(): void {
  // 初始化时确保模板样式已注入
  // 该操作是幂等的
  ensureTemplateStyles()
  // 正文变化后刷新依赖 DOM 内容的增强能力
  applyFigureLabels()
  generateToc()
  setupOutlinePreview()
  rerunHighlight()
  setupScrollMemory()
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootstrap, { once: true })
} else {
  bootstrap()
}

setupContentPatchMessaging(bootstrap)
