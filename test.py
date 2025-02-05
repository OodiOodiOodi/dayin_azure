import psycopg2

try:
    # 尝试连接到数据库，这里需要根据你的实际情况修改连接参数
    conn = psycopg2.connect(
        database="postgres",
        user="postgres",
        password="zhang202902",
        host="localhost",
        port=5432
    )
    print("连接成功！")
    conn.close()
except psycopg2.Error as e:
    print(f"连接失败: {e}")

