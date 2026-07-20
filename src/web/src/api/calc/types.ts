/** Shared frontend contracts for calculation-report controller DTOs. */

import type { ILowCodeField } from 'src/components/lowCode/types'

export const PublishState = {
  Unpublished: 'unpublished',
  Published: 'published',
  UnpublishedChanges: 'unpublished_changes',
  WorkspaceVersionMismatch: 'workspace_version_mismatch'
} as const
export type PublishState = typeof PublishState[keyof typeof PublishState]

export const BuildStatus = {
  NotRequested: 'not_requested',
  Pending: 'pending',
  Building: 'building',
  Ready: 'ready',
  Failed: 'failed'
} as const
export type BuildStatus = typeof BuildStatus[keyof typeof BuildStatus]

export const ExecutionSourceType = {
  Workspace: 'workspace',
  Latest: 'latest',
  Version: 'version'
} as const
export type ExecutionSourceType = typeof ExecutionSourceType[keyof typeof ExecutionSourceType]

export const ExecutionStatus = {
  Pending: 'pending',
  Running: 'running',
  Succeeded: 'succeeded',
  Failed: 'failed',
  Cancelled: 'cancelled',
  Expired: 'expired'
} as const
export type ExecutionStatus = typeof ExecutionStatus[keyof typeof ExecutionStatus]

export const ShareAccessType = {
  Public: 'public',
  Internal: 'internal',
  SpecifiedUsers: 'specified_users',
  SpecifiedDepartments: 'specified_departments'
} as const
export type ShareAccessType = typeof ShareAccessType[keyof typeof ShareAccessType]

export const ReportOriginType = {
  Native: 'native',
  Copy: 'copy',
  ShareImport: 'share_import',
  ShareSync: 'share_sync',
  FileImport: 'file_import'
} as const
export type ReportOriginType = typeof ReportOriginType[keyof typeof ReportOriginType]

export const ReportSyncState = {
  NotApplicable: 'not_applicable',
  Current: 'current',
  UpdateAvailable: 'update_available',
  SourceUnavailable: 'source_unavailable',
  AccessRevoked: 'access_revoked'
} as const
export type ReportSyncState = typeof ReportSyncState[keyof typeof ReportSyncState]

export const WorkspaceFileSource = {
  Upload: 'upload',
  Current: 'current'
} as const
export type WorkspaceFileSource = typeof WorkspaceFileSource[keyof typeof WorkspaceFileSource]

export const ExecutorType = {
  Local: 'local',
  Docker: 'docker'
} as const
export type ExecutorType = typeof ExecutorType[keyof typeof ExecutorType]

export const SandboxBackendMode = {
  InProcess: 'in_process',
  Bubblewrap: 'bubblewrap',
  Docker: 'docker'
} as const
export type SandboxBackendMode = typeof SandboxBackendMode[keyof typeof SandboxBackendMode]

export const ReservedDependencySelectorKey = {
  Latest: 'latest'
} as const

export const CalcErrorCode = {
  InvalidObjectId: 'INVALID_OBJECT_ID',
  ReportNotFound: 'REPORT_NOT_FOUND',
  CategoryNotFound: 'CATEGORY_NOT_FOUND',
  WorkspaceNotFound: 'WORKSPACE_NOT_FOUND',
  WorkspaceRevisionConflict: 'WORKSPACE_REVISION_CONFLICT',
  WorkspaceInvalid: 'WORKSPACE_INVALID',
  VersionNotFound: 'VERSION_NOT_FOUND',
  VersionAlreadyExists: 'VERSION_ALREADY_EXISTS',
  DependencyInvalid: 'DEPENDENCY_INVALID',
  DependencyCycle: 'DEPENDENCY_CYCLE',
  ExecutionArtifactNotReady: 'EXECUTION_ARTIFACT_NOT_READY',
  ExecutionArtifactBuildFailed: 'EXECUTION_ARTIFACT_BUILD_FAILED',
  ExecutionNotFound: 'EXECUTION_NOT_FOUND',
  ExecutionProcessLost: 'EXECUTION_PROCESS_LOST',
  ShareNotFound: 'SHARE_NOT_FOUND',
  ShareNotAllowed: 'SHARE_NOT_ALLOWED',
  ArchiveInvalid: 'ARCHIVE_INVALID'
} as const
export type CalcErrorCode = typeof CalcErrorCode[keyof typeof CalcErrorCode]

export interface CalcReportCategory {
  categoryOid: string
  name: string
  description: string | null
  manualOrder: number
  isPinned: boolean
  isHidden: boolean
  frequencyCount: number
  lastUsedAt: string | null
  reportCount: number
  createdAt: string
  updatedAt: string
}

