/* eslint-disable @typescript-eslint/no-explicit-any */
import { httpClient } from 'src/api/base/httpClient'
import type { ILowCodeField } from 'src/components/lowCode/types'

export interface ICalcWindow {
  title: string,
  fields: ILowCodeField[],
}

/**
 * 执行结果接口
 */
export interface ExecutionResult {
  executionId: string
  html: string
  isCompleted: boolean
  windows: Array<ICalcWindow>
}

/**
 * 开始计算执行
 * @param data 执行参数
 */
export function startCalcExecution (data: {
  reportOid: string
  isSilent: boolean
  defaults?: Record<string, Record<string, any>>
}) {
  return httpClient.post<ExecutionResult>('/calc/execution/start', {
    data
  })
}

/**
 * 恢复计算执行（用于轮询）
 * @param connectionId 连接ID
 * @param defaults 用户输入的默认值
 */
export function resumeCalcExecution (
  connectionId: string,
  defaults?: Record<string, Record<string, any>>
) {
  return httpClient.post<ExecutionResult>(`/calc/execution/resume/${connectionId}`, {
    data: {
      defaults: defaults || {}
    }
  })
}

/**
 * 启动文件执行（调试用）
 * @param filePath 文件路径
 */
export function startFileExecution (filePath: string) {
  return httpClient.post<ExecutionResult>('/calc/execution/file', {
    data: {
      filePath
    }
  })
}
