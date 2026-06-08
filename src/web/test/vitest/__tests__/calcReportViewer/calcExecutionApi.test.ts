import { describe, expect, it, vi } from 'vitest'
import { resumeCalcExecution, startCalcExecution, startFileExecution } from 'src/api/calcExecution'

// 独立保存 mock 函数，避免断言实例方法时丢失 this 作用域。
const httpClientPostMock = vi.hoisted(() => vi.fn())

vi.mock('src/api/base/httpClient', () => ({
  httpClient: {
    post: httpClientPostMock
  }
}))

describe('calcExecution api', () => {
  it('开始报告计算时提交上一次 HTML 路径', async () => {
    await startCalcExecution({
      reportOid: 'report-oid',
      isSilent: true,
      defaults: {},
      lastHtmlPath: 'public/calcs/1/old.html'
    })

    expect(httpClientPostMock).toHaveBeenCalledWith('/calc/execution/start', {
      data: {
        reportOid: 'report-oid',
        isSilent: true,
        defaults: {},
        lastHtmlPath: 'public/calcs/1/old.html'
      }
    })
  })

  it('继续和文件计算时提交上一次 HTML 路径', async () => {
    httpClientPostMock.mockClear()

    await resumeCalcExecution('connection-id', {}, 'public/calcs/1/resume-old.html')
    await startFileExecution('/tmp/report.py', {}, 'public/calcs/1/file-old.html')

    expect(httpClientPostMock).toHaveBeenNthCalledWith(1, '/calc/execution/resume/connection-id', {
      data: {
        defaults: {},
        lastHtmlPath: 'public/calcs/1/resume-old.html'
      }
    })
    expect(httpClientPostMock).toHaveBeenNthCalledWith(2, '/calc/execution/file', {
      data: {
        filePath: '/tmp/report.py',
        defaults: {},
        lastHtmlPath: 'public/calcs/1/file-old.html'
      }
    })
  })
})
