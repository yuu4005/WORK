'''
旅游规划智能分发系统

**场景**：你为一个旅游 APP 开发了智能问答系统，根据用户的旅游问题，分发给不同的专业顾问。

**需求**：

1. 定义 **5 个顾问 Chain**：
  * `destination`: 目的地顾问
  * `budget`: 预算规划师
  * `transportation`: 交通顾问
  * `food`: 美食顾问
  * `culture`: 文化顾问
2. 主管节点分析用户需求，判断需要哪些顾问参与
3. 支持单个顾问回答和多顾问并发回答
4. 实现一个**旅行计划生成器**：用户输入目的地 + 天数 + 预算，自动调用所有顾问生成完整旅行计划
5. 打印分发决策
'''
import os
import re
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# ==================== 1. 环境 & 模型 ====================
load_dotenv()
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

llm = ChatOpenAI(model=model_name, api_key=api_key, base_url=base_url, temperature=0.7)
supervisor_llm = ChatOpenAI(model=model_name, api_key=api_key, base_url=base_url, temperature=0.1)

# ==================== 2. 主管节点 ====================
supervisor_prompt = ChatPromptTemplate.from_template(
    "你是一个旅游规划智能分发系统的主管。\n"
    "用户问题：{question}\n\n"
    "请判断需要哪些顾问参与，输出逗号分隔的顾问名称（可多选），不要额外内容：\n"
    "1. destination（目的地顾问）\n"
    "2. budget（预算规划师）\n"
    "3. transportation（交通顾问）\n"
    "4. food（美食顾问）\n"
    "5. culture（文化顾问）\n\n"
    "例如：destination,budget,transportation"
)
supervisor_chain = supervisor_prompt | supervisor_llm | StrOutputParser()

# ==================== 3. 5 个顾问 Chain ====================
destination_prompt = ChatPromptTemplate.from_template(
    "你是一个旅游目的地顾问。\n用户问题：{question}\n请推荐合适的目的地并说明理由。"
)
destination_chain = destination_prompt | llm | StrOutputParser()

budget_prompt = ChatPromptTemplate.from_template(
    "你是一个旅游预算规划师。\n用户问题：{question}\n请给出详细的预算规划和费用明细。"
)
budget_chain = budget_prompt | llm | StrOutputParser()

transportation_prompt = ChatPromptTemplate.from_template(
    "你是一个旅游交通顾问。\n用户问题：{question}\n请推荐往返和当地的交通方式。"
)
transportation_chain = transportation_prompt | llm | StrOutputParser()

food_prompt = ChatPromptTemplate.from_template(
    "你是一个旅游美食顾问。\n用户问题：{question}\n请推荐当地必吃的特色美食和餐厅。"
)
food_chain = food_prompt | llm | StrOutputParser()

culture_prompt = ChatPromptTemplate.from_template(
    "你是一个旅游文化顾问。\n用户问题：{question}\n请推荐必去的文化景点和特色体验。"
)
culture_chain = culture_prompt | llm | StrOutputParser()

# ==================== 4. 顾问映射表 ====================
ADVISOR_MAP = {
    "destination":   ("目的地顾问", destination_chain),
    "budget":        ("预算规划师", budget_chain),
    "transportation":("交通顾问",   transportation_chain),
    "food":          ("美食顾问",   food_chain),
    "culture":       ("文化顾问",   culture_chain),
}

# ==================== 5. 旅行计划汇总师 ====================
def parse_travel_params(question: str):
    """从用户输入中提取天数、预算、目的地"""
    days_match = re.search(r"(\d+)\s*[天日]", question)
    budget_match = re.search(r"(\d+)\s*[元块万]", question)
    place_match = re.search(r"([\u4e00-\u9fa5]{2,4})(?:旅行|游|旅游|之行|攻略|行程)", question)
    return (
        days_match.group(1) if days_match else "未指定",
        (budget_match.group(1) + "元") if budget_match else "未指定",
        place_match.group(1) if place_match else "目的地",
    )

