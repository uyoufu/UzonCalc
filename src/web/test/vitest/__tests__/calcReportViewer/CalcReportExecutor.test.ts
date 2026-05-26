import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const projectRoot = resolve(__dirname, '../../../..')
const executorPath = resolve(projectRoot, 'src/pages/calcReport/viewer/CalcReportExecutor.vue')
const codePreviewerPath = resolve(projectRoot, 'src/pages/calcReport/editor/components/CodePreviewer.vue')

function readVueSource(filePath: string) {
  // 直接读取源码，避免当前测试入口未加载 Vue SFC 插件导致组件挂载失败
  return readFileSync(filePath, 'utf-8')
}

describe('CalcReportExecutor 复用结构', () => {
  it('执行器提供编辑器复用所需的最小控制参数', () => {
    const source = readVueSource(executorPath)

    expect(source).toContain('isVerticalLayout')
    expect(source).toContain('autoCollapseInputUis')
    expect(source).toContain('disableHeader')
    expect(source).toContain('disableButtons')
    expect(source).toContain('defineExpose')
  })

  it('代码预览器复用执行器而不是重复渲染输入表单和 iframe', () => {
    const source = readVueSource(codePreviewerPath)

    expect(source).toContain('CalcReportExecutor')
    expect(source).not.toContain('CalcInputForm')
    expect(source).not.toContain('<iframe')
  })

  it('执行器通过 postMessage 增量更新 iframe 正文', () => {
    const source = readVueSource(executorPath)

    expect(source).toContain('ref="reportIframeRef"')
    expect(source).toContain('postMessage')
    expect(source).toContain('uzoncalc:update-content')
    expect(source).toContain('iframeSrc')
    expect(source).toContain('contentHtml')
    expect(source).not.toContain('baseUrl')
    expect(source).not.toContain('buildPatchBaseUrl')
  })
})
