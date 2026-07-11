# uzoncalc api

为 uzoncalc web 端提供 api 接口，开发时需要遵循以下要求：

## 多语言

controller 和 service 层中，对前端所有的返回值都应进行多语言适配，使用 `ui/api/app/i18n.py` 中的 `_(message:str)` 函数

## Codegraph 代码图
