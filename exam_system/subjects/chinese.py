import sys
import os
# 添加项目根目录到路径，使直接运行此文件时能找到 shop_tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from subjects.base_exam import BaseExam

class ChineseExam(BaseExam):
    def __init__(self, subject_name:str,max_score:float,student_name:str,essay_score:float):
        super().__init__(subject_name,max_score,student_name)
        self.essay_score = essay_score
        
    def get_grade(self,score)->str: 
        if score >= 135:
            return "优秀"
        elif score >= 120:
            return "良好"
        elif score >= 90:  
            return "及格"
        else:
            return "不及格"

if __name__ == "__main__":
    chinese_exam = ChineseExam("语文",150,"张三",45)
    chinese_exam.input_score(80)
    print(chinese_exam.get_grade(60))
  
