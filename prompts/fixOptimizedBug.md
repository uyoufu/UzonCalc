# 修复一些已知 Bug

对以下 Bug 进行修复：

## 首页不正确

1. 登录后，进入首页时，标签显示 “共享计算书”，按预期，应显示 “计算报告” 页面

## 计算报告优化

### 工作区

1. 左侧目录树右键菜单中，“复制引用” 应根据文件不同，显示不同的引用格式，若是 python 文件，引用格式为 `from a.b.c import *`, 其它文件为路径
2. 左侧目录树中，设为入口应检查文件中是否包含 @uzon_calc 装饰器

### 运行逻辑优化

1. 允许工作区中的 python 文件可以相对引用导入，目前使用相对引用时，运行会报错：`ImportError: attempted relative import with no known parent package`
2. 工作区中的各个编辑标签应像 vscode 一样，支持引用跳转，对新增的文件，能够智能提示

### 分享计算书弹窗优化

1. 支持修改既有分享链接的设置，可以重新设置分享的信息
2. 分享添加允许添加备注信息并显示
3. 整个组件输入布局要优化，输入用户左侧与版本输入左侧没有对齐;允许编辑区域入侵到了上一个组件中
4. 链接分享的结果中，增加一键复制链接的功能

### 共享计算书列表显示优化

1. 共享计算书列表中，增加权限列显示，显示可编辑、可分享等权限
2. 将计算书名称中显示的分享人拆分到单独的列中显示

### 计算书导出优化

1. 计算书导出时，复用内核中的 /home/gmx/dev/uzoncalc/src/core/uzoncalc/cli_core/cli_thumbnail.py 相关逻辑，生成计算书缩略图，可能要对 cli_thumbnail 进行抽象
2. 修复导出的计算书在运行运算时报错, 错误如下：

``` bash
uv run 未命名计算书.png
Using CPython 3.12.3 interpreter at: /usr/bin/python3.12
Removed virtual environment at: .venv
Creating virtual environment at: .venv
  × No solution found when resolving dependencies for split (markers: python_full_version ==
  │ '3.12.*' and sys_platform == 'win32'):
  ╰─▶ Because the requested Python version (>=3.12) does not satisfy Python>=3.13 and
      uzoncalc==1.3.3 depends on Python>=3.13, we can conclude that uzoncalc==1.3.3 cannot be
      used.
      And because only uzoncalc==1.3.3 is available and your project depends on uzoncalc, we can
      conclude that your project's requirements are unsatisfiable.

hint: The resolution failed for an environment that is not the current one, consider limiting the environments with `tool.uv.environments`.
hint: The `requires-python` value (>=3.12) includes Python versions that are not supported by your dependencies (e.g., uzoncalc==1.3.3 only supports >=3.13). Consider using a more restrictive `requires-python` value (like >=3.13).%
```

### 计算书导入优化

1. 当导入使用 /home/gmx/dev/uzoncalc/src/core/uzoncalc/cli_core/cli_archive.py 生成的 png 文件时，报错 `Invalid v3 report archive: 归档格式版本不受支持`
2. 当选中分类导入时，应将其作为默认分类
