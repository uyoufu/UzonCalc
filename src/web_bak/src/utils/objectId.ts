/**
 * MongoDB ObjectId 生成器
 * 格式：时间戳(4字节) + 机器ID(3字节) + 进程ID(2字节) + 计数器(3字节)
 */
class ObjectIdGenerator {
  private machineId: number
  private processId: number
  private counter: number

  constructor() {
    this.machineId = Math.floor(Math.random() * 0xffffff)
    this.processId = Math.floor(Math.random() * 0xffff)
    this.counter = 0
  }

  /**
   * 生成一个新的 ObjectId 字符串（24位十六进制）
   */
  generate(): string {
    const timestamp = Math.floor(Date.now() / 1000)
    this.counter = (this.counter + 1) % 0xffffff

    return (
      timestamp.toString(16).padStart(8, '0') +
      this.machineId.toString(16).padStart(6, '0') +
      this.processId.toString(16).padStart(4, '0') +
      this.counter.toString(16).padStart(6, '0')
    )
  }
}

// 导出默认实例
const defaultGenerator = new ObjectIdGenerator()

/**
 * 生成一个新的 ObjectId 字符串
 */
export function objectId(): string {
  return defaultGenerator.generate()
}

// 同时导出类，方便需要创建多个独立生成器的场景
export { ObjectIdGenerator as ObjectId }
