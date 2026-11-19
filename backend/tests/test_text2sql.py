# -*- coding: utf-8 -*-
"""text2sql 核心逻辑单元测试"""
import pytest

import text2sql


def test_is_safe_sql_allow_select():
    assert text2sql.is_safe_sql("SELECT * FROM orders") is True
    assert text2sql.is_safe_sql("select sum(amount) as 销售额 from orders where region='华东'") is True
    assert text2sql.is_safe_sql("WITH t AS (SELECT 1) SELECT * FROM t") is True


def test_has_english_columns():
    assert text2sql._has_english_columns(["total_sales"]) is True
    assert text2sql._has_english_columns(["销售额", "订单数"]) is False
    assert text2sql._has_english_columns(["销售额", "region"]) is True
    assert text2sql._has_english_columns([]) is False
    assert text2sql._has_english_columns([None]) is False


@pytest.mark.parametrize("bad", [
    "DELETE FROM orders",
    "UPDATE orders SET amount=0",
    "INSERT INTO orders VALUES (1)",
    "DROP TABLE orders",
    "ALTER TABLE orders ADD COLUMN x",
    "CREATE TABLE x(y)",
    "TRUNCATE orders",
    "PRAGMA query_only=OFF",
    "ATTACH DATABASE 'x.db' AS x",
    "SELECT * FROM orders; DROP TABLE orders",
    "-- 注释掉\nDELETE FROM orders",  # 以注释开头，但含 delete
])
def test_is_safe_sql_reject(bad):
    assert text2sql.is_safe_sql(bad) is False


def test_ask_without_key(monkeypatch):
    monkeypatch.setattr(text2sql, "LLM_API_KEY", "")
    r = text2sql.ask("华东区销售额")
    assert "error" in r
    assert "未配置" in r["error"]
