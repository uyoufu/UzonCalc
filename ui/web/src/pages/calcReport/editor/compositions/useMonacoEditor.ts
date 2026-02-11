// 引入 Monaco Editor
import { monaco } from 'src/boot/monaco-editor'
import { registerUzoncalcProviders } from '../utils/uzoncalcCompletion'

export function useMonacoEditor() {
  // 创建对编辑器的引用
  const monacoEditorElementRef = ref()
  const monacoEditorRef = shallowRef<monaco.editor.IStandaloneCodeEditor>()
  let providers: { dispose: () => void } | null = null

  // 在组件挂载后执行
  onMounted(() => {
    // 注册 uzoncalc 的智能提示
    providers = registerUzoncalcProviders()

    // 创建 Monaco Editor 实例
    monacoEditorRef.value = monaco.editor.create(monacoEditorElementRef.value, {
      // 设置初始代码值
      value: `from uzoncalc import *

@uzon_calc()
async def sheet():
    # 在此处编写计算逻辑
    width = 10
    height = 5
    area = width * height
`,
      // 设置语言为 Python
      language: 'python',
      theme: 'vs', // 可选主题: 'vs' (浅色), 'vs-dark' (深色), 'hc-black' (高对比度)
      automaticLayout: true, // 自动调整布局
      minimap: {
        enabled: false // 启用缩略图
      },
      fontSize: 14,
      tabSize: 4,
      scrollBeyondLastLine: false
    })
  })

  // 组件卸载时销毁编辑器实例
  onUnmounted(() => {
    // 异步执行 dispose，避免阻塞主线程
    if (monacoEditorRef.value) {
      monacoEditorRef.value?.dispose()
      monacoEditorRef.value = undefined
    }
    if (providers) {
      providers.dispose()
    }
  })

  return {
    monacoEditorElementRef,
    monacoEditorRef
  }
}
