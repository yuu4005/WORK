import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, DataCollatorWithPadding
import evaluate
import numpy as np
from datetime import datetime

# 0. 检测设备
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"使用设备: {device}")

# 1. 加载数据集
dataset = load_dataset("json", data_files={
    "train": "yelp_train.json",
    "validation": "yelp_test.jsonl"
})

# CPU训练，取少量数据快速出结果
dataset["train"] = dataset["train"].select(range(800))
dataset["validation"] = dataset["validation"].select(range(500))

print("训练数据量：", len(dataset["train"]))
print("验证数据量：", len(dataset["validation"]))

# 2. 加载分词器和模型（用distilbert，比bert-base小40%，CPU上快很多）
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name, num_labels=2
)

# 3. 数据预处理
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, max_length=128)

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# 4. 评估函数
accuracy_metric = evaluate.load("accuracy")
f1_metric = evaluate.load("f1")

def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=1)
    acc = accuracy_metric.compute(predictions=predictions, references=labels)
    f1 = f1_metric.compute(predictions=predictions, references=labels, average="weighted")
    return {"accuracy": acc["accuracy"], "f1": f1["f1"]}

# 5. 训练参数
training_args = TrainingArguments(
    output_dir="./bert_binary_cls",
    per_device_train_batch_size=4,
    per_device_eval_batch_size=8,
    num_train_epochs=2,
    eval_strategy="epoch",
    learning_rate= 3e-5,
    logging_steps=20,
    save_strategy="no",
    dataloader_num_workers=0,
)

# 6. 开始训练
data_collator = DataCollatorWithPadding(tokenizer)
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["validation"],
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)
trainer.train()

# 7. 迭代优化记录
log_history = trainer.state.log_history

hyperparams = {
    "model": model_name,
    "batch_size": training_args.per_device_train_batch_size,
    "epochs": training_args.num_train_epochs,
    "learning_rate": training_args.learning_rate,
    "max_length": 128,
    "train_samples": len(dataset["train"]),
    "eval_samples": len(dataset["validation"]),
}

eval_records = [r for r in log_history if "eval_loss" in r]

record_lines = []
record_lines.append("=" * 55)
record_lines.append("BERT 文本二分类 — 迭代优化记录")
record_lines.append("=" * 55)
record_lines.append("")
record_lines.append("【超参数】")
for k, v in hyperparams.items():
    record_lines.append(f"  {k}: {v}")
record_lines.append("")
record_lines.append(f"{'Epoch':<8} {'Loss':<12} {'Accuracy':<12} {'F1':<12}")
record_lines.append("-" * 44)

for r in eval_records:
    epoch = r.get("epoch", "?")
    loss = r.get("eval_loss", 0)
    acc = r.get("eval_accuracy", 0)
    f1 = r.get("eval_f1", 0)
    record_lines.append(f"{epoch:<8.2f} {loss:<12.4f} {acc:<12.4f} {f1:<12.4f}")

record_lines.append("=" * 55)
record_lines.append(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

record_text = "\n".join(record_lines)
print("\n" + record_text)

with open("training_record.txt", "a", encoding="utf-8") as f:
    f.write(record_text + "\n\n")
print(f"迭代记录已追加到: training_record.txt")

# 8. 保存模型和分词器
save_path = "./bert_binary_cls_saved"
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)
print(f"模型已保存到: {save_path}")
