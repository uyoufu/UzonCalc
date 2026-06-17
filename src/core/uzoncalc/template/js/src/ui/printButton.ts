const PRINT_BUTTON_SELECTOR = '.uz-print-button'
const PRINT_BUTTON_LOADING_ATTRIBUTE = 'data-loading'
const PRINT_BUTTON_DEFAULT_LABEL = '打印文档'
const PRINT_BUTTON_LOADING_LABEL = '正在准备打印'
const PRINT_BUTTON_ICON = '🖨️'

/** 查找模板打印按钮。 */
export function resolvePrintButton(): HTMLButtonElement | null {
  return document.querySelector<HTMLButtonElement>(PRINT_BUTTON_SELECTOR)
}

/** 切换打印按钮的等待态，加载时只显示 spinner。 */
export function setPrintButtonLoading(
  printButton: HTMLButtonElement,
  isLoading: boolean
): void {
  printButton.disabled = isLoading
  if (isLoading) {
    printButton.setAttribute(PRINT_BUTTON_LOADING_ATTRIBUTE, 'true')
  } else {
    printButton.removeAttribute(PRINT_BUTTON_LOADING_ATTRIBUTE)
  }
  printButton.setAttribute(
    'aria-label',
    isLoading ? PRINT_BUTTON_LOADING_LABEL : PRINT_BUTTON_DEFAULT_LABEL
  )
  printButton.textContent = isLoading ? '' : PRINT_BUTTON_ICON
}
