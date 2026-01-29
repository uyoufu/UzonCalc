export default {
  // #region 全局通用
  global: {
    appName: 'UzonCalc',
    order: '序号',
    failed: '失败',
    success: '操作成功',
    confirm: '确认',
    cancel: '取消',
    modify: '修改',
    edit: '编辑',
    delete: '删除',
    new: '新增',
    add: '添加',
    confirmOperation: '操作确认',
    deleteConfirmation: '删除确认',
    warning: '警告',
    notice: '注意',
    cancelOperation: '取消操作',
    languageRequired: '语言是必填项',
    htmlContentRequired: 'Html 内容是必填项',
    deleteSuccess: '删除成功',
    updateSuccess: '更新成功',
    pleaseInputNumber: '请输入数字',
    import: '导入',
    importing: '导入中',
    export: '导出',
    exporting: '导出中',
    validate: '验证',
    validateMultiple: '批量验证',
    yes: '是',
    no: '否',
    empty: '无',
    save: '保存'
  },
  // #endregion

  // #region components
  components: {
    // 清空
    clear: '清空',
    // 移除已上传文件
    removeUploadedFile: '移除已上传文件',
    // 选择文件
    selectFile: '选择文件',
    // 上传
    upload: '上传',
    // 中止上传
    abortUpload: '中止上传',
    // 等待上传中...
    waitingForUpload: '等待上传中...',
    // 剩余
    remain: '剩余',
    // 正在计算 ${callbackData.file.name} 哈希值
    calculatingFileHash: '正在计算 {fileName} 哈希值',
    // 正在上传 ${file.name}
    uploadingFile: '正在上传 {fileName}'
  },
  // #endregion

  // #region search input 组件
  searchInput: {
    placeholder: '搜索'
  },
  // #endregion

  collapseLeft: {
    collapse: '折叠',
    expand: '展开'
  },

  collapseRight: {
    collapse: '折叠',
    expand: '展开'
  },

  // #region components 组件
  categoryList: {
    youCanRightClickToAddNewCategory: '您可以右键单击以添加新分类',
    newCategory: '新增分类',
    newCategorySuccess: '新增分类成功',
    onlyLettersNumbersUnderscoresAndCannotStartWithNumber: '仅支持字母、数字、下划线，且不能以数字开头',

    modifyCategory: '修改分类',
    deleteCategory: '删除分类',

    deleteCategoryConfirm: '您确定要删除分类 "{label}" 吗？此操作无法撤销。',
    deleteCategorySuccess: '删除分类 "{label}" 成功',

    field_name: '名称',
    field_icon: '图标',
    field_cover: '封面',
    field_total: '总数',
    field_order: '排序值',
    field_description: '描述'
  },
  // #endregion

  // #region utils
  utils: {
    // `... 等共 ${labels.length} ${unit}`
    totalItems: '... 等共 {count} {unit}',
    item: '项',

    // 未找到文件
    file_fileNotFound: '未找到文件',
    // 未检测到文件,可能是用户已取消
    file_noFileDetected: '未检测到文件,可能是用户已取消',
    // 指定 Worksheet
    file_specifyWorksheet: '指定 WorkSheet',
    // 请选择 Worksheet
    file_pleaseSelectWorksheet: '请选择 WorkSheet',
    // 字段 ${field} 不能为空
    file_fieldCannotBeEmpty: '字段 {field} 不能为空',
    // 严格模式下, mappers 不能为空
    file_mappersCannotBeEmptyInStrictMode: '严格模式下, mappers 不能为空',
    // 第 ${rowIndex} 行数据中，${map.headerName} 列不能为空
    file_fieldCannotBeEmptyAtRow: '第 {rowIndex} 行数据中，{field} 列不能为空',
    // 正在计算 hash 值...
    file_calculatingHash: '正在计算 hash 值...',
    // 文件 ${file.name} sha256 值为：
    file_fileHashCalculated: '文件 {fileName} sha256 值为：',
    // hash 已校验, 等待上传
    file_hashVerifiedWaitingUpload: 'hash 已校验, 等待上传',
    // 下载地址不合法,应以 http 开头
    file_invalidDownloadUrl: '下载地址不合法,应以 http 开头',
    // 正在解析文件...
    file_parsingFile: '正在解析文件...',
    // 下载完成
    file_downloadCompleted: '下载完成',
    // 下载失败
    file_downloadFailed: '下载失败',
    // ${fileHandle.name} 下载中...
    file_downloadingFile: '{fileName} 下载中...',
    // ${ext} 文件
    file_fileExtension: '{ext} 文件'
  },
  // #endregion

  // #region 路由
  routes: {
    sponsorAuthor: '支持作者',
    helpDoc: '帮助文档',
    startGuide: '使用说明',
    login: '用户登录',
    singlePages: '单页面',
    exception: '异常'
  },
  // #endregion

  // #region 按钮
  buttons: {
    new: '新增',
    newItem: '新增项',
    delete: '删除',
    deleteItem: '删除项',
    save: '保存',
    cancel: '取消',
    cancelCurrentOperation: '取消当前操作',
    export: '导出',
    exportData: '导出数据',
    import: '导入',
    importData: '导入数据',
    confirm: '确认',
    confirmCurrentOperation: '确认当前操作'
  },
  // #endregion

  // #region 登录页
  loginPage: {
    userName: '用户名',
    password: '密码',
    signIn: '登录',
    version: '版本',
    client: '客户端',
    server: '服务器',
    pleaseInputUserName: '请输入用户名',
    pleaseInputPassword: '请输入密码'
  },
  // #endregion

  // #region user
  userPage: {
    userInfo: '用户信息',
    profile: '个人资料'
  },
  // #endregion

  // #region 首页
  dashboardPage: {
    myFavorites: '我的收藏'
  },
  // #endregion

  // #region calcReport
  calcReportPage: {
    calcReport: '计算报告',

    newCalcReport: '新建计算',
    newCalcReportTooltip: '创建新的计算报告',

    defaultCalcReportName: 'new_calc_report',
    pleaseInputCalcReportName: '请输入计算报告名称(仅支持字母、数字、下划线，且不能以数字开头)',

    calcReportViewer: '查看计算'
  },

  calcModulePage: {
    calcModule: '计算模块'
  }
  // #endregion
}
