/** Publication dialog workflow for calculation reports selected from the report list. */

import { LowCodeFieldType } from 'src/components/lowCode/types'
import type { CalcReportVersion } from 'src/api/calc/types'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { t } from 'src/i18n/helpers'

export interface PublishVersionInput {
  versionName: string
  description: string
}

const semanticVersionPattern = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/

/** Create the calculation-report publication dialog opener. */
export function usePublishVersionDialog() {
  /** Suggest the next patch version and return validated publication metadata. */
  async function openPublishVersionDialog(versions: CalcReportVersion[]): Promise<PublishVersionInput | null> {
    const latest = versions[0]?.versionName?.split('.').map(Number)
    const suggestedVersion = latest?.length === 3
      ? `${latest[0]}.${latest[1]}.${(latest[2] || 0) + 1}`
      : '1.0.0'
    const result = await showDialog<PublishVersionInput>({
      title: t('calcWorkspace.publishVersion'),
      oneColumn: true,
      persistent: false,
      fields: [
        {
          name: 'versionName',
          label: t('calcWorkspace.version'),
          type: LowCodeFieldType.text,
          value: suggestedVersion,
          hint: 'MAJOR.MINOR.PATCH',
          required: true,
          validate: (value) => ({
            ok: typeof value === 'string' && semanticVersionPattern.test(value) &&
              !versions.some((version) => version.versionName === value),
            message: 'MAJOR.MINOR.PATCH'
          })
        },
        {
          name: 'description',
          label: t('calcWorkspace.description'),
          type: LowCodeFieldType.textarea,
          value: ''
        }
      ]
    })
    if (!result.ok) return null

    return {
      versionName: String(result.data.versionName),
      description: String(result.data.description || '')
    }
  }

  return { openPublishVersionDialog }
}
