'''
任务三（挑战关，约 20 分钟）：异步模拟多用户请求

要求（复用第三天的 AI 模型骨架，改成异步）：

1. 定义 `AIModel` 基类，`async def predict(self, input_data)` 抛 `NotImplementedError`。
2. 子类 `TextModel`：`predict` 里 `await asyncio.sleep(1)`，返回 `f"文本结果:{input_data}"`。
3. 子类 `ImageModel`：`predict` 里 `await asyncio.sleep(2)`，返回 `f"图像结果:{input_data}"`。
4. 写 `async def user_request(user, model, input_data)`：记录开始/结束时间，`await model.predict(...)`，
返回 `{user, model, cost, result}`。
5. 用 `gather` 同时跑 4 个用户请求（2 个文本、2 个图像），打印每个用户耗时和总耗时。
'''
import time
import threading
from datetime import datetime 
import asyncio

class AIModel:
    def __init__(self, name, model_type):
        self.name = name
        self.model_type = model_type

    async def predict(self, input_data):
        raise NotImplementedError("子类必须实现predict方法")
class TextModel(AIModel):
    async def predict(self, input_data):
        print(f"[{self.name}]正在生成文本：{input_data}")
        await asyncio.sleep(1)
        return f"文本结果：{input_data}"
                        

class ImageModel(AIModel):
    async def predict(self, input_data):
        print(f"[{self.name}]正在识别图像：{input_data}")
        await asyncio.sleep(2)
        return  f"图像结果：{input_data}"
          
async def user_request(user, model, input_data):
    start = datetime.now()
    result = await model.predict(input_data)
    end = datetime.now()
    print(f"user->{user},model->{model.name},耗时{(end - start).total_seconds()}秒，结果：[{result}]")
    return {"user":user,"model":model.name,"cost":(end - start).total_seconds(),"result":result}

async def main():
    text_model = TextModel("TextModel", "text")
    image_model = ImageModel("ImageModel", "image")

    start = datetime.now()
    await asyncio.gather(
        user_request("用户1", text_model, "写首诗"),
        user_request("用户2", text_model, "唱首歌"),
        user_request("用户3", image_model, "cat.jpg"),
        user_request("用户4", image_model, "dog.jpg"),
    )
    end = datetime.now()
    print(f"总耗时{(end-start).total_seconds()}秒")
    
asyncio.run(main())