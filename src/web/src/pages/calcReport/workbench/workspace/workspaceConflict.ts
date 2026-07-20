/** Workspace revision-conflict recovery choices. */

/** Recovery actions available after an optimistic workspace conflict. */
export enum WorkspaceConflictResolution {
  ExportLocalZip = 'exportLocalZip',
  DiscardAndReload = 'discardAndReload'
}

