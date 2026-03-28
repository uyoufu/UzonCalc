在 `ui/desktop/scrips/` 中创建一个部署脚本，可以指定平台（Windows、macOS、Linux），脚本会执行以下操作，以 windows 为例：

- 在 `publish` 目录下创建一个新的文件夹，命名为 `windows`，用于存放 Windows 平台的发布文件
- 将 `ui/desktop` 目录下的所有文件复制到 `publish/windows` 中
- 在 `publish/windows` 中安装 python 的 embedded 版本
- 将 `uzoncalc`、`ui/api` 复制到 `publish/windows` 中
- 为 embedded python 安装 `requirements.txt` 中的依赖, 每个项目下都有对应的 `requirements.txt`，需要分别安装
- 在 `publish/windows` 中创建一个 `start.bat` 脚本，用于启动 `desktop/app.py`
- 切换到 `ui/web` 目录，执行 `npm run build`，将构建好的文件从 `dist/spa` 复制到 `publish/windows/api/data/www` 中 