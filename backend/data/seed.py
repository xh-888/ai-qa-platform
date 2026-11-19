# -*- coding: utf-8 -*-
"""
AI问数 - 企业级销售经管数据平台 示例数据生成脚本

运行：python seed.py
产出：同目录下 sales.db（SQLite 单文件数据库）

设计说明：
  - 4 张表：customers(客户) / products(产品) / orders(订单) / sales_goals(销售目标)
  - orders.region 为冗余字段（真实项目可从 customers 关联获取，这里冗余是为了
    让 text2sql 既能回答简单查询，也能回答跨表 JOIN 查询，覆盖两种问数场景）
"""
import os
import random
import sqlite3
from datetime import date, timedelta

# 固定随机种子：保证每次生成的数据完全一致，便于复现与测试
random.seed(42)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales.db")

REGIONS = ["华东", "华南", "华北", "西南"]
INDUSTRIES = ["制造", "零售", "金融", "互联网", "医疗"]
CATEGORIES = ["软件", "硬件", "服务", "耗材"]
STATUSES = ["已完成", "进行中", "已取消"]
STATUS_WEIGHTS = [80, 12, 8]  # 各状态占比（%）

PRODUCTS = [
    ("ERP系统", "软件"), ("云服务器", "硬件"), ("数据分析服务", "服务"),
    ("打印耗材", "耗材"), ("OA办公套件", "软件"), ("网络安全设备", "硬件"),
    ("数据库软件", "软件"), ("运维服务", "服务"), ("智能网关", "硬件"),
    ("显示设备", "硬件"),
]


def create_tables(conn):
    cur = conn.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS sales_goals;
    DROP TABLE IF EXISTS customers;
    DROP TABLE IF EXISTS products;

    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        name        TEXT NOT NULL,
        region      TEXT NOT NULL,
        industry    TEXT NOT NULL
    );

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        name        TEXT NOT NULL,
        category    TEXT NOT NULL,
        price       REAL NOT NULL
    );

    CREATE TABLE orders (
        order_id    INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        product_id  INTEGER NOT NULL,
        order_date  TEXT NOT NULL,
        region      TEXT NOT NULL,
        quantity    INTEGER NOT NULL,
        amount      REAL NOT NULL,
        status      TEXT NOT NULL
    );

    CREATE TABLE sales_goals (
        goal_id       INTEGER PRIMARY KEY,
        region        TEXT NOT NULL,
        year_month    TEXT NOT NULL,
        target_amount REAL NOT NULL
    );
    """)
    conn.commit()


def seed_customers(cur):
    rows = []
    for i in range(1, 21):
        region = random.choice(REGIONS)
        rows.append((i, f"客户{i:02d}", region, random.choice(INDUSTRIES)))
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?)", rows)
    return rows


def seed_products(cur):
    rows = []
    for i, (name, category) in enumerate(PRODUCTS, start=1):
        base = random.choice([800, 3000, 12000, 25000, 50000])
        price = round(base * random.uniform(0.85, 1.15), 2)
        rows.append((i, name, category, price))
    cur.executemany("INSERT INTO products VALUES (?,?,?,?)", rows)
    return rows


def seed_orders(cur, customers, products):
    # 动态日期范围：从 2026-05-01 到「今天」，保证任意时间运行都有本月数据可查
    start = date(2026, 5, 1)
    end = date.today()
    days = (end - start).days
    price_map = {p[0]: p[3] for p in products}

    rows = []
    for order_id in range(1, 421):
        customer_id = random.randint(1, len(customers))
        region = customers[customer_id - 1][2]  # 冗余区域，取自客户
        product_id = random.randint(1, len(products))
        order_date = (start + timedelta(days=random.randint(0, days))).isoformat()
        quantity = random.randint(1, 8)
        amount = round(price_map[product_id] * quantity, 2)
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        rows.append((order_id, customer_id, product_id, order_date,
                     region, quantity, amount, status))
    cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)", rows)


def seed_goals(cur):
    # 动态生成月份：与订单同区间（2026-05 至今），每月每区域一条目标
    rows = []
    gid = 1
    start = date(2026, 5, 1)
    end = date.today()
    months, ym = [], start
    while ym <= end:
        months.append(ym.strftime("%Y-%m"))
        # 下一个 1 号
        ym = date(ym.year + (ym.month == 12), (ym.month % 12) + 1, 1)
    for m in months:
        for region in REGIONS:
            target = random.randint(80, 200) * 10000  # 80万 ~ 200万
            rows.append((gid, region, m, target))
            gid += 1
    cur.executemany("INSERT INTO sales_goals VALUES (?,?,?,?)", rows)


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    create_tables(conn)
    customers = seed_customers(cur)
    products = seed_products(cur)
    seed_orders(cur, customers, products)
    seed_goals(cur)
    conn.commit()

    print("=== 各表数据行数 ===")
    for table in ["customers", "products", "orders", "sales_goals"]:
        n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<12} {n} 行")
    conn.close()
    print("已生成数据库:", DB_PATH)


if __name__ == "__main__":
    main()
