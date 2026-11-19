# -*- coding: utf-8 -*-
"""数据库访问层：连接、只读查询、表结构读取"""
import sqlite3
from functools import lru_cache

from config import DB_PATH

MAX_ROWS = 1000  # 单次查询最多返回行数，防止模型生成全表扫描拖垮服务


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    # 只读兜底：即使 SQL 校验被绕过，也写不进去（双重保险）
    conn.execute("PRAGMA query_only=ON")
    return conn


def run_query(sql, params=()):
    """执行只读查询，返回 (列名列表, 数据行列表)"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    columns = [d[0] for d in cur.description] if cur.description else []
    rows = [list(r) for r in cur.fetchmany(MAX_ROWS + 1)]
    conn.close()
    return columns, rows[:MAX_ROWS]


@lru_cache(maxsize=1)
def get_schema():
    """读取全部表结构，拼成给大模型的「菜单」描述（结果缓存，数据不变）。
    对取值较少（<=20 个）的文本列，附上去重后的实际取值，
    避免模型臆造枚举值（如把 region 写成 '华东区' 而库里存的是 '华东'）。
    排除 name 等标识符字段，避免噪音 token。"""
    conn = get_conn()
    cur = conn.cursor()
    tables = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    lines = []
    for (t,) in tables:
        cols = cur.execute(f'PRAGMA table_info("{t}")').fetchall()
        col_desc = ", ".join(f"{c[1]} {c[2]}" for c in cols)
        line = f"表 {t}({col_desc})"
        samples = []
        for c in cols:
            name, ctype = c[1], (c[2] or "").upper()
            if name.lower().endswith("name"):
                continue  # name 类字段是标识符不是枚举，喂给模型只会产生噪音
            if "CHAR" in ctype or "TEXT" in ctype:
                try:
                    vals = [str(r[0]) for r in cur.execute(
                        f'SELECT DISTINCT "{name}" FROM "{t}" LIMIT 21')]
                    if 1 < len(vals) <= 20:
                        samples.append(f"{name} 的取值: {', '.join(vals)}")
                except Exception:
                    pass
        if samples:
            line += "；" + "；".join(samples)
        lines.append(line)
    conn.close()
    return "\n".join(lines)
