import pymysql

conn = pymysql.connect(
    host="192.168.0.43",
    port=3306,
    user="root", 
    password="123456", 
    charset="utf8mb4",
   
)
cursor = conn.cursor()

# 创建数据库
sql1 = "CREATE DATABASE IF NOT EXISTS test_db DEFAULT CHARSET=utf8mb4;"
sql2 = "CREATE DATABASE IF NOT EXISTS student_db DEFAULT CHARSET=utf8mb4;"
cursor.execute(sql1)
print("test_db数据库创建成功")
cursor.execute(sql2)
print("student_db数据库创建成功")


cursor.close()
conn.close()