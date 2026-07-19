import threading
from abc import ABC, abstractmethod

# 2. 第三方库（本项目暂未使用）
# import requests

# 3. 自定义包/模块
from subjects import BaseExam, ChineseExam, MathExam, EnglishExam
from grade_utils import student_records
from grade_utils import (
    check_valid_score,
    calc_percentage,
    save_records,  
    read_all_records,               
    get_excellent_students,
    report_card_generator,  
    input_score_thread_safe, 
    multi_thread_input_test     
)


def main():
    """程序主入口"""
    print("===== 学生成绩管理系统 =====")
    print("===== 1. 基础得分率计算测试 =====")
    print(calc_percentage(80, 100))
    print("===== 2. 成绩保存与读取测试 =====")
    save_records("张三,语文,80")
    read_all_records()
    print("===== 3. 多线程录入测试 =====")
    multi_thread_input_test()
    print("===== 4. 设置及格率为 0.65 =====")
    BaseExam.set_passing_rate(0.65)
    print(BaseExam.passing_rate)
    print("===== 5. 语文测试（创建、录入成绩、查看作文分、评定等级、保存记录） =====")
    print(f"当前记录：{student_records}")
    chinese_exam = ChineseExam("语文", 150, "张三",30)
    chinese_exam.input_score(80)
    print(f"{chinese_exam.student_name}语文成绩：{chinese_exam.get_score()}")
    print(f"作文分：{chinese_exam.essay_score}")
    print(chinese_exam.get_grade(80))
    print(f"当前记录：{student_records}")

    print("===== 6. 数学测试（创建、录入成绩、设置附加分、查看加权分、保存记录） =====")
    math_exam = MathExam("数学",150,"李四")
    math_exam.input_score(130)
    math_exam.set_bonus_points(10)
    print(f"{math_exam.student_name}数学成绩：{math_exam.get_score()},附加分：{math_exam.get_bonus_points()}")
    print(f"{math_exam.student_name}数学加权成绩：{math_exam.calc_weighted_score(0.5)}") 
    print(math_exam.get_grade(130))
    print(f"当前记录：{student_records}")
   
    print("===== 7. 英语测试（创建、录入成绩、打印分项成绩单、评定等级、保存记录） =====")
    english_exam = EnglishExam("英语",100,"王五")
    english_exam.input_score(90)
    english_exam.listening_score = 30
    english_exam.reading_score = 25
    english_exam.writing_score = 35
    english_exam.print_report_card()
    print(english_exam.get_grade(90))

    print("===== 8. 优秀学生筛选测试（用字典 + 列表推导式） =====")
    print(get_excellent_students({"张三": 90, "李四": 78, "王五": 92, "陈六": 88},90))

    print("===== 9. 成绩单生成器测试 =====")
    student_list = [(name, subject, score) 
                for name, subjects in student_records.items() 
                for subject, score in subjects.items()]

    # 调用生成器并遍历输出
    gen = report_card_generator(student_list)
    for record in gen:
        print(record)

    print("===== 10. 批量统计多态测试（3门学科各1份答卷，遍历调用 calc_weighted_score） =====")
    chinese_exam1 = ChineseExam("语文", 150, "s1",30)
    math_exam1 = MathExam("数学",150,"s2")
    english_exam1 = EnglishExam("英语",100,"s3")
    math_exam1.set_bonus_points(30)
    for exam in [chinese_exam1,math_exam1,english_exam1]:
        exam.input_score(100)
        print(f"{exam.student_name}成绩：{exam.get_score()},加权成绩：{exam.calc_weighted_score(0.7):.2f}")
    print(f"当前记录：{student_records}")   
    
if __name__ == "__main__":
    main()