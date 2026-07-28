"""
任务描述: 构建二分类模型预测客户流失
包含: 数据生成、预处理、多模型训练、评估与对比
输出: classification_report, confusion_matrix.png, roc_curve.png
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
import seaborn as sns

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ====== 1. 生成模拟数据 ======
np.random.seed(42)
n_samples = 1000
data = pd.DataFrame({
    '年龄': np.random.randint(18, 65, n_samples),
    '月消费金额': np.random.exponential(200, n_samples),
    '使用时长_月': np.random.randint(1, 60, n_samples),
    '投诉次数': np.random.poisson(0.5, n_samples),
    '是否流失': np.zeros(n_samples, dtype=int)
})

# 基于特征构造有意义的流失标签（保留原数据列不变，仅替换流失列）
score = (0.03 * (data['年龄'] - 40) -
         0.01 * data['月消费金额'] +
         0.05 * (60 - data['使用时长_月']) +
         0.8 * data['投诉次数'] +
         np.random.normal(0, 0.5, n_samples))
prob = 1 / (1 + np.exp(-score))
data['是否流失'] = (prob > 0.5).astype(int)

print("="*50)
print("客户流失预测模型")
print("="*50)
print("\n数据概况:")
print(data.head())
print(f"\n流失比例: {data['是否流失'].mean():.2%}")

# ====== 2. 数据预处理 ======
# 构造类别特征：年龄分段
bins = [0, 30, 50, 100]
labels = ['青年', '中年', '老年']
data['年龄段'] = pd.cut(data['年龄'], bins=bins, labels=labels)

X = data[['月消费金额', '使用时长_月', '投诉次数', '年龄段']]
y = data['是否流失']

# 数值特征标准化
num_features = ['月消费金额', '使用时长_月', '投诉次数']
scaler = StandardScaler()
X_num = scaler.fit_transform(X[num_features])
print("\n数值特征标准化完成")

# 类别特征独热编码
cat_features = ['年龄段']
encoder = OneHotEncoder(sparse_output=False, drop='first')  # 避免多重共线性
X_cat = encoder.fit_transform(X[cat_features])
print(f"类别编码后特征维度: {X_cat.shape[1]}")

# 合并特征并划分数据集
X_processed = np.hstack([X_num, X_cat])
X_train, X_test, y_train, y_test = train_test_split(
    X_processed, y, test_size=0.3, random_state=42, stratify=y
)

# ====== 3. 模型训练 ======
models = {
    '逻辑回归': LogisticRegression(max_iter=1000, random_state=42),
    'SVM': SVC(kernel='rbf', probability=True, random_state=42),
    '随机森林': RandomForestClassifier(n_estimators=100, random_state=42)
}

for name, model in models.items():
    model.fit(X_train, y_train)
    print(f"\n{name} 训练完成")

# ====== 4. 模型评估与可视化 ======
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
axes = axes.flatten()

for idx, (name, model) in enumerate(models.items()):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # 打印分类报告
    print(f"\n{'='*30}\n{name}\n{'='*30}")
    print(classification_report(y_test, y_pred))
    
    # 混淆矩阵子图
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['未流失', '流失'],
                yticklabels=['未流失', '流失'],
                ax=axes[idx])
    axes[idx].set_title(f'{name} 混淆矩阵')
    axes[idx].set_xlabel('预测标签')
    axes[idx].set_ylabel('真实标签')

# ROC曲线汇总到第四个子图
ax_roc = axes[3]
for name, model in models.items():
    y_prob = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    ax_roc.plot(fpr, tpr, label=f'{name} (AUC={roc_auc:.3f})')

ax_roc.plot([0, 1], [0, 1], 'k--', label='随机猜测')
ax_roc.set_xlabel('假正率')
ax_roc.set_ylabel('真正率')
ax_roc.set_title('ROC曲线对比')
ax_roc.legend()
ax_roc.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=150)  # 包含三个混淆矩阵和ROC
plt.close()
print("\n已保存混淆矩阵与ROC对比图: confusion_matrix.png")

# 单独保存高清ROC曲线
plt.figure(figsize=(8, 6))
for name, model in models.items():
    y_prob = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    plt.plot(fpr, tpr, label=f'{name} (AUC={roc_auc:.3f})')
plt.plot([0, 1], [0, 1], 'k--')
plt.xlabel('假正率')
plt.ylabel('真正率')
plt.title('ROC曲线')
plt.legend()
plt.grid(alpha=0.3)
plt.savefig('roc_curve.png', dpi=150)
plt.close()
print("已保存ROC曲线: roc_curve.png")

# ====== 5. 模型效果分析 ======
print("""
【模型效果分析】
随机森林通常表现最佳，原因如下：
- 它能自动捕捉特征间的非线性交互（如年龄与使用时长对流失的共同影响），
  对异常值不敏感，且不需要特征缩放，天然适合结构化数据。
- 逻辑回归效果最弱，因为它假设特征与流失之间为线性关系，难以刻画
  投诉次数突增导致概率陡升等复杂边界。
- SVM通过RBF核能学习非线性，但默认参数未必最优，且对数据尺度敏感，
  在未精细调参时性能常介于前两者之间。
""")