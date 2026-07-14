import { httpClient } from 'src/api/base/httpClient'

/**
 * 弹出文件选择对话框并返回选择的文件路径（仅限桌面模式）
 */
export function selectLocalFile() {
  return httpClient.get<string>('/desktop/select-file')
}

/**
 * 在文件资源管理器中显示计算报告源码文件（仅限桌面模式）
 */
export function showCalcReportInExplorer(reportOid: string) {
  return httpClient.post<void>(`/desktop/calc-report/${reportOid}/show-in-explorer`)
}
