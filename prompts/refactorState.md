# 重构状态表示

将 web 和 api 端所有的字符串状态表示都按编码风格重构为强类型，前端使用 as const 定义常量，python 端使用枚举代替字符串状态

## 关联文件

1. /home/gmx/dev/uzoncalc/src/web/src/api/calc/types.ts
2. /home/gmx/dev/uzoncalc/src/api/app/service