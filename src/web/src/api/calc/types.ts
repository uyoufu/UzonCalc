/** Shared frontend contracts for calculation-report controller DTOs. */

import type { ILowCodeField } from 'src/components/lowCode/types'

export type PublishState = 'unpublished' | 'published' | 'unpublished_changes' | 'workspace_version_mismatch'
export type BuildStatus = 'not_requested' | 'pending' | 'building' | 'ready' | 'failed'
export type ReviewStatus = 'pending' | 'approved' | 'rejected'
export type ExecutionSourceType = 'workspace' | 'latest' | 'version'
export type ExecutionStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'cancelled' | 'expired'
export type ShareAccessType = 'link' | 'public' | 'specified_users'

export enum CalcErrorCode {
  InvalidObjectId = 'INVALID_OBJECT_ID',
  ReportNotFound = 'REPORT_NOT_FOUND',
  CategoryNotFound = 'CATEGORY_NOT_FOUND',
  WorkspaceNotFound = 'WORKSPACE_NOT_FOUND',
  WorkspaceRevisionConflict = 'WORKSPACE_REVISION_CONFLICT',
  WorkspaceInvalid = 'WORKSPACE_INVALID',
  VersionNotFound = 'VERSION_NOT_FOUND',
  VersionAlreadyExists = 'VERSION_ALREADY_EXISTS',
  DependencyInvalid = 'DEPENDENCY_INVALID',
  DependencyCycle = 'DEPENDENCY_CYCLE',
  ExecutionArtifactNotReady = 'EXECUTION_ARTIFACT_NOT_READY',
  ExecutionArtifactBuildFailed = 'EXECUTION_ARTIFACT_BUILD_FAILED',
  ExecutionNotFound = 'EXECUTION_NOT_FOUND',
  ExecutionProcessLost = 'EXECUTION_PROCESS_LOST',
  ShareNotFound = 'SHARE_NOT_FOUND',
  ShareNotAllowed = 'SHARE_NOT_ALLOWED',
  ArchiveInvalid = 'ARCHIVE_INVALID'
}

export interface CalcReportCategory {
  categoryOid: string
  name: string
  description: string | null
  sortOrder: number
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
  createdAt: string
  updatedAt: string
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
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
  source: 'upload' | 'current'
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
  reviewStatus: ReviewStatus
  reviewedAt: string | null
  reviewComment: string | null
  isLatest: boolean
  createdAt: string
}

export interface ShareLink {
  shareOid: string
  reportOid: string
  versionName: string
  accessType: ShareAccessType
  expiresAt: string | null
  revokedAt: string | null
  maxUseCount: number | null
  useCount: number
  createdAt: string
  token: string | null
}

export interface SharePreview {
  reportName: string
  reportDescription: string | null
  reportOid: string
  versionName: string
  dependencyCount: number
  totalFileCount: number
  totalSize: number
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
  executorType: string
  backendMode: string
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
  resultPath: string
  revision: number
  createdAt: string
  updatedAt: string
}
