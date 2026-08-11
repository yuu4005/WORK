'''
基于现有的
华为的年报下载下来，选择一个合适的分块策略，跑通基本的rag流程，
embedding（https://huggingface.co/BAAI/bge-large-zh/tree/main）本地加载。
升阶优化：稠密检索 + 稀疏检索 RRF 融合 + reranker 模型精排
'''

import os
import torch
import numpy as np
from dotenv import load_dotenv

from transformers import AutoModelForSequenceClassification, AutoTokenizer
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ===================== 配置 =====================
load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

local_embed_path = "D:/ai_models/bge-large-zh"
local_rerank_path = "D:/ai_models/bge-reranker-base"  # 本地重排序模型路径

# 检索参数
TOP_K = 8            # 每路检索召回数量
RRF_K = 60           # RRF 平滑常数，避免排名为 0 时除零，抑制低排名文档贡献
FINAL_TOP_K = 5      # RRF 融合后保留条数
RERANK_TOP_K = 3     # 精排后最终输出条数

# ===================== 本地 Reranker 模型 =====================
class LocalReranker:
    """
    Cross-Encoder 架构的本地重排序模型。
    将 query 与每个候选文档拼接后直接打分，捕获深度语义交互，
    弥补双塔模型（Bi-Encoder）在精细匹配上的不足。
    """
    def __init__(self, model_path):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def rank(self, query, docs):
        """对候选文档列表逐一打分，返回按相关性降序排列的文档列表"""
        pairs = [[query, doc.page_content] for doc in docs]
        with torch.no_grad():
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=self.tokenizer.model_max_length,
            )
            scores = self.model(**inputs, return_dict=True).logits.view(-1).float()
            scores = scores.tolist()

        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in ranked]

# ===================== 工具函数 =====================
def get_all_docs(vectorstore):
    """从 Chroma 向量库提取全部文档，用于 BM25 构建索引"""
    data = vectorstore.get(include=["documents", "metadatas"])
    return [
        Document(page_content=d, metadata=m if m else {})
        for d, m in zip(data["documents"], data["metadatas"])
    ]

def format_docs(docs):
    return "\n\n".join(f"[分块{i+1}]\n{d.page_content}" for i, d in enumerate(docs))

# ===================== RRF 融合 + Reranker 检索 =====================
def rrf_hybrid_retrieve(query, vectorstore, bm25_retriever, reranker):
    """
    混合检索管线：
    1. 稠密检索（向量语义召回）
    2. 稀疏检索（BM25 关键词召回）
    3. RRF 倒数排名融合（不依赖绝对分值，对异构检索结果更鲁棒）
    4. Reranker 精排（Cross-Encoder 做最终语义把关）
    """
    # 1. 稠密检索
    dense_docs = vectorstore.similarity_search(query, k=TOP_K)

    # 2. 稀疏检索
    bm25_docs = bm25_retriever.invoke(query)

    # 3. RRF 融合：score(d) = Σ 1/(k + rank_i(d))
    rrf_scores = {}
    for i, doc in enumerate(dense_docs):
        cnt = doc.page_content
        rrf_scores[cnt] = rrf_scores.get(cnt, 0) + 1.0 / (RRF_K + i + 1)
    for i, doc in enumerate(bm25_docs):
        cnt = doc.page_content
        rrf_scores[cnt] = rrf_scores.get(cnt, 0) + 1.0 / (RRF_K + i + 1)

    # 收集去重后的候选文档及其 RRF 得分
    all_docs_dict = {}
    for doc in dense_docs + bm25_docs:
        cnt = doc.page_content
        all_docs_dict[cnt] = (rrf_scores.get(cnt, 0), doc)

    sorted_docs = sorted(all_docs_dict.values(), key=lambda x: x[0], reverse=True)
    fused_docs = [doc for _, doc in sorted_docs[:FINAL_TOP_K]]

    # 4. Reranker 精排
    reranked_docs = reranker.rank(query, fused_docs)
    return reranked_docs[:RERANK_TOP_K]

# ===================== 主流程 =====================
if __name__ == "__main__":
    # --- 阶段1：加载 PDF ---
    print("开始加载年报PDF文件")
    loader = PDFPlumberLoader("华为2025年年报_0401.pdf")
    documents = loader.load()
    print(f"成功加载 {len(documents)} 个页面")

    # --- 阶段2：分块 ---
    print("正在分块文档...")
    recursive_splitter = RecursiveCharacterTextSplitter(
        separators=["## ", "\n\n", "\n", "。", "，"],
        chunk_size=1024,
        chunk_overlap=200,
        length_function=len,
    )
    split_docs = recursive_splitter.split_documents(documents)
    print(f"成功分块 {len(split_docs)} 个文本块")

    # --- 阶段3：Embedding + Chroma 向量库 ---
    print("正在加载嵌入模型...")
    embeddings = HuggingFaceEmbeddings(
        model_name=local_embed_path,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    print("正在将文本块向量化并存入Chroma数据库...")
    vectorstore = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory="./chroma_db",
    )
    print(f"成功将 {vectorstore._collection.count()} 个文本块向量化并存入Chroma")

    # --- 阶段4：构建 BM25 稀疏检索器 ---
    print("正在构建BM25稀疏检索器...")
    all_docs = get_all_docs(vectorstore)
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = TOP_K
    print(f"BM25检索器就绪，基于 {len(all_docs)} 个文档")

    # --- 阶段5：加载 Reranker ---
    print("正在加载Reranker模型...")
    reranker = LocalReranker(local_rerank_path)
    print("Reranker模型加载完成")

    # --- 阶段6：RAG 问答 ---
    llm = ChatOpenAI(model=model_name, api_key=api_key, base_url=base_url)

    system_prompt = (
        "你是华为有限公司的内部智能人事/行政助手。\n"
        "请严格基于以下提供的公司年报内容回答用户问题。\n"
        "如果你在文档找不到答案，请直接说'根据提供的文档，我无法回答该问题'，绝不能凭空捏造信息。\n"
        "请在回答中标注参考了哪个分块。\n"
        "【参考文档内容】\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    query = "华为2025年的营收是多少，以及营收的组成部分有哪些?"

    # RRF 融合 + Reranker 检索
    final_docs = rrf_hybrid_retrieve(query, vectorstore, bm25_retriever, reranker)
    print(f"\nRRF融合 + Reranker精排完成，最终召回 {len(final_docs)} 条")
    for i, d in enumerate(final_docs):
        snippet = d.page_content[:80].replace("\n", " ")
        print(f"  [{i+1}] {snippet}...")

    rag_chain = (
        {"context": lambda x: format_docs(final_docs), "input": lambda x: x}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("\n================ 问答结果 ================")
    answer = rag_chain.invoke(query)
    print(answer)