planner_prompt = ChatPromptTemplate.from_template(
    "你是一个旅行计划整合专家。根据以下各顾问的建议，为一次{days}天、预算为{budget}的{place}旅行生成一份完整的计划。\n\n"
    "目的地建议：{destination}\n"
    "预算规划：{budget_advice}\n"
    "交通建议：{transportation}\n"
    "美食推荐：{food}\n"
    "文化参观：{culture}\n\n"
    "请用流畅的段落组织成一份详细的旅行计划，包含每日行程安排和预算分配建议。"
)
planner_chain = planner_prompt | llm | StrOutputParser()

# ==================== 6. 旅行计划检测 ====================
def is_travel_plan(question: str) -> bool:
    """检测用户是否在请求完整旅行计划（含目的地+天数+预算等）"""
    keywords = ["天", "日", "预算", "元", "旅行计划", "行程", "攻略", "规划"]
    return sum(1 for kw in keywords if kw in question) >= 2

# ==================== 7. 路由分发 ====================
async def dispatch(x: dict) -> str:
    """
    两种模式：
      旅行计划模式 → 全顾问并发 → planner_chain 生成结构化计划
      普通模式     → 主管决策 → 单顾问直调 / 多顾问并发拼接
    """
    question = x["question"]
    is_plan = is_travel_plan(question)

    # ── 旅行计划生成器 ──
    if is_plan:
        selected = list(ADVISOR_MAP.keys())
        days, budget, place = parse_travel_params(question)
        print(f"\n[分发决策] 🗺️  旅行计划模式 → {days}天 | {budget} | {place}")
        print(f"[分发决策] 并发调用全部 {len(selected)} 个顾问...")

        # 收集每个顾问的结果，按名字存储
        async def call_one(name):
            result = await ADVISOR_MAP[name][1].ainvoke({"question": question})
            return name, result

        results = await asyncio.gather(*[call_one(n) for n in selected])
        advisor_results = dict(results)

        # 汇总师整合为结构化计划
        plan = await planner_chain.ainvoke({
            "days": days,
            "budget": budget,
            "place": place,
            "destination": advisor_results.get("destination", ""),
            "budget_advice": advisor_results.get("budget", ""),
            "transportation": advisor_results.get("transportation", ""),
            "food": advisor_results.get("food", ""),
            "culture": advisor_results.get("culture", ""),
        })
        return plan

    # ── 普通模式：主管决策 ──
    advisors_raw = x.get("advisors", "")
    names = [w.strip().lower() for w in re.split(r"[,，、\s]+", advisors_raw)]
    selected = [n for n in names if n in ADVISOR_MAP]

    if not selected:
        return "【系统回复】您好，我们是旅游智能问答系统，您的问题超出了我们的服务范围。"
    print(f"\n[分发决策] 主管选择: {[ADVISOR_MAP[n][0] for n in selected]}")

    # 单顾问
    if len(selected) == 1:
        name = selected[0]
        label = ADVISOR_MAP[name][0]
        result = await ADVISOR_MAP[name][1].ainvoke({"question": question})
        return f"【{label}回复】\n{result}"

    # 多顾问并发 → 拼接
    async def call_one(name):
        label = ADVISOR_MAP[name][0]
        result = await ADVISOR_MAP[name][1].ainvoke({"question": question})
        return f"【{label}回复】\n{result}"

    results = await asyncio.gather(*[call_one(n) for n in selected])
    return "\n\n".join(results)

# ==================== 8. 组装管道 ====================
context_chain = {
    "question": RunnablePassthrough(),
    "advisors": supervisor_chain,
}
final_pipeline = context_chain | RunnableLambda(dispatch)

# ==================== 8. 交互循环 ====================
async def main():
    print("\n" + "=" * 50)
    print("  旅游规划智能分发系统")
    print("  已接入: 目的地 | 预算 | 交通 | 美食 | 文化")
    print("  输入 'exit' 退出")
    print("=" * 50)

    while True:
        user_input = input("\n👤 我: ")
        if user_input.lower() == "exit":
            print("再见!")
            break
        if not user_input.strip():
            continue

        try:
            response = await final_pipeline.ainvoke(user_input)
            print(f"🤖 AI:\n{response}")
        except Exception as e:
            print(f"❌ 运行出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())
