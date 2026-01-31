"""测试异步生成器的 send 参数传递问题"""
import asyncio


# ========== 测试 1: 直接使用异步生成器 (正常工作) ==========
async def inner_generator():
    """内层异步生成器"""
    print("开始生成器")
    
    # 第一个 yield
    received = yield "请输入数据"
    print(f"收到输入: {received}")
    
    # 第二个 yield
    yield f"处理结果: {received}"


async def test_direct_send():
    """测试直接对异步生成器使用 asend"""
    print("\n=== 测试 1: 直接使用异步生成器 ===")
    
    gen = inner_generator()
    
    # 第一次获取
    value1 = await gen.__anext__()
    print(f"第一次获取: {value1}")
    
    # 发送数据
    value2 = await gen.asend("用户输入的数据")
    print(f"第二次获取: {value2}")
    
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        print("生成器结束")


# ========== 测试 2: 使用 async for 包装 (问题所在) ==========
async def wrapper_with_async_for():
    """使用 async for 包装的异步生成器"""
    print("包装器开始")
    async for item in inner_generator():
        print(f"包装器收到: {item}")
        yield item
    print("包装器结束")


async def test_wrapped_send():
    """测试对包装后的生成器使用 asend"""
    print("\n=== 测试 2: 使用 async for 包装 (会失败) ===")
    
    gen = wrapper_with_async_for()
    
    try:
        # 第一次获取
        value1 = await gen.__anext__()
        print(f"第一次获取: {value1}")
        
        # 尝试发送数据 - 这里会失败，因为数据无法传递到内层生成器
        value2 = await gen.asend("用户输入的数据")
        print(f"第二次获取: {value2}")
        
        await gen.__anext__()
    except StopAsyncIteration:
        print("生成器结束")


# ========== 测试 3: 正确的包装方式 (手动转发) ==========
async def wrapper_with_manual_forward():
    """手动转发 send 的异步生成器包装器"""
    print("手动转发包装器开始")
    
    # 创建内层生成器
    inner_gen = inner_generator()
    
    # 第一次获取
    value = await inner_gen.__anext__()
    
    # 循环处理
    while True:
        try:
            # yield 出去，并接收外部 send 的值
            received = yield value
            
            # 将接收到的值转发给内层生成器
            if received is not None:
                value = await inner_gen.asend(received)
            else:
                value = await inner_gen.__anext__()
        except StopAsyncIteration:
            break
    
    print("手动转发包装器结束")


async def test_manual_forward():
    """测试手动转发的包装器"""
    print("\n=== 测试 3: 手动转发 send (正确方式) ===")
    
    gen = wrapper_with_manual_forward()
    
    try:
        # 第一次获取
        value1 = await gen.__anext__()
        print(f"第一次获取: {value1}")
        
        # 发送数据
        value2 = await gen.asend("用户输入的数据")
        print(f"第二次获取: {value2}")
        
        await gen.__anext__()
    except StopAsyncIteration:
        print("生成器结束")


# ========== 运行所有测试 ==========
async def main():
    print("=" * 60)
    print("异步生成器 send 参数传递测试")
    print("=" * 60)
    
    await test_direct_send()
    await test_wrapped_send()
    await test_manual_forward()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
