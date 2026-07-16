export default {
  // #region 全局通用
  global: {
    appName: 'UzonCalc',
    order: '序号',
    failed: '失败',
    success: '操作成功',
    confirm: '确认',
    cancel: '取消',
    view: '查看',
    version: '版本',
    lastModified: '最后修改时间',
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

  calcWorkspace: {
    categories: '计算书分类', newCategory: '新建分类', editCategory: '编辑分类', categoryName: '分类',
    allReports: '全部计算书', newReport: '新建计算书', untitledReport: '未命名计算书', reportName: '计算书名称',
    description: '描述', searchReports: '搜索计算书', latestVersion: '最新版本', state: '状态',
    openWorkspace: '打开工作区', runLatest: '运行最新版本', editMetadata: '编辑信息', toggleFavorite: '切换收藏',
    copyReport: '复制计算书', share: '分享', shareReport: '分享计算书', showInExplorer: '在文件管理器中显示',
    importUzc: '导入 .uzc', uzcFile: '.uzc 文件', importComplete: '导入完成', metadataRequired: '请填写分类和计算书名称',
    workspace: '工作区', run: '运行', versionsAndShares: '版本与分享', backToReports: '返回计算书列表', desktopRequired: '工作区编辑仅支持桌面端',
    saveWorkspace: '保存完整工作区', workspaceSaved: '工作区已保存', saved: '已保存', unsaved: '有未保存修改',
    newFile: '新建文件', uploadResources: '上传资源', dependencies: '依赖', selectFile: '选择文件开始编辑',
    rename: '重命名', setEntry: '设为入口', format: '格式化 Python', download: '下载', binaryResource: '二进制资源',
    runWorkspace: '保存并运行工作区', alias: '依赖别名', targetReport: '目标计算书', selectors: '版本选择器', defaultSelector: '默认选择器',
    revisionConflict: '工作区版本冲突', revisionConflictMessage: '服务器工作区已被其他请求修改。本地内容仍然保留。',
    exportLocalZip: '导出本地 ZIP', discardAndReload: '放弃本地修改并重新加载', leaveWithoutSaving: '离开后未保存修改将丢失。',
    executionSource: '执行来源', sourceWorkspace: '工作区', sourceLatest: '最新发布版本', sourceVersion: '指定版本',
    silentRun: '使用默认值直接运行', startRun: '开始运行', continueRun: '继续运行', terminate: '终止执行',
    runToPreview: '运行后在此预览结果', noInputs: '当前步骤没有输入项', backend: '执行后端', startedAt: '开始时间',
    buildWaiting: '执行产物正在构建，完成后即可重试', buildReady: '执行产物已构建完成', buildFailed: '执行产物构建失败',
    saveInstance: '保存计算实例', instanceName: '实例名称', defaultInstanceCategory: '默认分类', instanceSaved: '实例已保存',
    publishVersion: '发布版本', version: '版本', versionPublished: '版本已发布', publishedAt: '发布时间',
    setLatest: '设为 latest', restoreWorkspace: '恢复到工作区', review: '审核', reviewStatus: '审核状态', reviewComment: '审核意见',
    refresh: '刷新', accessType: '访问范围', accessLink: '持有链接的已登录用户', accessPublic: '所有已登录用户',
    accessSpecified: '指定用户', recipientUsernames: '接收者用户名', expiresAt: '过期时间', maxUseCount: '最大使用次数',
    createLink: '创建链接', linkCopied: '分享链接已复制，token 仅显示本次', userNotFound: '未找到该用户名',
    revoked: '已撤销', active: '有效', noShareLinks: '暂无分享链接', sharedReport: '共享计算书', importName: '导入后名称',
    importSharedReport: '导入共享计算书', files: '文件数', totalSize: '总大小',
    instanceCategories: '实例分类', allInstances: '全部实例', savedInstances: '计算实例', searchInstances: '搜索实例',
    editInstance: '编辑实例', instanceDetail: '实例详情', recalculate: '重新计算', updateInstanceResult: '更新实例结果',
    instanceUpdated: '实例结果已更新', executionHistory: '执行历史',
    publishStates: { unpublished: '未发布', published: '已发布', unpublished_changes: '有未发布修改', workspace_version_mismatch: '工作区为其他版本' },
    buildStates: { not_requested: '未构建', pending: '等待构建', building: '构建中', ready: '可运行', failed: '构建失败' },
    reviewStates: { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
  },

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
    onlyLettersNumbersUnderscoresAndCannotStartWithNumber:
      '仅支持字母、数字、下划线，且不能以数字开头',

    modifyCategory: '修改分类',
    deleteCategory: '删除分类',
    modifyCategorySuccess: '修改分类成功',

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
    index: '首页',
    newCalcReport: '新建报告',
    myFavorites: '我的收藏',
    noCategory: '无分类'
  },
  // #endregion

  // #region calcReport
  calcReportPage: {
    calcManagement: '计算管理',
    calcReport: '计算报告',
    reportTemplate: '报告模板',
    myCalcs: '我的计算',

    newCalcReport: '新建计算',
    newCalcReportTooltip: '创建新的计算报告',

    editCalcReport: '编辑计算',

    defaultCalcReportName: '',
    errorNoCategory: '没有 categoryOid，请关联分类信息',
    errorCategoryNotFound: '找不到对应的分类信息',
    pleaseInputCalcReportName: '请输入计算报告名称(有效的文件名，不能包含 : * ? " < > | 等字符)',

    calcReportViewer: '查看计算',

    // #region Viewer 页面
    viewer: {
      name: '名称',
      openLocalFile: '打开本地文件',
      devLocalFilePathPlaceholder: '输入本机文件完整路径',
      applyDevLocalFilePath: '使用该路径打开',
      restart: '重新开始',
      executeCalculation: '执行计算',
      resumeCalculation: '继续计算',
      uiDisplayArea: 'UI 显示区',
      pleaseStartExecution: '请单击 "执行计算" 按钮开始执行',
      missingReportOidOrPath: '缺失计算报告 oid 或路径',
      calculationCompleted: '计算执行完成',
      missingExecutionId: '缺失执行 ID',
      resumeExecutionFailed: '恢复计算执行失败',
      saveAsInstance: '保存为计算实例',
      saveCurrentInstance: '保存当前实例',
      saveInstance: '保存计算实例',
      saveInstanceSuccess: '计算实例保存成功',
      instanceCategory: '实例分类',
      resultNotReady: '请先执行计算'
    },
    // #endregion

    editor: {
      index: {
        // 请输入报告名称
        pleaseInputReportName: '请输入报告名称(仅支持字母、数字、下划线，且不能以数字开头)',
        // 保存 Ctrl + S
        saveTooltip: '保存 (Ctrl + S)',
        // 保存成功
        saveSuccess: '保存成功',
        // 保存失败
        saveFailed: '保存失败',
        runTooltip: '运行 (F5)',
        formatTooltip: '格式化 (Alt + Shift + F)'
      },

      menubar: {
        insert: '插入',
        format: '格式',
        groups: {
          elements: '元素',
          options: '选项'
        },
        elements: {
          title: '标题',
          subtitle: '副标题',
          h: '任意章节标题',
          h1: '一级章节标题',
          h2: '二级章节标题',
          h3: '三级章节标题',
          h4: '四级章节标题',
          h5: '五级章节标题',
          h6: '六级章节标题',
          p: '段落',
          div: '容器',
          span: '行内元素',
          br: '换行',
          row: '行',
          img: '图片',
          table: '表格',
          input: '输入框',
          code: '代码块',
          info: '信息',
          latex: 'LaTeX',
          plot: '图表'
        },
        options: {
          show: '显示',
          hide: '隐藏',
          enableSubstitution: '启用替换',
          disableSubstitution: '禁用替换',
          enableFStringEquation: '启用 F 字符串公式',
          disableFStringEquation: '禁用 F 字符串公式',
          inline: '行内',
          endInline: '换行',
          alias: '别名'
        }
      }
    },

    list: {
      col_name: '名称',
      col_description: '描述',
      col_version: '版本',
      col_lastModified: '最后修改时间',
      col_createdAt: '创建时间',
      deleteReportConfirm: '确认删除计算报告 "{name}"？',
      reportName: '报告名称',
      reportDescription: '报告描述',
      modifyReport: '修改报告',
      modifyInfo: '修改信息',
      modifyReportSourceCode: '修改源码',
      copy: '复制',
      copyReport: '复制报告',
      copyReportNameSuffix: '_副本',
      copyReportSuccess: '复制报告成功',
      reportNameRequired: '请输入报告名称',
      showInFileExplorer: '在文件资源管理器中显示',
      modifyReportSuccess: '修改报告成功'
    }
  },

  calcReportInstancePage: {
    calcsManagement: '计算管理',
    myCalcs: '我的计算',
    defaultCategoryName: '默认分类',
    list: {
      col_name: '名称',
      col_description: '描述',
      col_reportName: '来源计算',
      col_version: '版本',
      col_lastModified: '最后修改时间',
      col_createdAt: '创建时间',
      instanceName: '实例名称',
      instanceDescription: '实例描述',
      modifyInstance: '修改计算实例',
      modifyInfo: '修改信息',
      modifyInstanceSuccess: '修改计算实例成功',
      deleteInstanceConfirm: '确认删除计算实例 "{name}"？'
    }
  },

  calcModulePage: {
    calcModule: '计算模块'
  }
  // #endregion
}
