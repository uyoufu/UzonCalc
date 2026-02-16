import type { ICascadeMenuActionItem } from 'src/components/cascadeMenu/types'
import type { monaco } from 'src/boot/monaco-editor'
import { t } from 'src/i18n/helpers'
import type { ShallowRef } from 'vue'

interface ISnippetController {
  insert: (template: string) => void
}

interface IMenuSnippetConfig {
  label: string
  snippet: string
}

function normalizeSnippetToPlainText(snippet: string) {
  return snippet
    .replace(/\$\{\d+:([^}]*)\}/g, '$1')
    .replace(/\$\{\d+\}/g, '')
    .replace(/\$\d+/g, '')
}

function insertSnippet(editor: monaco.editor.IStandaloneCodeEditor, snippet: string) {
  const snippetController = editor.getContribution('snippetController2') as ISnippetController | null
  if (snippetController && typeof snippetController.insert === 'function') {
    snippetController.insert(snippet)
    return
  }

  const model = editor.getModel()
  const position = editor.getPosition()
  if (!model || !position) return

  const plainText = normalizeSnippetToPlainText(snippet)

  model.applyEdits([
    {
      range: {
        startLineNumber: position.lineNumber,
        startColumn: position.column,
        endLineNumber: position.lineNumber,
        endColumn: position.column
      },
      text: plainText
    }
  ])
}

function createSnippetItem(
  editorRef: ShallowRef<monaco.editor.IStandaloneCodeEditor | undefined>,
  label: string,
  snippet: string
): ICascadeMenuActionItem {
  return {
    label,
    onClick: () => {
      const editor = editorRef.value
      if (!editor) return

      editor.focus()
      insertSnippet(editor, snippet)
    }
  }
}

function createSnippetItems(
  editorRef: ShallowRef<monaco.editor.IStandaloneCodeEditor | undefined>,
  configs: IMenuSnippetConfig[]
) {
  return configs.map((item) => createSnippetItem(editorRef, item.label, item.snippet))
}

export function useMenubar(editorRef: ShallowRef<monaco.editor.IStandaloneCodeEditor | undefined>) {
  const elementsConfig: IMenuSnippetConfig[] = [
    { label: t('calcReportPage.editor.menubar.elements.title'), snippet: 'Title(${1:text})' },
    { label: t('calcReportPage.editor.menubar.elements.subtitle'), snippet: 'Subtitle(${1:text})' },
    { label: t('calcReportPage.editor.menubar.elements.h'), snippet: 'H(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.h1'), snippet: 'H1(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.h2'), snippet: 'H2(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.h3'), snippet: 'H3(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.h4'), snippet: 'H4(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.h5'), snippet: 'H5(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.h6'), snippet: 'H6(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.p'), snippet: 'P(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.div'), snippet: 'Div(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.span'), snippet: 'Span(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.br'), snippet: 'Br()' },
    { label: t('calcReportPage.editor.menubar.elements.row'), snippet: 'Row(${1:content}, tag=${2:"div"})' },
    { label: t('calcReportPage.editor.menubar.elements.img'), snippet: 'Img(${1:src}, alt=${2:alt}, width=${3:None}, height=${4:None})' },
    {
      label: t('calcReportPage.editor.menubar.elements.table'),
      snippet: 'Table(\n    headers=${1:headers},\n    rows=${2:rows},\n    title=${3:None}\n)'
    },
    { label: t('calcReportPage.editor.menubar.elements.input'), snippet: 'Input(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.code'), snippet: 'Code(${1:content}, language=${2:None})' },
    { label: t('calcReportPage.editor.menubar.elements.info'), snippet: 'Info(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.latex'), snippet: 'LaTex(${1:content})' },
    { label: t('calcReportPage.editor.menubar.elements.plot'), snippet: 'Plot(${1:fig}, width=${2:None})' }
  ]

  const optionsConfig: IMenuSnippetConfig[] = [
    { label: t('calcReportPage.editor.menubar.options.show'), snippet: 'show()' },
    { label: t('calcReportPage.editor.menubar.options.hide'), snippet: 'hide()' },
    { label: t('calcReportPage.editor.menubar.options.enableSubstitution'), snippet: 'enable_substitution()' },
    { label: t('calcReportPage.editor.menubar.options.disableSubstitution'), snippet: 'disable_substitution()' },
    { label: t('calcReportPage.editor.menubar.options.enableFStringEquation'), snippet: 'enable_fstring_equation()' },
    { label: t('calcReportPage.editor.menubar.options.disableFStringEquation'), snippet: 'disable_fstring_equation()' },
    { label: t('calcReportPage.editor.menubar.options.inline'), snippet: 'inline(${1:separator})' },
    { label: t('calcReportPage.editor.menubar.options.endline'), snippet: 'endline()' },
    { label: t('calcReportPage.editor.menubar.options.alias'), snippet: 'alias(${1:name}, ${2:value})' }
  ]

  const elementsSnippetItems = createSnippetItems(editorRef, elementsConfig)
  const optionsSnippetItems = createSnippetItems(editorRef, optionsConfig)

  const insertMenuItems: ICascadeMenuActionItem[] = [
    {
      label: t('calcReportPage.editor.menubar.groups.elements'),
      children: elementsSnippetItems
    },
    {
      label: t('calcReportPage.editor.menubar.groups.options'),
      children: optionsSnippetItems
    }
  ]

  return {
    insertMenuItems
  }
}
