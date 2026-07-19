import sys
import os
# 添加项目根目录到路径，使直接运行此文件时能找到 shop_tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from subjects.base_exam import BaseExam

class MathExam(BaseExam):
    def __init__(self, subject_name:str,max_score:float,student_name:str):
        super().__init__(subject_name,max_score,student_name)
        self.__bonus_points = 0  # 附加分

    def get_bonus_points(self)->float:
        return self.__bonus_points
    def set_bonus_points(self,bonus_points:float):
        self.__bonus_points = bonus_points
        
    def get_grade(self,score)->str: 
        if score >= 140:
            return "优秀"
        elif score >= 120:
            return "良好"
        elif score >= 90:  
            return "及格"
        else:
            return "不及格"

    def calc_weighted_score(self,weight):# 数学加权分计算包含附加分
        self.__score = self.get_score()
        return weight * (self.__bonus_points+self.__score)


if __name__ == "__main__":
    math_exam = MathExam("数学",150,"张三")
    print(math_exam.get_grade(160))
    print(math_exam.get_score())
    math_exam.input_score(160)
    print(math_exam.get_score())
    print(math_exam.calc_weighted_score(0.5))

