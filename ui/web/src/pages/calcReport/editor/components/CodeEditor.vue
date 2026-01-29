<template>
  <!-- 将编辑器容器绑定到 ref -->
  <div class="full-height full-width" ref="editorElementRef"></div>
</template>

<script lang="ts" setup>
// 引入 Monaco Editor
import { monaco } from 'src/boot/monaco-editor'
import { registerUzoncalcProviders } from '../utils/uzoncalcCompletion'

// 创建对编辑器的引用
const editorElementRef = ref()
const monacoEditor = shallowRef<monaco.editor.IStandaloneCodeEditor>()
let providers: { dispose: () => void } | null = null

// 在组件挂载后执行
onMounted(() => {
  // 注册 uzoncalc 的智能提示
  providers = registerUzoncalcProviders()

  // 创建 Monaco Editor 实例
  monacoEditor.value = monaco.editor.create(editorElementRef.value, {
    // 设置初始代码值
    value: `from uzoncalc.utils import *

@uzon_calc()
def sheet():
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
  if (monacoEditor.value) {
    monacoEditor.value?.dispose()
    monacoEditor.value = undefined
  }
  if (providers) {
    providers.dispose()
  }
})

defineExpose({
  monacoEditor
})
</script>

<style lang="scss" scoped></style>
