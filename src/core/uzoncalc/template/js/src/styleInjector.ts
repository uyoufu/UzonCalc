import { templateStyles } from './styles'

const STYLE_ATTRIBUTE = 'data-uzoncalc-template'

export function ensureTemplateStyles(): void {
  const headElement = document.head
  if (!headElement) {
    return
  }

  if (headElement.querySelector(`style[${STYLE_ATTRIBUTE}]`)) {
    return
  }

  const styleElement = document.createElement('style')
  styleElement.setAttribute(STYLE_ATTRIBUTE, 'true')
  styleElement.textContent = templateStyles

  // 模板主题样式需要晚于 Tailwind reset，确保基础元素样式最终生效。
  headElement.appendChild(styleElement)
}
