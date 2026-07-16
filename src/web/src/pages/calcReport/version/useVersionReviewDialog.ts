/** Administrator review dialog workflow for immutable calculation-report versions. */

import { LowCodeFieldType } from 'src/components/lowCode/types'
import type { CalcReportVersion, ReviewStatus } from 'src/api/calc/types'
import { showDialog } from 'src/components/lowCode/PopupDialog'
import { t } from 'src/i18n/helpers'

interface ReviewVersionInput {
  status: ReviewStatus
  comment: string
}

/**
 * Create the immutable-version review dialog opener.
 *
 * @returns Review function that resolves input or null after cancellation.
 */
export function useVersionReviewDialog() {
  /** Open administrator review controls for one immutable version. */
  async function openVersionReviewDialog(version: CalcReportVersion): Promise<ReviewVersionInput | null> {
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

  return { openVersionReviewDialog }
}
