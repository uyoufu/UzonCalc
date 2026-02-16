import { monaco } from 'src/boot/monaco-editor'
import { formatPythonByBlack } from 'src/api/codeFormat'

interface UzonCalcCompletion {
  label: string;
  kind: monaco.languages.CompletionItemKind;
  insertText: string;
  insertTextRules?: monaco.languages.CompletionItemInsertTextRule;
  detail?: string;
  documentation?: string;
}

export const uzoncalcCompletions: UzonCalcCompletion[] = [
  {
    label: 'uzon_calc',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'uzon_calc',
    detail: '@uzon_calc(name=None)',
    documentation: '计算装饰器，用于定义一个计算单页。它会自动处理公式插桩和上下文管理。'
  },
  {
    label: 'doc_title',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'doc_title(${1:title})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'doc_title(title: str)',
    documentation: '设置生成的 HTML 文档标题。'
  },
  {
    label: 'font_family',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "font_family('${1:Arial}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'font_family(family: str)',
    documentation: "设置页面字体。例如: 'Arial', 'Times New Roman'。"
  },
  {
    label: 'page_size',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "page_size('${1:A4}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'page_size(size: str)',
    documentation: "设置页面大小。例如: 'A4', 'Letter'。"
  },
  {
    label: 'style',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'style(${1:name}, ${2:value})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'style(name: str, value: dict)',
    documentation: '设置全局样式。'
  },
  {
    label: 'save',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'save(${1:filename})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'save(filename: str | None = None)',
    documentation: '保存当前文档为指定文件。'
  },
  {
    label: 'toc',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'toc(${1:title})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: "toc(title: str = 'Table of Contents')",
    documentation: '在当前位置插入目录。'
  },
  {
    label: 'show',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'show()',
    detail: 'show()',
    documentation: '启用内容录制（默认开启）。'
  },
  {
    label: 'hide',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'hide()',
    detail: 'hide()',
    documentation: '禁用内容录制，之后的计算过程将不显示在文档中。'
  },
  {
    label: 'enable_substitution',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'enable_substitution()',
    detail: 'enable_substitution()',
    documentation: '启用公式中的变量替换。'
  },
  {
    label: 'disable_substitution',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'disable_substitution()',
    detail: 'disable_substitution()',
    documentation: '禁用公式中的变量替换，仅显示原始公式。'
  },
  {
    label: 'unit',
    kind: monaco.languages.CompletionItemKind.Variable,
    insertText: 'unit',
    detail: 'unit (UnitRegistry)',
    documentation: '单位注册表，用于处理单位转换。'
  },
  {
    label: 'h',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "h('${1:tag}', children=${2:None})",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'h(tag, children, classes, props, persist, is_self_closing)',
    documentation: '创建 HTML 元素。'
  }
]

export function registerUzoncalcProviders() {
  // 注册代码提示
  const completionProvider = monaco.languages.registerCompletionItemProvider('python', {
    provideCompletionItems: (model, position) => {
      const word = model.getWordUntilPosition(position)
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn
      }

      const suggestions: monaco.languages.CompletionItem[] = uzoncalcCompletions.map((item) => ({
        label: item.label,
        kind: item.kind,
        insertText: item.insertText,
        insertTextRules: item.insertTextRules,
        detail: item.detail,
        documentation: item.documentation,
        range: range
      }))

      return {
        suggestions: suggestions
      }
    }
  })

  // 注册悬停提示
  const hoverProvider = monaco.languages.registerHoverProvider('python', {
    provideHover: (model, position) => {
      const word = model.getWordAtPosition(position)
      if (!word) return null

      const found = uzoncalcCompletions.find((item) => item.label === word.word)

      if (found) {
        return {
          range: new monaco.Range(
            position.lineNumber,
            word.startColumn,
            position.lineNumber,
            word.endColumn
          ),
          contents: [
            { value: `**${found.label}**` },
            { value: found.detail || '' },
            { value: found.documentation || '' }
          ]
        }
      }
      return null
    }
  })

  // 注册代码格式化
  const formatProvider = monaco.languages.registerDocumentFormattingEditProvider('python', {
    provideDocumentFormattingEdits: async (model) => {
      try {
        const sourceCode = model.getValue()
        const result = await formatPythonByBlack({
          code: sourceCode
        })

        const formattedCode = result.data?.formattedCode
        if (!formattedCode || formattedCode === sourceCode) {
          return []
        }

        return [
          {
            range: model.getFullModelRange(),
            text: formattedCode
          }
        ]
      } catch {
        return []
      }
    }
  })

  return {
    dispose: () => {
      completionProvider.dispose()
      hoverProvider.dispose()
      formatProvider.dispose()
    }
  }
}
