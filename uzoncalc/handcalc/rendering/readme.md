# rendering 模块说明
  
定义了把 MathIR 转成最终展示内容的渲染器，供 `steps.py` 调用。核心职责是把 MathIR 与运行时值组合成最终展示内容，包括变量替换、数组样式修正、赋值左右侧拼接、f-string 混排和数值格式化，并输出 MathML 或 HTML 片段。