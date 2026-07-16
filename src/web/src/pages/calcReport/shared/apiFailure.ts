/** Utilities for reading stable API failures from Axios and response envelopes. */

import axios from 'axios'
import type { IResponseData } from 'src/api/base/types'

export interface ApiFailure {
  message: string
  code?: number
  errorCode?: string
  data?: unknown
}

/** Normalize an unknown request error into the backend response-envelope shape. */
export function getApiFailure(error: unknown): ApiFailure {
  if (axios.isAxiosError<IResponseData<unknown>>(error) && error.response?.data) {
    const response = error.response.data
    return {
      message: response.message || error.message,
      code: response.code,
      errorCode: response.errorCode,
      data: response.data
    }
  }
  if (typeof error === 'object' && error !== null && 'message' in error) {
    const response = error as Partial<IResponseData<unknown>>
    return {
      message: typeof response.message === 'string' ? response.message : 'Request failed',
      code: response.code,
      errorCode: response.errorCode,
      data: response.data
    }
  }
  return { message: error instanceof Error ? error.message : 'Request failed' }
}
