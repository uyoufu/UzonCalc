# 编写一个脚本，用于更新项目的版本号

## 要求

1. 编写一个 python 脚本，保存到 scripts/ 目录下，用于更新项目的版本号
2. 需要修改的版本号文件包括:

**Web**
  - /home/gmx/dev/uzoncalc/src/web/package.json version
  - /home/gmx/dev/uzoncalc/src/web/src/config/app.config.ts version
  
**API**
  - /home/gmx/dev/uzoncalc/src/api/pyproject.toml version
  - /home/gmx/dev/uzoncalc/src/api/config/app.ini version

**Core**
  - /home/gmx/dev/uzoncalc/src/core/pyproject.toml version

## 实现效果

1. 执行后，分别从 git 中收集这 3 个子项目的自上一次版本提交后的文件变更记录，上一次的提交记录可以在项目根下保存
2. 若存在变更，则版本号 +1，否则保持不变
3. 以一个列表的形式输出，供用户确认，以不同的颜色区分存在变更项，还要显示变更的提交数量
4. 用户可以取消某些项目的版本升迁，只对需要升迁的项目进行版本号更新