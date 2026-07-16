// This is just an example,
// so you can safely delete all default props below

export default {
  // #region Global
  global: {
    appName: 'UzonCalc',
    order: 'No.',
    failed: 'Failed',
    success: 'Operation successful',
    confirm: 'Confirm',
    cancel: 'Cancel',
    view: 'View',
    version: 'Version',
    lastModified: 'Last modified',
    modify: 'Modify',
    edit: 'Edit',
    delete: 'Delete',
    new: 'New',
    add: 'Add',
    confirmOperation: 'Confirm operation',
    deleteConfirmation: 'Delete confirmation',
    warning: 'Warning',
    notice: 'Notice',
    cancelOperation: 'Cancel operation',
    languageRequired: 'Language is required',
    htmlContentRequired: 'HTML content is required',
    deleteSuccess: 'Deleted successfully',
    updateSuccess: 'Updated successfully',
    pleaseInputNumber: 'Please enter a number',
    import: 'Import',
    importing: 'Importing',
    export: 'Export',
    exporting: 'Exporting',
    validate: 'Validate',
    validateMultiple: 'Batch validate',
    yes: 'Yes',
    no: 'No',
    empty: 'Empty',
    save: 'Save'
  },

  // #endregion

  calcWorkspace: {
    categories: 'Report categories', newCategory: 'New category', editCategory: 'Edit category', categoryName: 'Category',
    allReports: 'All reports', newReport: 'New report', untitledReport: 'Untitled report', reportName: 'Report name',
    description: 'Description', searchReports: 'Search reports', latestVersion: 'Latest version', state: 'Status',
    openWorkspace: 'Open workspace', runLatest: 'Run latest', editMetadata: 'Edit metadata', toggleFavorite: 'Toggle favorite',
    copyReport: 'Copy report', share: 'Share', shareReport: 'Share report', showInExplorer: 'Show in file explorer',
    importUzc: 'Import .uzc', uzcFile: '.uzc file', importComplete: 'Import complete', metadataRequired: 'Category and report name are required',
    workspace: 'Workspace', run: 'Run', versionsAndShares: 'Versions and shares', backToReports: 'Back to reports', desktopRequired: 'Workspace editing requires a desktop viewport',
    saveWorkspace: 'Save complete workspace', workspaceSaved: 'Workspace saved', saved: 'Saved', unsaved: 'Unsaved changes',
    newFile: 'New file', uploadResources: 'Upload resources', dependencies: 'Dependencies', selectFile: 'Select a file to edit',
    rename: 'Rename', setEntry: 'Set as entry', format: 'Format Python', download: 'Download', binaryResource: 'Binary resource',
    runWorkspace: 'Save and run workspace', alias: 'Dependency alias', targetReport: 'Target report', selectors: 'Version selectors', defaultSelector: 'Default selector',
    revisionConflict: 'Workspace revision conflict', revisionConflictMessage: 'The server workspace changed. Local content is still preserved.',
    exportLocalZip: 'Export local ZIP', discardAndReload: 'Discard local changes and reload', leaveWithoutSaving: 'Unsaved changes will be lost when leaving.',
    executionSource: 'Execution source', sourceWorkspace: 'Workspace', sourceLatest: 'Latest published version', sourceVersion: 'Explicit version',
    silentRun: 'Run directly with defaults', startRun: 'Start', continueRun: 'Continue', terminate: 'Terminate',
    runToPreview: 'Run to preview the result', noInputs: 'This step has no inputs', backend: 'Backend', startedAt: 'Started at',
    buildWaiting: 'The execution artifact is building; retry when it is ready', buildReady: 'The execution artifact is ready', buildFailed: 'Execution artifact build failed',
    saveInstance: 'Save instance', instanceName: 'Instance name', defaultInstanceCategory: 'Default category', instanceSaved: 'Instance saved',
    publishVersion: 'Publish version', version: 'Version', versionPublished: 'Version published', publishedAt: 'Published at',
    setLatest: 'Set latest', restoreWorkspace: 'Restore workspace', review: 'Review', reviewStatus: 'Review status', reviewComment: 'Review comment',
    refresh: 'Refresh', accessType: 'Access', accessLink: 'Signed-in link holders', accessPublic: 'All signed-in users',
    accessSpecified: 'Specified users', recipientUsernames: 'Recipient usernames', expiresAt: 'Expires at', maxUseCount: 'Maximum uses',
    createLink: 'Create link', linkCopied: 'Share link copied; the token is shown only once', userNotFound: 'Username not found',
    revoked: 'Revoked', active: 'Active', noShareLinks: 'No share links', sharedReport: 'Shared report', importName: 'Imported name',
    importSharedReport: 'Import shared report', files: 'Files', totalSize: 'Total size',
    instanceCategories: 'Instance categories', allInstances: 'All instances', savedInstances: 'Saved instances', searchInstances: 'Search instances',
    editInstance: 'Edit instance', instanceDetail: 'Instance detail', recalculate: 'Recalculate', updateInstanceResult: 'Update instance result',
    instanceUpdated: 'Instance result updated', executionHistory: 'Execution history',
    publishStates: { unpublished: 'Unpublished', published: 'Published', unpublished_changes: 'Unpublished changes', workspace_version_mismatch: 'Workspace is another version' },
    buildStates: { not_requested: 'Not built', pending: 'Pending', building: 'Building', ready: 'Ready', failed: 'Build failed' },
    reviewStates: { pending: 'Pending', approved: 'Approved', rejected: 'Rejected' }
  },

  // #region Components
  components: {
    clear: 'Clear',
    removeUploadedFile: 'Remove uploaded file',
    selectFile: 'Select file',
    upload: 'Upload',
    abortUpload: 'Abort upload',
    waitingForUpload: 'Waiting for upload...',
    remain: 'Remaining',
    calculatingFileHash: 'Calculating hash for {fileName}',
    uploadingFile: 'Uploading {fileName}'
  },

  // #endregion

  searchInput: {
    placeholder: 'Search'
  },

  collapseLeft: {
    collapse: 'Collapse',
    expand: 'Expand'
  },

  collapseRight: {
    collapse: 'Collapse',
    expand: 'Expand'
  },

  categoryList: {
    youCanRightClickToAddNewCategory: 'You can right-click to add a new category',
    newCategory: 'New category',
    newCategorySuccess: 'Category added successfully',
    onlyLettersNumbersUnderscoresAndCannotStartWithNumber:
      'Only letters, numbers and underscores are allowed, and cannot start with a number',

    modifyCategory: 'Edit category',
    deleteCategory: 'Delete category',
    modifyCategorySuccess: 'Category updated successfully',

    deleteCategoryConfirm:
      'Are you sure you want to delete category "{label}"? This action cannot be undone.',
    deleteCategorySuccess: 'Category "{label}" deleted successfully',

    field_name: 'Name',
    field_icon: 'Icon',
    field_cover: 'Cover',
    field_total: 'Total',
    field_order: 'Order',
    field_description: 'Description'
  },

  utils: {
    totalItems: '... and {count} {unit} in total',
    item: 'item',

    file_fileNotFound: 'File not found',
    file_noFileDetected: 'No file detected, the user may have canceled',
    file_specifyWorksheet: 'Specify worksheet',
    file_pleaseSelectWorksheet: 'Please select a worksheet',
    file_fieldCannotBeEmpty: 'Field {field} cannot be empty',
    file_mappersCannotBeEmptyInStrictMode: 'Mappers cannot be empty in strict mode',
    file_fieldCannotBeEmptyAtRow: 'In row {rowIndex}, the {field} column cannot be empty',
    file_calculatingHash: 'Calculating hash...',
    file_fileHashCalculated: 'File {fileName} sha256 is:',
    file_hashVerifiedWaitingUpload: 'Hash verified, waiting for upload',
    file_invalidDownloadUrl: 'Invalid download URL, should start with http',
    file_parsingFile: 'Parsing file...',
    file_downloadCompleted: 'Download completed',
    file_downloadFailed: 'Download failed',
    file_downloadingFile: '{fileName} downloading...',
    file_fileExtension: '{ext} file'
  },

  routes: {
    sponsorAuthor: 'Support author',
    helpDoc: 'Help documentation',
    startGuide: 'Getting started',
    login: 'Login',
    singlePages: 'Single pages',
    exception: 'Exception'
  },

  buttons: {
    new: 'New',
    newItem: 'New item',
    delete: 'Delete',
    deleteItem: 'Delete item',
    save: 'Save',
    cancel: 'Cancel',
    cancelCurrentOperation: 'Cancel current operation',
    export: 'Export',
    exportData: 'Export data',
    import: 'Import',
    importData: 'Import data',
    confirm: 'Confirm',
    confirmCurrentOperation: 'Confirm current operation'
  },

  loginPage: {
    userName: 'Username',
    password: 'Password',
    signIn: 'Sign in',
    version: 'Version',
    client: 'Client',
    server: 'Server',
    pleaseInputUserName: 'Please enter username',
    pleaseInputPassword: 'Please enter password'
  },

  userPage: {
    userInfo: 'User info',
    profile: 'Profile'
  },

  dashboardPage: {
    index: 'Dashboard',
    newCalcReport: 'New report',
    myFavorites: 'My favorites',
    noCategory: 'No category'
  },

  calcReportPage: {
    calcManagement: 'Calculation management',
    calcReport: 'Calculation report',
    reportTemplate: 'Report template',
    myCalcs: 'My calculations',

    newCalcReport: 'New calculation',
    newCalcReportTooltip: 'Create a new calculation report',

    editCalcReport: 'Edit calculation',

    defaultCalcReportName: '',
    errorNoCategory: 'No categoryOid, please link category information',
    errorCategoryNotFound: 'Category information not found',
    pleaseInputCalcReportName:
      'Please enter calculation report name (valid filename, cannot contain : * ? " < > | etc.)',

    calcReportViewer: 'View calculation',

    viewer: {
      name: 'Name',
      openLocalFile: 'Open local file',
      devLocalFilePathPlaceholder: 'Enter local file full path',
      applyDevLocalFilePath: 'Open with this path',
      restart: 'Restart',
      executeCalculation: 'Execute calculation',
      resumeCalculation: 'Resume calculation',
      uiDisplayArea: 'UI display area',
      pleaseStartExecution: 'Please click "Execute calculation" to start',
      missingReportOidOrPath: 'Missing report oid or path',
      calculationCompleted: 'Calculation completed',
      missingExecutionId: 'Missing execution ID',
      resumeExecutionFailed: 'Failed to resume execution',
      saveAsInstance: 'Save as calculation instance',
      saveCurrentInstance: 'Save current instance',
      saveInstance: 'Save calculation instance',
      saveInstanceSuccess: 'Calculation instance saved',
      instanceCategory: 'Instance category',
      resultNotReady: 'Please execute the calculation first'
    },

    editor: {
      index: {
        pleaseInputReportName:
          'Please enter report name (only letters, numbers, underscores, and cannot start with a number)',
        saveTooltip: 'Save (Ctrl + S)',
        saveSuccess: 'Saved successfully',
        saveFailed: 'Save failed',
        runTooltip: 'Run (F5)',
        formatTooltip: 'Format (Alt + Shift + F)'
      },

      menubar: {
        insert: 'Insert',
        format: 'Format',
        groups: {
          elements: 'Elements',
          options: 'Options'
        },
        elements: {
          title: 'Title',
          subtitle: 'Subtitle',
          h: 'Any section title',
          h1: 'Heading 1',
          h2: 'Heading 2',
          h3: 'Heading 3',
          h4: 'Heading 4',
          h5: 'Heading 5',
          h6: 'Heading 6',
          p: 'Paragraph',
          div: 'Container',
          span: 'Inline element',
          br: 'Line break',
          row: 'Row',
          img: 'Image',
          table: 'Table',
          input: 'Input',
          code: 'Code block',
          info: 'Info',
          latex: 'LaTeX',
          plot: 'Chart'
        },
        options: {
          show: 'Show',
          hide: 'Hide',
          enableSubstitution: 'Enable substitution',
          disableSubstitution: 'Disable substitution',
          enableFStringEquation: 'Enable f-string equations',
          disableFStringEquation: 'Disable f-string equations',
          inline: 'Inline',
          endInline: 'New line',
          alias: 'Alias'
        }
      }
    },

    list: {
      col_name: 'Name',
      col_description: 'Description',
      col_version: 'Version',
      col_lastModified: 'Last modified',
      col_createdAt: 'Created at',
      deleteReportConfirm: 'Confirm delete calculation report "{name}"?',
      reportName: 'Report name',
      reportDescription: 'Report description',
      modifyReport: 'Modify report',
      modifyInfo: 'Modify info',
      modifyReportSourceCode: 'Modify source code',
      copy: 'Copy',
      copyReport: 'Copy report',
      copyReportNameSuffix: '_copy',
      copyReportSuccess: 'Report copied successfully',
      reportNameRequired: 'Please enter report name',
      showInFileExplorer: 'Show in file explorer',
      modifyReportSuccess: 'Report updated successfully'
    }
  },

  calcReportInstancePage: {
    calcsManagement: 'Calculations management',
    myCalcs: 'My calculations',
    defaultCategoryName: 'Default',
    list: {
      col_name: 'Name',
      col_description: 'Description',
      col_reportName: 'Source calculation',
      col_version: 'Version',
      col_lastModified: 'Last modified',
      col_createdAt: 'Created at',
      instanceName: 'Instance name',
      instanceDescription: 'Instance description',
      modifyInstance: 'Modify instance',
      modifyInfo: 'Modify info',
      modifyInstanceSuccess: 'Instance updated successfully',
      deleteInstanceConfirm: 'Confirm delete calculation instance "{name}"?'
    }
  },

  calcModulePage: {
    calcModule: 'Calculation module'
  }
}
