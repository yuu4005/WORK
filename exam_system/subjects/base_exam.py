import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from abc import ABC, abstractmethod   
from grade_utils import input_score_thread_safe

class BaseExam(ABC):
    #类属性:
    passing_rate = 0.6  # 及格率（60%）
    #实例属性:
    def __init__(self,subject_name:str,max_score:float,student_name:str):
        self.subject_name = subject_name # 学科名称
        self.max_score = max_score    # 满分值
        self.student_name = student_name   # 学生姓名
        self.__score = 0      # 私有成绩，默认0
    
    #方法:
    def get_score(self) -> float:
        return self.__score
    
    def input_score(self,score:float):# 录入成绩，超出满分抛异常
        if not (0 <= score <= self.max_score):
            raise ValueError(f"成绩 {score} 超出满分范围(0 ~ {self.max_score})")       
        input_score_thread_safe(self.student_name, self.subject_name, score)
        self.__score = score
       
    @classmethod
    def set_passing_rate(cls, rate):           # 类方法
        cls.passing_rate = rate

    @staticmethod
    def check_student_name(name)->bool:       # 静态方法
        if not name or name.isspace():
            raise ValueError("学生名字不能为空")
        return name

    @abstractmethod
    def get_grade(score)->str:                # 抽象方法（子类必须实现等级规则）
        pass

    def calc_weighted_score(self,weight)->float:   # 计算加权分（如期末占70%）
        return self.__score * weight

    def print_report_card():                   # 通用成绩单打印
        score = self.get_score()
        print(f"学生：{self.student_name},学科：{self.subject_name},成绩：{score}")

if __name__ == "__main__":
    print("===== base_exam.py 模块自测 =====\n")
    # 1. 测试静态方法：名称校验
    # print("--- 测试1：静态方法（名称校验）---")
    # print(BaseExam.check_student_name('张三'))  # True
    #print(f"BaseExam.check_student_name('') = {BaseExam.check_student_name('')}")  # False
    #print(f"BaseExam.check_student_name('  ') = {BaseExam.check_student_name('  ')}")  # False

    # 2. 测试类方法
    # print(f"初始及格率：{BaseExam.passing_rate}")
    # BaseExam.set_passing_rate(0.8)
    # print(f"设置后及格率：{BaseExam.passing_rate}")
    # # # 重置折扣为默认值
    # BaseExam.set_passing_rate(0.6)
   # 3. 测试抽象类实例化限制
    try:
        test = BaseExam("语文",70,"张三")
    except TypeError as e:
        print(f"抽象类无法实例化：{e}")

