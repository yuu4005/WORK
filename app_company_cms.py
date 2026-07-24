'''
📦 任务：技术公司官方网站与内容管理系统 (CMS)
### 📊 项目描述

某科技初创公司需要一个动态官网，用于展示公司简介、新闻公告，并提供后台内容管理功能。

### 🎯 任务要求

请独立编写 `app_company_cms.py`，实现以下功能：

1. **前台展示接口**：
  
  * `GET /`：展示公司首页（公司简介、最新 3 条新闻）。
  * `GET /api/news`：获取新闻列表（支持按发布时间倒序）。
  * `GET /api/news/<id>`：获取新闻详情。
2. **后台管理接口（需管理员权限）**：
  
  * 管理员账号预设：`admin / admin123`。
  * `POST /admin/news`：发布新新闻（字段：`title`, `content`, `category`）。
  * `DELETE /admin/news/<id>`：删除指定新闻。
  * 必须实现登录校验装饰器，非 `admin` 角色访问后台接口返回 `403 Forbidden`。
3. **数据持久化（可选挑战）**：
  
  * 使用 `sqlite3` 或 `SQLAlchemy` 将新闻数据存入本地文件 `cms.db`，替代内存字典，确保重启服务器后数据不丢失。
4. **测试提交**：
  
  * 提交完整的 `.py` 文件。
  * 附带 Postman 或 Curl 测试截图（包含成功登录、发布新闻、前台获取新闻的完整链路）。
  * 测试接口全部无误后，让ai生成前端页面，完成一个完整的CMS。

* * *

## 📝 提交要求

1. 所有代码必须包含详细的中文注释。
2. 运行前请确保已通过 `pip install flask requests` 安装依赖。
'''
from flask import Flask,request,session,jsonify
from sqlalchemy import create_engine,Column,Integer,String,DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from functools import wraps



#链接本地数据库
#1.创建数据库引擎
engine = create_engine("sqlite:///cms.db",echo=False)
#2.创建模型基类
Base = declarative_base()
#3.创建会话工厂
SessionLoc = sessionmaker(bind=engine,autocommit=False, autoflush=False,)

#定义模型
class News(Base):
  __tablename__ = "news_table"
  id = Column(Integer, primary_key=True,autoincrement=True)
  title = Column(String(255), nullable=False)
  content = Column(String(255), nullable=False)
  category = Column(String(255), nullable=False)
  publish_time = Column(DateTime, nullable=False, default=datetime.now)

class User(Base):
    __tablename__ = "user_table"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # admin 或 user

#定义实例
app = Flask(__name__) 
app.secret_key = secrets.token_hex(16)

@app.route("/admin/admin123",methods=["POST"])
def set_admin():
  #获取请求中用户名和密码
  data = request.get_json()
  #验证用户名和密码是否为空
  if not data or "username" not in data or "password" not in data:
    return jsonify({"code": 400, "msg": "用户名或密码为空"}), 400
  #在用户数据库中查询用户名是否存在，存在则返回"用户名已经为管理员"
  username = data["username"]
  password = data["password"]
  db = SessionLoc()
  #查询用户名是否存在
  if db.query(User).filter(User.username == username).first():
      db.close()
      return jsonify({"code": 400, "msg": "用户名已存在"}), 400
  #若用户名不存在则存入用户数据库，设置管理员名称为请求中的用户名
  #安全考虑：密码应加密存储
  new_user = User(
      username=username,
      password_hash=generate_password_hash(password),
      role="admin"
  )
  db.add(new_user)
  db.commit()
  db.close()
  return jsonify({"code": 200, "data": {"username": username, "role": "admin"}, "msg": "管理员账号设置成功"}), 200


#账号登录
@app.route('/login', methods=['POST'])
def login_temp():
  #获取请求中用户名和密码
  data = request.get_json()
  #验证用户名和密码是否为空
  if not data or "username" not in data or "password" not in data:
    return jsonify({"code": 400, "msg": "用户名或密码为空"}), 400
  #在用户数据库中查询用户名是否存在，不存在则返回"用户名不存在"
  username = data["username"]
  password = data["password"]
  db = SessionLoc()
  #查询用户名是否存在
  user = db.query(User).filter(User.username == username).first()
  db.close()

  if user and check_password_hash(user.password_hash, password):
    session["username"] = username
    session["role"] = user.role
    return jsonify({"code": 200, "data": {"username": username, "role": user.role}, "msg": "登录成功"}), 200
  else:
        return jsonify({"code": 400, "msg": "用户名或密码错误"}), 400
