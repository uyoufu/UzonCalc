# Calculation Instance List Page

实现一个计算实例列表页面，用于展示和管理用户的计算实例。

## 前端 ui/web

### 页面设计

在 ui/web/src/pages/calcReportInstance/list/InstanceList.vue 中实现页面，页面风格与功能参考 ui/web/src/pages/calcReport/list/CalcReportList.vue

**右键功能**

- 可跳转到查看计算查看结果

### 查看计算

在"查看计算"页面，当"执行计算"按钮执行完成后，显示保存为"计算实例"的选项，用户可以选择将当前计算结果保存为一个新的计算实例。
若计算已经是一个实例，则保存在当前实例中

## 后端 ui/api

**数据库**

数据库参考 api/app/db/models/calc_report_archive.py 和 api/app/db/models/calc_report_category.py 设计。需要新增的表为：
- `calc_report_instance`
- `calc_report_instance_category`
