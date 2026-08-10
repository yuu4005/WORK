'''
基于现有的
华为的年报下载下来，选择一个合适的分块策略，跑通基本的rag流程，
embedding（https://huggingface.co/BAAI/bge-large-zh/tree/main）本地加载。
项目代码架构改造（晚上）
'''

from langchain_community.document_loaders import PDFPlumberLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

from rank_bm25 import BM25Okapi
import numpy as np


print("开始加载年报PDF文件")
try:
    loader = PDFPlumberLoader("华为2025年年报_0401.pdf")
    documents = loader.load()
    print(f"成功加载 {len(documents)} 个页面")
except Exception as e:
    print(f"加载年报PDF文件失败出错: {e}")

#选择一个合适的分块策略
#使用递归分割
print("正在分块文档...")
recursive_splitter = RecursiveCharacterTextSplitter(
    separators=["## ", "\n\n", "\n", "。", "，"],
    chunk_size=1024,
    chunk_overlap=200,
    length_function=len
)
split_docs = recursive_splitter.split_documents(documents)
print(f"成功分块 {len(split_docs)} 个文本块")

#加载embedding模型
local_model_path = "D:/ai_models/bge-large-zh"
print("正在加载嵌入模型...")
embeddings = HuggingFaceEmbeddings(
    model_name=local_model_path,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

#将文本向量化并存入Chroma数据库
print("正在将文本块向量化并存入Chroma数据库...")
vectors = Chroma.from_documents(
    documents=split_docs,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
print(f"成功将 {vectors._collection.count()}个文本块向量化, 存入Chroma数据库")

#检索阶段
#大模型初始化
load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url
)

#定义提示模板
system_prompt = (
        "你是华为有限公司的内部智能人事/行政助手。\n"
        "请严格基于以下提供的公司年报内容回答用户问题。\n"
        "如果你在文档找不到答案，请直接说‘根据提供的文档，我无法回答该问题’，绝不能凭空捏造信息。\n"
        "请在回答中标注参考了哪个分块。\n"
        "【参考文档内容】\n"
        "{context}"
    )

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human","{input}"),
])

query = "华为2025年的营收是多少?"

#混合检索
#1.embedding相似检索,
dense_results = vectors.similarity_search_with_score(query, k=5)
dense_docs = [doc for doc, _ in dense_results]
dense_dist = np.array([s for _, s in dense_results])
dense_scores = 1.0 / (1.0 + dense_dist)  # 距离→相似度

print("向量相似度得分：", dense_scores)

#2.BM25检索
tokenized_corpus = [list(d.page_content) for d in split_docs]
bm25 = BM25Okapi(tokenized_corpus)
bm25_raw = bm25.get_scores(list(query))
doc_hash = {d.page_content[:80]: i for i, d in enumerate(split_docs)}
bm25_aligned = np.array([bm25_raw[doc_hash.get(d.page_content[:80], 0)] for d in dense_docs])
bm25_scores_norm = bm25_aligned / max(bm25_aligned.sum(), 1e-8)

print("BM25得分：", bm25_scores_norm)
#3.ybrid
hybrid_scores = 0.9 * bm25_scores_norm + 0.1 * dense_scores

best_idx = np.argsort(hybrid_scores)[::-1]
docs = [dense_docs[i] for i in best_idx]

def format_docs(docs):
    return "\n\n".join(f"[分块{i+1}]\n{d.page_content}" for i, d in enumerate(docs))

#将得到的相关文本docs加入到prompt中
rag_chain = (
        {"context": lambda x: format_docs(docs), "input": lambda x: x}
        | prompt
        | llm
        | StrOutputParser()
    )
    
print("混合检索结果：")
answer = rag_chain.invoke(query)
print(answer)
