'''
1. check_valid_score(score, max_score)  → 校验成绩是否在合法范围（0~满分）
2. calc_percentage(score, max_score)    → 计算得分率 = 分数/满分 × 100%
3. save_record(record_info)             → 使用 with 追加写入 exam_records.txt
4. read_all_records()                   → 使用 with 读取全部成绩记录
5. get_excellent_students(score_dict, threshold)  → 列表推导式筛选达到优秀的学生
6. report_card_generator(student_list)  → 生成器，yield 格式化成绩单字符串
7. input_score_thread_safe(student_name, subject, score)  → 线程锁安全录入成绩
8. multi_thread_input_test()            → 创建2个线程并发录入测试
'''
import threading
record_lock=threading.Lock()
student_records = {"张三": {"语文": 0, "数学": 0,"英语":0}} # 全局共享成绩字典，格式：{"张三": {"语文": 0, "数学": 0}}
# from subjects.base_exam import BaseExam

def check_valid_score(score,max_score):
    if score<=0 or score>max_score:
        print("成绩不在合法范围内")
    else:
        return True

def calc_percentage(score,max_score):
    return f"得分率为{score/max_score*100:.2f}%"

def save_records(record_info):
    with open("exam_records.txt","a",encoding="utf-8") as f:
        f.write(record_info + "\n")
    print("成绩保存成功,文件已自动关闭")
def read_all_records():
    print("读取所有成绩记录")
    with open("exam_records.txt","r",encoding="utf-8") as f:
        content=f.readlines()
        return [line.strip() for line in content]
            
#输入({"张三": 90, "李四": 78, "王五": 92, "陈六": 88},90)，返回['张三', '王五']
def get_excellent_students(score_dict, threshold): # 筛选出达到优秀的学生
    if not isinstance(score_dict,dict):
        raise TypeError("score_dict必须是字典类型")
    excellent_data={student_name:score for student_name,score in score_dict.items() if score>=threshold}
    return list(excellent_data.keys())

    
#list格式应该为[("张三","语文",100),("张三","数学",90)]
def report_card_generator(student_list): #生成器，yield 格式化成绩单字符串
    for student in student_list:
        yield f"{student[0]}的{student[1]}成绩为{student[2]}"

#yuwenexam = BaseExam("语文",100,"张三")
#yuwenexam.input_score(80)
def input_score_thread_safe(student_name, subject, score): #线程锁安全录入成绩
    with record_lock:
        if student_name not in student_records:
            student_records[student_name] = {}
        student_records[student_name][subject] = score
        print(f"成绩录入成功")
        info = f"{student_name},{subject},{score}"
        save_records(info)
        print(info)

def multi_thread_input_test(): #创建2个线程并发录入测试
    thread1 = threading.Thread(target=input_score_thread_safe, args=("张三", "语文", 90))
    thread2 = threading.Thread(target=input_score_thread_safe, args=("张三", "数学", 85))
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    print("所有线程完成")


if __name__ == "__main__":
    #1.测试成绩是否在合法范围
    # check_valid_score(90,100)
    # print(calc_percentage(90,100))
    #2.测试文件操作
    # save_records("张三,数学,90")
    # save_records("张三,英语,80")
    # read_all_records()
    # 3.测试筛选优秀学生
    # print(get_excellent_students({"张三": 90, "李四": 78, "王五": 92, "陈六": 88},90))
    # 4.测试生成器
    # for report_card in report_card_generator([("张三","语文",100),("张三","数学",90)]):
    #     print(report_card)
    # 5.测试线程锁安全录入成绩
    # input_score_thread_safe("张三","英语",80)
    print("成绩录入前：",student_records)
    multi_thread_input_test()
    print("成绩录入后：",student_records)
    

    