#登录校验装饰器，非 `admin` 角色访问后台接口返回 `403 Forbidden`
def admin_required(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    if "username" not in session :
      return jsonify({"code": 400, "msg": "请先登录"}), 400
    if session["role"] != "admin":
      return jsonify({"code": 403, "msg": "Forbidden"}), 403
    return f(*args, **kwargs)
  return decorated


#`POST /admin/news`：发布新新闻（字段：`title`, `content`, `category`）
@app.route("/admin/news",methods=["POST"])
@admin_required
def publish_news():
  data = request.get_json()
  if not data.get('title') or not data.get('content') or not data.get('category'):
        return jsonify({"code": 400, "msg": "标题、内容和分类不能为空"}), 400
  #创建新闻实例
  new_news = News(
    title=data["title"],
    content=data["content"],
    category=data["category"],
    publish_time=datetime.now()
  )
  #添加到数据库
  db = SessionLoc()
  db.add(new_news)
  db.commit()
  resonse_data={
    "id": new_news.id,
    "title": new_news.title,
    "content": new_news.content,
    "category": new_news.category,
    "publish_time": new_news.publish_time.isoformat()  # 转为字符串
  }
  db.close()
  #返回成功响应
  return jsonify({
        "code": 200,
        "data": resonse_data,
        "msg": "新闻发布成功"
    }), 200 
 
  

#`DELETE /admin/news/<id>`：删除指定新闻
@app.route("/admin/news/<int:id>",methods=["DELETE"])
@admin_required
def delete_news(id):
  #查询新闻是否存在
  db = SessionLoc()
  news = db.query(News).filter(News.id == id).first()
  if not news:
    db.close()
    return jsonify({"code": 404, "msg": "新闻不存在"}), 404
  #删除新闻
  db.delete(news)
  db.commit()
  db.close()
  return jsonify({"code": 200, "msg": "新闻删除成功"}), 200

#GET /`：展示公司首页（公司简介、最新 3 条新闻）
@app.route("/",methods=["GET"])
def index():
  #查询公司简介
  db = SessionLoc()
  news = db.query(News).order_by(News.publish_time.desc()).limit(3).all()
  #将新闻列表转换为字典列表
  news_list = [{
    "id": n.id,
    "title": n.title,
    "content": n.content,
    "category": n.category,
    "publish_time": n.publish_time.isoformat()  # 转为字符串
  } for n in news]
  db.close()
  #返回公司简介和最新 3 条新闻
  return jsonify({
        "code": 200,
        "data": {
            "公司简介":"这是一个公司",
            "最新 3 条新闻": news_list,
        },
        "msg": "公司首页展示成功"
    }), 200 

#`GET /api/news`：获取新闻列表（支持按发布时间倒序）。
@app.route("/api/news",methods=["GET"])
def get_news():
  #查询新闻列表
  db = SessionLoc()
  news = db.query(News).all()
  #将新闻列表转换为字典列表
  news_list = [{
    "id": n.id,
    "title": n.title,
    "content": n.content,
    "category": n.category,
    "publish_time": n.publish_time.isoformat()  # 转为字符串
  } for n in news]
  db.close()
  #返回新闻列表
  return jsonify({
        "code": 200,
        "data": news_list,
        "msg": "新闻列表获取成功"
    }), 200 

# `GET /api/news/<id>`：获取新闻详情。
@app.route("/api/news/<int:id>",methods=["GET"])
def get_news_detail(id):
  #查询新闻是否存在
  db = SessionLoc()
  news = db.query(News).filter(News.id == id).first()
  if not news:
    db.close()
    return jsonify({"code": 404, "msg": "新闻不存在"}), 404
  #将新闻转换为字典
  news_dict = {
    "id": news.id,
    "title": news.title,
    "content": news.content,
    "category": news.category,
    "publish_time": news.publish_time.isoformat()  # 转为字符串
  }
  db.close()
  #返回新闻详情
  return jsonify({
        "code": 200,
        "data": news_dict,
        "msg": "新闻详情获取成功"
    }), 200 

if __name__ == "__main__":
  #创建数据库表
  Base.metadata.create_all(bind=engine)
  #启动应用
  app.run(host="127.0.0.1", port=5006, debug=True)