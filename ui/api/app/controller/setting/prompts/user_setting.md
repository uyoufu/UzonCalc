根据 app/db/models/user_setting.py 文件，在 `app/controller/setting/user_setting.py` 中创建对应的 API 接口，允许用户保存和获取个人设置。接口包括：

1. GET /api/v1/user_settings/{key}: 根据 key 获取用户设置数据
2. PUT /api/v1/user_settings/{key}: 更新用户设置数据，若不存在则创建
3. DELETE /api/v1/user_settings/{key}: 删除用户设置数据

然后在前端 #file:userSetting.ts 中完成对上述接口的调用
