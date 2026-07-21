# 添加 new_version_doc.py 脚本

## 作用

该脚本用于从 git 历史中读取自上一个版本以来的所有提交，将这些提交的标题作为文档的发布说明更新到  /home/gmx/dev/uzoncalc/src/docs/src/downloads.md 和 /home/gmx/dev/uzoncalc/src/docs/src/en/downloads.md 中。

## 大致步骤

1. 从 git 历史中读取自上一个版本以来的所有提交，版本可以通过 tag 来确定
2. 然后将这些内容通过 opencode 生成不同语言的提交内容
3. 然后要求 opencode 调用脚本自动写入文档
4. 生成的内容要求要面向用户
5. 内容至少包含以下项，内容根据当前内容进行动态调整
6. 版本号、更新日期、下载地址在脚本内部自动生成，AI 只需要传入更新的内容部分即可

``` markdown
## 1.3.0

> 更新日期：2026-06-20

### 下载地址

[uzoncalc-win-x64-1.3.0.zip](https://oss.uzoncloud.com:2234/public/files/soft/uzoncalc-win-x64-1.3.0.zip)
```

## opencode 调用示例

参考文件: /home/gmx/dev/iepc/iepc-python/scripts/update_work_log.py

## 参考脚本

1. /home/gmx/dev/uzonmail/scripts/new-version-doc.ps1