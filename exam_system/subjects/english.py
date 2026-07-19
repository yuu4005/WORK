import sys
import os
# 添加项目根目录到路径，使直接运行此文件时能找到 shop_tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from subjects.base_exam import BaseExam

class EnglishExam(BaseExam):
    def __init__(self, subject_name:str,max_score:float,student_name:str):
        super().__init__(subject_name,max_score,student_name)
        self.listening_score = 0.0
        self.reading_score = 0.0
        self.writing_score = 0.0
       
        
    def get_grade(self,score)->str: 
        if score >= 90:
            return "优秀"
        elif score >= 75:
            return "良好"
        elif score >= 60:  
            return "及格"
        else:
            return "不及格"

    def print_report_card(self):            # 打印"听力/阅读/写作分项成绩"标语
        score = self.get_score()
        if self.listening_score+self.reading_score+self.writing_score != score:
            print("成绩构成异常")
        else:
            print(f"学生：{self.student_name},学科：{self.subject_name},听力成绩：{self.listening_score},阅读成绩：{self.reading_score},写作成绩：{self.writing_score}")

if __name__ == "__main__":
    english_exam = EnglishExam("英语",100,"张三")
    print(english_exam.get_grade(60))
    english_exam.print_report_card()
