import { httpClient } from 'src/api/base/httpClient'

export interface IPythonRuffFormatReq {
  code: string
  lineLength?: number
}

export interface IPythonRuffFormatRes {
  formattedCode: string
  changed: boolean
  formatter: 'ruff'
}

/** Format Python source through the isolated backend Ruff formatter. */
export function formatPythonByRuff(data: IPythonRuffFormatReq) {
  return httpClient.post<IPythonRuffFormatRes>('/code-format/python/ruff', {
    data,
    stopNotifyError: true
  })
}
