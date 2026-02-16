import { httpClient } from 'src/api/base/httpClient'

export interface IPythonBlackFormatReq {
  code: string
  lineLength?: number
}

export interface IPythonBlackFormatRes {
  formattedCode: string
  changed: boolean
  formatter: 'black'
}

export function formatPythonByBlack(data: IPythonBlackFormatReq) {
  return httpClient.post<IPythonBlackFormatRes>('/code-format/python/black', {
    data,
    stopNotifyError: true
  })
}
