# 开发文档

## uv 操作

**为单个子项添加依赖**

```bash
uv add pint --project ./uzoncalc
```

**同步核心包环境**

```bash
uv sync --package uzoncalc --no-default-groups
```

**同步根目录预览服务环境**

```bash
uv sync --group preview
```
