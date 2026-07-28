'''
**任务描述**: 使用加州房价数据集,完成以下任务:
1. 加载数据并进行探索性分析
2. 进行特征工程(标准化、特征选择)
3. 使用线性回归、决策树、随机森林分别训练模型
4. 比较三种模型的性能(MSE、R²)
5. 输出特征重要性排序
'''

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ====== 1. 加载数据 & 探索性分析 ======
housing = fetch_california_housing()
X = pd.DataFrame(housing.data, columns=housing.feature_names)
y = housing.target

print("="*50)
print("加州房价数据集")
print("="*50)
print(f"数据形状: {X.shape}")
print(f"目标变量均值: {y.mean():.2f} (单位: 10万美元)")
print(f"特征说明: {', '.join(housing.feature_names)}")

# ====== 2. 划分数据集 ======
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ====== 3. 特征工程 ======
print("\n--- 特征选择 ---")
selector = SelectKBest(score_func=f_regression, k=5)  # 选择5个最相关的特征
selector.fit(X_train, y_train)
selected_features = X.columns[selector.get_support()]
print(f"保留特征: {list(selected_features)}")

# 筛选特征
X_train_selected = selector.transform(X_train)
X_test_selected = selector.transform(X_test)

# 标准化
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_selected)
X_test_scaled = scaler.transform(X_test_selected)
print("特征标准化完成")

# ====== 4. 模型训练 ======
models = {
    '线性回归': LinearRegression(),
    '决策树': DecisionTreeRegressor(max_depth=5, random_state=42),
    '随机森林': RandomForestRegressor(n_estimators=100, random_state=42)
}

results = {}
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    results[name] = {'model': model, 'MSE': mse, 'R²': r2}
    print(f"{name} 训练完成 - MSE: {mse:.4f}, R²: {r2:.4f}")

# ====== 5. 模型性能对比 ======
print("\n" + "="*50)
print("模型性能对比")
print("="*50)
print(f"{'模型':<8} {'MSE':<10} {'R²':<10}")
for name, res in results.items():
    print(f"{name:<8} {res['MSE']:<10.4f} {res['R²']:<10.4f}")

# ====== 6. 特征重要性(基于随机森林) ======
print("\n--- 特征重要性排序 ---")
rf_model = results['随机森林']['model']
importances = rf_model.feature_importances_
indices = np.argsort(importances)[::-1]

# 打印排序
for i, idx in enumerate(indices):
    print(f"{i+1}. {selected_features[idx]:<15} 重要性: {importances[idx]:.4f}")

# 可视化
plt.figure(figsize=(10, 6))
plt.barh(range(len(selected_features)), importances[indices], align='center')
plt.yticks(range(len(selected_features)), [selected_features[i] for i in indices])
plt.xlabel('重要性')
plt.title('随机森林特征重要性')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=100)
plt.close()
print("特征重要性图已保存: feature_importance.png")