export interface CalcReport {
  reportOid: string
  categoryOid: string
  name: string
  description: string | null
  cover: string | null
  entryPath: string
  formatVersion: number
  workspaceRevision: number
  workspaceArtifactHash: string | null
  latestVersionName: string | null
  latestArtifactHash: string | null
  buildStatus: BuildStatus
  publishState: PublishState
  isFavorite: boolean
  originType: ReportOriginType
  syncState: ReportSyncState
  canEdit: boolean
  canShare: boolean
  createdAt: string
  updatedAt: string
}

export interface DependencySelector {
  selectorKey: string
  versionName: string | null
  isDefault: boolean
}

export interface ReportDependency {
  alias: string
  targetReportOid: string
  selectors: DependencySelector[]
}

export interface WorkspaceFileInfo {
  path: string
  size: number
  sha256: string
}

export interface WorkspaceSnapshot {
  reportOid: string
  workspaceRevision: number
  sourceArtifactHash: string
  entryPath: string
  formatVersion: number
  files: WorkspaceFileInfo[]
  dependencies: ReportDependency[]
  buildStatus: BuildStatus
  publishState: PublishState
}

export interface WorkspaceBuild {
  sourceArtifactHash: string
  runtimeFingerprint: string | null
  buildStatus: BuildStatus
  diagnostics: Record<string, unknown> | null
}

export interface WorkspaceFileDescriptor {
  path: string
  sha256?: string
  source: WorkspaceFileSource
}

export interface WorkspaceSaveRequest {
  workspaceRevision: number
  create?: {
    categoryOid: string
    name: string
    description?: string | null
    cover?: string | null
  }
  files: WorkspaceFileDescriptor[]
  dependencies: ReportDependency[]
}

export interface CalcReportVersion {
  versionOid: string
  versionName: string
  importSegment: string
  sourceArtifactHash: string
  description: string | null
  isLatest: boolean
  createdAt: string
}

export interface ShareLink {
  shareOid: string
  reportOid: string
  versionName: string
  accessType: ShareAccessType
  canEdit: boolean
  canShare: boolean
  recipientUserOids: string[]
  recipientDepartmentOids: string[]
  note: string | null
  expiresAt: string | null
  revokedAt: string | null
  maxUseCount: number | null
  useCount: number
  createdAt: string
  token: string | null
  shareUrl?: string
}

export interface SharePreview {
  reportName: string
  reportDescription: string | null
  reportOid: string
  versionName: string
  dependencyCount: number
  totalFileCount: number
  totalSize: number
  canEdit: boolean
  canShare: boolean
  note: string | null
  recentExecution: CalcExecution | null
}

export interface CalcInputWindow {
  title: string
  caption?: string | null
  fields: ILowCodeField[]
}

export enum HtmlUpdateType {
  None = 0,
  Full = 1,
  Partial = 2
}

export interface CalcExecutionSource {
  type: ExecutionSourceType
  versionName?: string
}

export interface CalcExecution {
  executionId: string
  reportOid: string
  sourceType: ExecutionSourceType
  resolvedVersion: string | null
  sourceArtifactHash: string
  executionArtifactHash: string
  bundleHash: string
  runtimeFingerprint: string
  executorType: ExecutorType
  backendMode: SandboxBackendMode
  status: ExecutionStatus
  isCompleted: boolean
  windows: CalcInputWindow[]
  htmlPath: string
  updateType: HtmlUpdateType
  htmlContentPatch: string | null
  createdAt: string
  completedAt: string | null
}

export interface CalcInstanceCategory {
  categoryOid: string
  name: string
  description: string | null
  sortOrder: number
  instanceCount: number
  createdAt: string
  updatedAt: string
}

export interface CalcInstance {
  instanceOid: string
  categoryOid: string
  reportOid: string
  reportName: string | null
  sourceVersion: string | null
  bundleHash: string
  executionId: string | null
  name: string
  description: string | null
  defaults: Record<string, Record<string, unknown>>
  inputWindows: CalcInputWindow[]
  resultPath: string
  isShared: boolean
  shareToken: string | null
  revision: number
  createdAt: string
  updatedAt: string
}

export interface SharedReport {
  shareOid: string
  reportName: string
  qualifiedName: string
  sharedBy: string
  description: string | null
  note: string | null
  versionName: string
  sharedAt: string
  canEdit: boolean
  canShare: boolean
}

export interface ReportSyncStatus {
  reportOid: string
  state: ReportSyncState
  currentVersionName: string
  upstreamVersionName: string | null
}
