import pymysql

# 1. 连接数据库
conn = pymysql.connect(
    host="192.168.0.43",
    port=3306,
    user="root",
    password="123456",
    charset="utf8mb4",
    database="test_db"

  
)
cursor = conn.cursor()
 # 增加学生
insert_student = """
    INSERT INTO students (id, name, age, gender) VALUES (%s, %s, %s,%s)
    """
cursor.execute(insert_student, (3, '小明', 20, '男'))
print(f"插入学生成功")
cursor.execute(insert_student, (4, '小红', 22, '女'))
print(f"插入学生成功")
conn.commit()
# 查询所有学生
all_student="SELECT * FROM students"
cursor.execute(all_student)
print("查询所有学生成功")
student_age ="SELECT * FROM students WHERE age > 18"
cursor.execute(student_age)
print("查询年龄大于18的学生成功")


# 更新某学生的年龄
update_sql = "UPDATE students SET age = %s WHERE name = %s"
cursor.execute(update_sql, (21, '张三'))
print("更新成功，张三的年龄已改为21")
conn.commit()
  
# 验证更新结果
cursor.execute("SELECT name, age FROM students WHERE name = '张三'")


# 删除
delete_sql = "DELETE FROM students WHERE name=%s"
cursor.execute(delete_sql, ('张三',))
conn.commit()
# 查看剩余学生
cursor.execute("SELECT * FROM students")



cursor.close()
conn.close()
