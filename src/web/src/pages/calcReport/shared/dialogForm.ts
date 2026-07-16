/** Shared form contracts and validators for calculation workspace dialogs. */

import type { IFunctionResult } from 'src/types'

/** Select option used by page-local calculation dialogs. */
export interface DialogSelectOption {
  label: string
  value: string
}

/**
 * Create a validator that rejects empty or whitespace-only text.
 *
 * @param message - Validation message returned for blank text.
 * @returns Field validator compatible with lowCode dialog fields.
 */
export function createNonBlankValidator(message: string): (value: unknown) => IFunctionResult {
  return (value: unknown) => ({ ok: typeof value === 'string' && value.trim().length > 0, message })
}

