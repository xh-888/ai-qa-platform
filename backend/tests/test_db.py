# -*- coding: utf-8 -*-
"""数据库访问层单元测试"""
from db import get_schema, run_query


def test_run_query():
    cols, rows = run_query(
        "SELECT region, COUNT(*) AS 订单数 FROM orders GROUP BY region ORDER BY region"
    )
    assert cols == ["region", "订单数"]
    assert len(rows) == 4  # 华东/华北/华南/西南


def test_get_schema_contains_tables_and_enum_values():
    s = get_schema()
    assert "表 orders" in s
    assert "region 的取值" in s
    assert "华东" in s
    # name 字段是标识符，不应作为取值示例出现（噪音）
    assert "客户01" not in s
    assert "的取值: 客户" not in s


def test_run_query_is_readonly_enforced():
    # query_only 兜底：写操作应被数据库层面拒绝
    import sqlite3
    try:
        run_query("DROP TABLE orders")
        assert False, "写操作不应被允许"
    except sqlite3.DatabaseError:
        pass
