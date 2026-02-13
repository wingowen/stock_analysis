import requests
from lxml import etree
import time
import random

# 目标URL
url = "https://q.10jqka.com.cn/gn/detail/code/301558/"

# 伪装浏览器的请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

# 随机延迟，模拟人类行为
time.sleep(random.uniform(1, 3))

try:
    # 发送请求
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = "utf-8"
    
    # 检查响应状态
    if response.status_code == 200:
        # 解析HTML
        tree = etree.HTML(response.text)
        
        # 使用XPath提取目标表格
        tbody = tree.xpath("/html/body/div[2]/div[4]/div[2]/table/tbody")
        
        if tbody:
            # 提取表格中的所有行
            rows = tbody[0].xpath("./tr")
            print(f"找到 {len(rows)} 行数据")
            
            # 遍历行，提取数据
            for i, row in enumerate(rows):
                # 提取每行的所有单元格
                cells = row.xpath("./td")
                cell_data = [cell.text.strip() if cell.text else '' for cell in cells]
                print(f"第 {i+1} 行: {cell_data}")
        else:
            print("未找到目标表格结构")
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}...")
        
except Exception as e:
    print(f"爬取过程中出错: {str(e)}")
