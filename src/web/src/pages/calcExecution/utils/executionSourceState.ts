/** Compare execution provenance with the currently loaded report source. */

import { ExecutionSourceType, type CalcExecution, type CalcReport } from 'src/api/calc/types'

/** Return whether a workspace execution was produced from an older source artifact. */
export function isWorkspaceExecutionOutdated(
  execution: CalcExecution | null,
  report: CalcReport | null
): boolean {
  return Boolean(
    execution?.sourceType === ExecutionSourceType.Workspace
    && report?.workspaceHash
    && execution.sourceArtifactHash !== report.workspaceHash
  )
}
