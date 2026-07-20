import pymysql

conn = pymysql.connect(
    host="192.168.0.43",
    port=3306,
    user="root", 
    password="123456", 
    charset="utf8mb4",
    database="test_db"          # 指定已存在的数据库
   
)
cursor = conn.cursor()

# 创建数据表
students_list= """
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '学号',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    age INT NOT NULL COMMENT '年龄',
    gender ENUM('男', '女') DEFAULT '男' COMMENT '性别',
    register_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

courses_list= """
CREATE TABLE IF NOT EXISTS courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '课程编号',
    course_name VARCHAR(100) NOT NULL COMMENT '课程名称',
    credit DECIMAL(3,1) NOT NULL COMMENT '学分'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# 3. 执行建表（逐条执行）
cursor.execute(students_list)
print("students表创建成功")
cursor.execute(courses_list)
print("courses表创建成功")


cursor.close()
conn.close()