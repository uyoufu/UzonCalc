/** Version publication and review dialog workflows. */

import { LowCodeFieldType } from 'src/components/lowCode/types'
import type { CalcReportVersion, ReviewStatus } from 'src/api/calc/types'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { t } from 'src/i18n/helpers'

interface PublishVersionInput {
  versionName: string
  description: string
}

interface ReviewVersionInput {
  status: ReviewStatus
  comment: string
}

const semanticVersionPattern = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/

/**
 * Create version dialog openers.
 *
 * @returns Publication and review functions that resolve input or null after cancellation.
 */
export function useVersionDialogs() {
  /** Suggest the next patch version and open publication metadata. */
  async function openPublishDialog(
    versions: CalcReportVersion[]
  ): Promise<PublishVersionInput | null> {
    const latest = versions[0]?.versionName?.split('.').map(Number)
    const suggestedVersion =
      latest?.length === 3 ? `${latest[0]}.${latest[1]}.${(latest[2] || 0) + 1}` : '1.0.0'
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
            ok:
              typeof value === 'string' &&
              semanticVersionPattern.test(value) &&
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

  /** Open administrator review controls for one immutable version. */
  async function openReviewDialog(version: CalcReportVersion): Promise<ReviewVersionInput | null> {
    const result = await showDialog<ReviewVersionInput>({
      title: `${t('calcWorkspace.review')} · ${version.versionName}`,
      oneColumn: true,
      persistent: false,
      fields: [
        {
          name: 'status',
          label: t('calcWorkspace.reviewStatus'),
          type: LowCodeFieldType.selectOne,
          value: version.reviewStatus,
          options: [
            { label: t('calcWorkspace.reviewStates.pending'), value: 'pending' },
            { label: t('calcWorkspace.reviewStates.approved'), value: 'approved' },
            { label: t('calcWorkspace.reviewStates.rejected'), value: 'rejected' }
          ],
          optionLabel: 'label',
          optionValue: 'value',
          emitValue: true,
          mapOptions: true,
          required: true
        },
        {
          name: 'comment',
          label: t('calcWorkspace.reviewComment'),
          type: LowCodeFieldType.textarea,
          value: version.reviewComment || ''
        }
      ]
    })
    if (!result.ok) return null

    return {
      status: result.data.status,
      comment: String(result.data.comment || '')
    }
  }

  return { openPublishDialog, openReviewDialog }
}
