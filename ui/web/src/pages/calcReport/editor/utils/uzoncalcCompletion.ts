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
  // 核心装饰器和运行函数
  {
    label: 'uzon_calc',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'uzon_calc',
    detail: '@uzon_calc(name=None)',
    documentation: '计算装饰器，用于定义一个计算单页。它会自动处理公式插桩和上下文管理。'
  },
  {
    label: 'run',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'run(${1:func})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'async run(func, *args, defaults=None, is_silent=True, **kwargs)',
    documentation: '异步运行被 @uzon_calc 装饰的函数。支持传入默认值和执行模式设置。'
  },
  {
    label: 'run_sync',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'run_sync(${1:func})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'run_sync(func, *args, defaults=None, **kwargs)',
    documentation: '同步执行异步函数（静默模式）。使用 asyncio.run() 执行，UI 调用将返回默认值。'
  },
  {
    label: 'get_current_instance',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'get_current_instance()',
    detail: 'get_current_instance() -> CalcContext',
    documentation: '获取当前的 CalcContext 实例。'
  },
  {
    label: 'CalcContext',
    kind: monaco.languages.CompletionItemKind.Class,
    insertText: 'CalcContext',
    detail: 'class CalcContext',
    documentation: '计算上下文类，管理文档内容、选项和状态。'
  },

  // 文档设置
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

  // 显示控制
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

  // 变量替换
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

  // F-string 等式
  {
    label: 'enable_fstring_equation',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'enable_fstring_equation()',
    detail: 'enable_fstring_equation()',
    documentation: '启用 f-string 等式渲染。'
  },
  {
    label: 'disable_fstring_equation',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'disable_fstring_equation()',
    detail: 'disable_fstring_equation()',
    documentation: '禁用 f-string 等式渲染。'
  },

  // 行内模式
  {
    label: 'inline',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'inline(${1:" "})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'inline(separator: str = " ")',
    documentation: '开始行内模式，多个表达式将在同一行显示，使用指定的分隔符连接。'
  },
  {
    label: 'endline',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'endline()',
    detail: 'endline()',
    documentation: '结束行内模式，恢复正常的换行显示。'
  },

  // 别名
  {
    label: 'alias',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'alias(${1:name}, ${2:value})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'alias(name: str, value: str)',
    documentation: '定义变量符号别名，用于在渲染时将变量名替换为指定的符号。'
  },

  // 单位
  {
    label: 'unit',
    kind: monaco.languages.CompletionItemKind.Variable,
    insertText: 'unit',
    detail: 'unit (UnitRegistry)',
    documentation: '单位注册表，用于处理单位转换。'
  },

  // HTML 元素
  {
    label: 'h',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "h('${1:tag}', children=${2:None})",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'h(tag, children, classes, props, persist, is_self_closing)',
    documentation: '创建 HTML 元素。'
  },
  {
    label: 'Props',
    kind: monaco.languages.CompletionItemKind.Class,
    insertText: 'Props',
    detail: 'class Props',
    documentation: 'HTML 元素属性类，支持标准 HTML 属性和自定义属性。'
  },
  {
    label: 'props',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'props(${1:})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'props(**kwargs) -> Props',
    documentation: '创建 Props 实例的便捷函数，支持 id、classes、styles 等属性。'
  },

  // 标题
  {
    label: 'title',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "title('${1:text}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'title(text: str, classes=None, persist=False)',
    documentation: '创建文档标题（大号、粗体、居中）。'
  },
  {
    label: 'Title',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "Title('${1:text}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'Title(text: str, classes=None)',
    documentation: '创建文档标题并添加到文档（大号、粗体、居中）。'
  },
  {
    label: 'subtitle',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "subtitle('${1:text}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'subtitle(text: str, classes=None, persist=False)',
    documentation: '创建文档副标题（粗体、居中）。'
  },
  {
    label: 'Subtitle',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "Subtitle('${1:text}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'Subtitle(text: str, classes=None)',
    documentation: '创建文档副标题并添加到文档（粗体、居中）。'
  },

  // 标题级别 h1-h6
  {
    label: 'h1',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "h1('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'h1(content, classes=None, props=None, persist=False)',
    documentation: '创建一级标题。'
  },
  {
    label: 'H1',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "H1('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'H1(content, classes=None, props=None)',
    documentation: '创建一级标题并添加到文档。'
  },
  {
    label: 'h2',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "h2('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'h2(content, classes=None, props=None, persist=False)',
    documentation: '创建二级标题。'
  },
  {
    label: 'H2',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "H2('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'H2(content, classes=None, props=None)',
    documentation: '创建二级标题并添加到文档。'
  },
  {
    label: 'h3',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "h3('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'h3(content, classes=None, props=None, persist=False)',
    documentation: '创建三级标题。'
  },
  {
    label: 'H3',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "H3('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'H3(content, classes=None, props=None)',
    documentation: '创建三级标题并添加到文档。'
  },
  {
    label: 'h4',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "h4('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'h4(content, classes=None, props=None, persist=False)',
    documentation: '创建四级标题。'
  },
  {
    label: 'H4',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "H4('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'H4(content, classes=None, props=None)',
    documentation: '创建四级标题并添加到文档。'
  },
  {
    label: 'h5',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "h5('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'h5(content, classes=None, props=None, persist=False)',
    documentation: '创建五级标题。'
  },
  {
    label: 'H5',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "H5('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'H5(content, classes=None, props=None)',
    documentation: '创建五级标题并添加到文档。'
  },
  {
    label: 'h6',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "h6('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'h6(content, classes=None, props=None, persist=False)',
    documentation: '创建六级标题。'
  },
  {
    label: 'H6',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "H6('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'H6(content, classes=None, props=None)',
    documentation: '创建六级标题并添加到文档。'
  },

  // 段落和容器
  {
    label: 'p',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "p('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'p(content, classes=None, props=None, persist=False)',
    documentation: '创建段落。'
  },
  {
    label: 'P',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "P('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'P(content, classes=None, props=None)',
    documentation: '创建段落并添加到文档。'
  },
  {
    label: 'div',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "div('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'div(content, classes=None, props=None, persist=False)',
    documentation: '创建 div 容器。'
  },
  {
    label: 'Div',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "Div('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'Div(content, classes=None, props=None)',
    documentation: '创建 div 容器并添加到文档。'
  },
  {
    label: 'span',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "span('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'span(content, classes=None, props=None, persist=False)',
    documentation: '创建行内元素 span。'
  },
  {
    label: 'Span',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "Span('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'Span(content, classes=None, props=None)',
    documentation: '创建行内元素 span 并添加到文档。'
  },
  {
    label: 'br',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'br()',
    detail: 'br()',
    documentation: '创建换行符。'
  },
  {
    label: 'Br',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'Br()',
    detail: 'Br()',
    documentation: '创建换行符并添加到文档。'
  },
  {
    label: 'row',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "row('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'row(content, classes=None, props=None, persist=False, tag="div")',
    documentation: '创建行容器。'
  },
  {
    label: 'Row',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "Row('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'Row(content, classes=None, props=None, tag="div")',
    documentation: '创建行容器并添加到文档。'
  },

  // 图片
  {
    label: 'img',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "img('${1:src}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'img(src, classes=None, alt=None, width=None, height=None, props=None, persist=False)',
    documentation: '创建图片元素。'
  },
  {
    label: 'Img',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "Img('${1:src}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'Img(src, classes=None, alt=None, width=None, height=None, props=None)',
    documentation: '创建图片元素并添加到文档。'
  },

  // 表格
  {
    label: 'table',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'table(${1:headers}, ${2:rows})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'table(headers, rows, classes=None, title=None, props=None, persist=False)',
    documentation: '创建表格。headers 和 rows 可以是列表或列表的列表。'
  },
  {
    label: 'Table',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'Table(${1:headers}, ${2:rows})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'Table(headers, rows, classes=None, title=None, props=None)',
    documentation: '创建表格并添加到文档。headers 和 rows 可以是列表或列表的列表。'
  },
  {
    label: 'th',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "th('${1:value}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'th(value, classes=None, rowspan=1, colspan=1)',
    documentation: '创建表格表头单元格。'
  },
  {
    label: 'tr',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "tr('${1:value}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'tr(value, classes=None)',
    documentation: '创建表格行。'
  },
  {
    label: 'td',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "td('${1:value}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'td(value, classes=None)',
    documentation: '创建表格数据单元格。'
  },

  // 输入
  {
    label: 'input',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "input('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'input(content, persist=False)',
    documentation: '创建输入框元素。'
  },
  {
    label: 'Input',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "Input('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'Input(content)',
    documentation: '创建输入框元素并添加到文档。'
  },

  // 代码
  {
    label: 'code',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "code('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'code(content, language=None)',
    documentation: '创建代码块，支持语法高亮。'
  },
  {
    label: 'Code',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "Code('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'Code(content, language=None)',
    documentation: '创建代码块并添加到文档，支持语法高亮。'
  },

  // 信息框
  {
    label: 'info',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "info('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'info(content, persist=False)',
    documentation: '创建蓝色信息提示框。'
  },
  {
    label: 'Info',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "Info('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'Info(content)',
    documentation: '创建蓝色信息提示框并添加到文档。'
  },

  // LaTeX
  {
    label: 'laTex',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "laTex('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'laTex(content, persist=False)',
    documentation: '渲染 LaTeX 数学公式（转换为 MathML 格式）。'
  },
  {
    label: 'LaTex',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "LaTex('${1:content}')",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'LaTex(content)',
    documentation: '渲染 LaTeX 数学公式并添加到文档（转换为 MathML 格式）。'
  },

  // 绘图
  {
    label: 'plot',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'plot(${1:fig})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'plot(fig: Figure, width=None, persist=False)',
    documentation: '创建 matplotlib 图表的嵌入式图片。'
  },
  {
    label: 'Plot',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: 'Plot(${1:fig})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'Plot(fig: Figure | bytes, width=None)',
    documentation: '创建 matplotlib 图表的嵌入式图片并添加到文档。'
  },

  // UI 交互
  {
    label: 'UI',
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: "UI('${1:title}', [${2:fields}])",
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'async UI(title: str, fields: list[Field], caption=None)',
    documentation: '定义 UI 交互窗口，返回用户输入的值字典。在静默模式下返回默认值。'
  },
  {
    label: 'Field',
    kind: monaco.languages.CompletionItemKind.Class,
    insertText: 'Field(name=${1:name}, label=${2:label})',
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: 'class Field',
    documentation: 'UI 字段定义类，用于创建表单字段。支持 text、number、selectOne、selectMany、checkbox、textarea 等类型。'
  },
  {
    label: 'FieldType',
    kind: monaco.languages.CompletionItemKind.Class,
    insertText: 'FieldType',
    detail: 'class FieldType',
    documentation: '字段类型枚举：text, number, selectOne, selectMany, checkbox, textarea。'
  },
  {
    label: 'Window',
    kind: monaco.languages.CompletionItemKind.Class,
    insertText: 'Window',
    detail: 'class Window',
    documentation: 'UI 窗口定义类，包含标题、字段列表和说明文字。'
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
