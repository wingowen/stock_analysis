import sqlite3

# 连接数据库
conn = sqlite3.connect('stock_history.db')
cursor = conn.cursor()

# 查询表结构
print("表结构:")
cursor.execute("PRAGMA table_info(stock_history)")
columns = cursor.fetchall()
for column in columns:
    print(column)

# 查询数据数量
print("\n数据数量:")
cursor.execute("SELECT COUNT(*) FROM stock_history")
count = cursor.fetchone()[0]
print(f"总共有 {count} 条记录")

# 查询前5条数据
print("\n前5条记录:")
cursor.execute("SELECT * FROM stock_history LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(row)

# 查询指定股票的最新数据
print("\n股票 688323 的最新5条记录:")
cursor.execute("SELECT * FROM stock_history WHERE 股票代码 = '688323' ORDER BY 日期 DESC LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(row)

# 查询概念指数表结构
print("\n概念指数表结构:")
try:
    cursor.execute("PRAGMA table_info(concept_index_history)")
    columns = cursor.fetchall()
    for column in columns:
        print(column)
    
    # 查询概念指数数据数量
    print("\n概念指数数据数量:")
    cursor.execute("SELECT COUNT(*) FROM concept_index_history")
    count = cursor.fetchone()[0]
    print(f"总共有 {count} 条记录")
    
    # 查询概念指数前5条数据
    print("\n概念指数前5条记录:")
    cursor.execute("SELECT * FROM concept_index_history LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    
    # 查询指定概念指数的最新数据
    print("\n概念指数 人工智能 的最新5条记录:")
    cursor.execute("SELECT * FROM concept_index_history WHERE 概念名称 = '人工智能' ORDER BY 日期 DESC LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
except sqlite3.OperationalError as e:
    print(f"概念指数表不存在: {e}")

# 关闭连接
conn.close()
