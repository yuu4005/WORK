from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate,PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import List



#1.环境配置
load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

#2.初始化模型
llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0.3
)

#3.生成自我介绍
def generate_introduction(name, job, skills):
    #创建提示词模板对象
    prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的人力资源顾问，擅长帮人写简洁有力的自我介绍"),
    ("human","请根据以下信息，帮我写一段 50 字以内的自我介绍。姓名：`{name}`，职位：`{job}`，技能：`{skills}`")
    ])
    #

    #用 LCEL 语法组合
    chain = prompt | llm | StrOutputParser()

    #调用模型
    response = chain.invoke({"name": name, "job": job, "skills": skills})
    print(response)
    print(type(response))
    return response
   
#生成个人 slogan
def generate_slogan(name, job):
    #创建提示词
    prompt = PromptTemplate.from_template("请根据以下信息，生成一句 15 字以内的个人 slogan，要求朗朗上口。姓名：`{name}`，职位：`{job}'")
    #调用模型生成 slogan
    response = llm.invoke(prompt.format(name=name, job=job))
    print(response.content)
    return response.content


#生成结构化名片数据    
def generate_card(name, job, skills, intro, slogan):
   #定义一个 Pydantic 类 `Card`
    class Card(BaseModel):
        name: str = Field(description="姓名")
        job: str = Field(description="职位")
        intro: str = Field(description="自我介绍")
        slogan: str = Field(description="个人 slogan")
        skills: list = Field(description="技能列表")

    #创建 `JsonOutputParser(pydantic_object=Card)`,初始化JSON解析器
    parser = JsonOutputParser(pydantic_object=Card)

    #创建提示词模板对象,使用 `parser.get_format_instructions()` 作为 system 提示词
    messages = [
    SystemMessage(content=parser.get_format_instructions()),  # 生成响应 JSON 的系统提示词
    HumanMessage(content=f"姓名:{name},职位:{job},技能字符串:{skills},自我介绍:{intro},标语:{slogan}")
    ]

    #调用模型生成结构化名片数据
    response = llm.invoke(messages)
    resp = parser.invoke(response)
    print(resp)
    return resp




if __name__ == "__main__":
    #测试数据测试数据：`name="张三"`，`job="Python 开发工程师"`，`skills="Python, LangChain, FastAPI"`
    intro = generate_introduction("张三", "Python 开发工程师", "Python, LangChain, FastAPI")
    slogan = generate_slogan("张三", "Python 开发工程师")
    card = generate_card("张三", "Python 开发工程师", "Python, LangChain, FastAPI", intro, slogan)
    # 任务要求：格式化打印完整名片
    print("=" * 28)
    print("        AI 智能名片")
    print("=" * 28)
    print(f"姓名：{card['name']}")
    print(f"职位：{card['job']}")
    print(f"自我介绍：{card['intro']}")
    print(f"个人 slogan：{card['slogan']}")
    print(f"技能：{', '.join(card['skills'])}")
    print("=" * 28)