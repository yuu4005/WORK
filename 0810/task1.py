'''
* **测试不同文本的向量表示**：
  
  * 编码以下5个句子，输出向量维度和前5个数值
  * "Java开发工程师要求3年以上经验"
  * "Python岗位要求熟悉Django框架"
  * "公司节日福利包括购物卡和电影票"
  * "员工享受带薪年假和五险一金"
  * "Java高级工程师需精通JVM调优"
* **计算语义相似度**：
  
  * 计算上述5个句子两两之间的余弦相似度
  * 输出相似度矩阵（5x5）
  * 找出最相似的句子对
* **实战问答**：
  
  * 用户提问："Java岗位有什么要求？"
  * 计算该问题与5个句子的相似度，返回最相似的Top 2

  * 使用 `sklearn.metrics.pairwise.cosine_similarity` 计算相似度
* 使用 `numpy` 进行数组操作
'''
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from langchain_huggingface import HuggingFaceEmbeddings

# 初始化嵌入模型
local_model_path = "./bge-large-zh"
print("▶ 正在加载嵌入模型...")
embeddings = HuggingFaceEmbeddings(
    model_name=local_model_path,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

# 编码文本
texts= [
    "Java开发工程师要求3年以上经验",
    "Python岗位要求熟悉Django框架",
    "公司节日福利包括购物卡和电影票",
    "员工享受带薪年假和五险一金",
    "Java高级工程师需精通JVM调优"
]

# 批量编码
vectors = embeddings.embed_documents(texts)

# 查看向量信息
print(f"向量数量: {len(vectors)}")
print(f"向量维度: {len(vectors[0])}")
print("第一个向量（前10维）:", vectors[0][:10])


# ---------- 3. 计算两两余弦相似度矩阵 ----------
vector_matrix = np.array(vectors)   # 转为 numpy 数组方便计算
sim_matrix = cosine_similarity(vector_matrix)  # 5x5

print("\n========== 相似度矩阵 (5x5) ==========")
np.set_printoptions(precision=4, suppress=True)  # 设置打印精度
print(sim_matrix)

# ---------- 4. 找出最相似的句子对（排除自身） ----------
# 将上三角（不包括对角线）的索引和值提取出来
rows, cols = np.triu_indices_from(sim_matrix, k=1)  # k=1 排除对角线
upper_tri_values = sim_matrix[rows, cols]
max_idx = np.argmax(upper_tri_values)
pair = (rows[max_idx], cols[max_idx])
print(f"\n最相似的句子对: 文本{pair[0]+1} 和 文本{pair[1]+1}, 相似度 = {upper_tri_values[max_idx]:.4f}")
print(f"  - \"{texts[pair[0]]}\"")
print(f"  - \"{texts[pair[1]]}\"")

# ---------- 5. 实战问答：用户提问 ----------
user_query = "Java岗位有什么要求？"
query_vector = embeddings.embed_query(user_query)  # 单个文本用 embed_query
query_vector = np.array(query_vector).reshape(1, -1)  # 转为二维数组（1行）

# 计算查询与所有文档的相似度
sim_scores = cosine_similarity(query_vector, vector_matrix)[0]  # 一维数组

# 获取相似度最高的 Top-2 索引
top2_indices = np.argsort(sim_scores)[-2:][::-1]  # 降序

print("\n========== 用户问答 ==========")
print(f"用户问题: \"{user_query}\"")
print("Top-2 最相似句子:")
for rank, idx in enumerate(top2_indices, 1):
    print(f"  {rank}. 相似度 {sim_scores[idx]:.4f} -> \"{texts[idx]}\"")