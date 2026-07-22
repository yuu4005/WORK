import requests
import time
import random
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. 数据库模型（讲义复用）
engine = create_engine("sqlite:///gov_news.db", echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class GovNews(Base):
    __tablename__ = "gov_news"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500))
    publish_time = Column(String(30))
    link = Column(String(800), unique=True)

Base.metadata.create_all(bind=engine)

# 2. 防反爬请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.gov.cn/"
}

def crawl_page(page_num):
    url = f"https://www.gov.cn/toutiao/liebiao/?page={page_num}"
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 403:
            print(f"第{page_num}页访问受限，触发反爬")
            return False
        resp.encoding = "utf-8"
        # BS4核心自学代码
        soup = BeautifulSoup(resp.text, "lxml")
        news_list = soup.select(".news_box .list_list_1.list_2 ul li")
        db = SessionLocal()
        for item in news_list:
            a_tag = item.select_one("h4 a")  
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            href = a_tag.get("href")
            if href.startswith("//"):      # 处理协议相对路径
                full_link = "https:" + href
            elif href.startswith("/"):
                full_link = "https://www.gov.cn" + href
            else:
                full_link = href   # 保留原样，但一般不会出
            pub_time = item.select_one("span.date").get_text(strip=True)
            db.add(GovNews(title=title, publish_time=pub_time, link=full_link))
        db.commit()
        db.close()
        print(f"第{page_num}页抓取完成")
        return True
    except Exception as e:
        print(f"第{page_num}页异常：{e}")
        return False

if __name__ == "__main__":
    # 仅抓取1-10页
    for page in range(1, 11):
        crawl_page(page)
        time.sleep(random.uniform(2, 4))
    print("抓取全部完成")
```