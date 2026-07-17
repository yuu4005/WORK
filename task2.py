'''
任务二（进阶关，约 15 分钟）：三种方式大对比

要求：

1. 写一个"模拟推理"的活：等 1 秒，返回结果。
2. 分别用**串行**（一个一个来）、**多线程**、**异步**三种方式跑 5 个活。
3. 用 `datetime` 记录每种方式的总耗时，打印出来对比。
'''
from datetime import datetime
import time
import threading
import asyncio


def simulate_inference(model):
    print(f"{model}开始推理")
    time.sleep(1)
    print(f"{model}推理结束")
    return "推理结果"

start1 = datetime.now()
for i in range(5):
    simulate_inference(f"T{i}")
end1 = datetime.now()
print(f"串行耗时{(end1-start1).total_seconds()}")

threads=[threading.Thread(target=simulate_inference,args=(f"T{i}",)) for i in range(5)]
start2 = datetime.now()
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
end2 = datetime.now()
print(f"多线程耗时{(end2-start2).total_seconds()}")


async def simulate_inference_async(model):
    print(f"{model}开始推理")
    await asyncio.sleep(1)
    print(f"{model}推理结束")
    return "推理结果"

async def main():
    start = datetime.now()
    await asyncio.gather(*[simulate_inference_async(f"T{i}") for i in range(5)] )
    end = datetime.now()
    print(f"异步耗时{(end-start).total_seconds()}")

asyncio.run(main())