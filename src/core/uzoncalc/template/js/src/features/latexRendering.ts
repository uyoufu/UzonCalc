interface KatexRuntime {
  render(
    source: string,
    element: Element,
    options: {
      displayMode: boolean
      throwOnError: boolean
      output: string
    }
  ): void
}

/** 使用 KaTeX 渲染模板中的独立 LaTeX 标签。 */
export function renderLatexElements(): void {
  const katexRuntime = (window as unknown as { katex?: KatexRuntime }).katex
  if (!katexRuntime) {
    return
  }

  const latexElements = document.querySelectorAll('latex.latex')
  latexElements.forEach((element) => {
    katexRuntime.render(element.textContent || '', element, {
      displayMode: true,
      throwOnError: false,
      output: 'htmlAndMathml'
    })
  })
}
