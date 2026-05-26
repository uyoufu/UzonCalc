# UzonCalc

## 目录介绍

- src
  - core/uzoncalc: 计算引擎核心
  - api: 界面的后端 api
  - web: 界面的前端
    - src-tauri: Tauri 应用，用于将 web 目录下的文件打包到桌面应用中

## Agents

在开发某些模块时，提前读取对应目录下的 AGENTS.md 文件，了解开发规范, 其中包含 AGENTS.md 文件的目录如下：

| 项目/目录         | Agent                       |
| ----------------- | --------------------------- |
| src/core/uzoncalc | src/core/uzoncalc/AGENTS.md |
| src/api           | src/api/AGENTS.md           |
| src/web           | src/web/AGENTS.md           |
