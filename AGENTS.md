# UzonCalc

## 目录介绍

- src
  - core/uzoncalc: 计算引擎核心
  - api: 界面的后端 api
  - web: 界面的前端
    - src-tauri: Tauri 应用，用于将 web 目录下的文件打包到桌面应用中

## Agents

在开发对应子项时，提前读取对应目录下的 AGENTS.md 文件，了解开发规范, 其中包含 AGENTS.md 文件的目录如下：

| 项目/目录         | Agent                       |
| ----------------- | --------------------------- |
| src/core/uzoncalc | src/core/uzoncalc/AGENTS.md |
| src/api           | src/api/AGENTS.md           |
| src/web           | src/web/AGENTS.md           |

## Scripts

- 编写脚本时，默认使用 python, 且使用 rich 库进行输出美化

## 测试

测试文件应分类保存在各个项目的 tests/ 下的子目录中

### Codex 后台测试环境

- Codex 隔离沙箱中，Python `asyncio` 从后台线程通过 `loop.call_soon_threadsafe()` 唤醒主事件循环可能失效。依赖该路径的 `aiosqlite` 和默认 `ThreadPoolExecutor` 会使测试无输出地卡住。
- 若包含上述依赖的测试在后台运行至超时，先使用隔离环境外的执行权限重新运行相同命令；不要据此降级依赖或修改业务代码。`pytest -q` 在测试结束前通常没有可见输出，可临时加 `-vv -s` 观察卡点。
- 需要强制终止诊断命令时使用 `timeout -k 3 <seconds> ...`，确保超时后的子进程也会退出。
