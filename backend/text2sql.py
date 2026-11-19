# -*- coding: utf-8 -*-
"""Text2SQL 核心：大模型生成 SQL + 安全校验 + 执行"""
import json
import re

from openai import OpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from db import get_schema, run_query

SYSTEM_PROMPT = """你是销售数据平台的 SQL 助手，使用 SQLite 方言。根据用户问题和数据库表结构，生成一条 SQLite 查询，并给出合适的展示方式。

严格规则：
1. 只能生成 SELECT 查询，禁止任何修改数据的语句（INSERT/UPDATE/DELETE/DROP 等）。
2. 只用表结构里存在的表和字段，禁止臆造。
3. 金额字段 amount、price 单位都是元。
4. SELECT 的每一列都必须用中文别名（AS 中文名），如 SUM(amount) AS 销售额、COUNT(*) AS 订单数，禁止把 total_sales 等英文名暴露给用户。
5. 只能输出纯 JSON（不要 markdown 代码块），格式：
{"sql": "SELECT ...", "chart": "bar", "explanation": "简短说明"}
其中 chart 必须是 number、bar、line、pie、table 这五个词中的「一个」，不能写多个。
6. 若问题无法用现有数据回答，sql 置空，explanation 说明原因。
7. 查询结果默认限制在 500 行以内（在 SQL 里加 LIMIT 500）。

SQLite 日期处理（务必遵守）：
- SQLite 没有 DATE_FORMAT 函数，请使用 strftime。
- 「上月」写成：strftime('%Y-%m', order_date) = strftime('%Y-%m', 'now', '-1 month')
- 「本月」写成：strftime('%Y-%m', order_date) = strftime('%Y-%m', 'now')
- 按月分组或取月份用：strftime('%Y-%m', order_date)
- 禁止写 order_date = date('now','-1 month','start of month') 这类只匹配某一天的写法。
"""


def _client():
    return OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)


def generate_sql(question, error_hint=None):
    """调用大模型，把自然语言问题翻译成 SQL + 图表类型。
    error_hint 不为空时，说明上一次尝试失败，让模型自我修正。"""
    schema = get_schema()
    user_content = f"数据库表结构：\n{schema}\n\n用户问题：{question}"
    if error_hint:
        user_content += (
            f"\n\n上一次尝试失败，请修正后重新输出。\n失败原因：{error_hint['detail']}"
        )
        if error_hint.get("sql"):
            user_content += f"\n上一次 SQL：{error_hint['sql']}"
    resp = _client().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
        max_tokens=800,
    )
    content = resp.choices[0].message.content.strip()
    # 去掉可能包裹的 markdown 代码块
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"模型返回了非法 JSON：{str(e)[:80]}") from e
    if not isinstance(result, dict) or "sql" not in result:
        raise ValueError("模型返回的 JSON 缺少 sql 字段")
    # chart 归一化：模型偶尔返回 "table|bar" 之类多值，取第一个合法片段
    _VALID_CHARTS = ("pie", "line", "bar", "number", "table")
    chart = str(result.get("chart", "table")).strip()
    if chart not in _VALID_CHARTS:
        chart = next((c for c in _VALID_CHARTS if c in chart), "bar")
    result["chart"] = chart
    return result


def is_safe_sql(sql):
    """安全校验：只放行 SELECT / WITH 查询，拦截一切写操作，防注入"""
    s = sql.strip().rstrip(";").lower()
    if not (s.startswith("select") or s.startswith("with")):
        return False
    forbidden = ["insert", "update", "delete", "drop", "alter",
                 "create", "truncate", "attach", "detach", "pragma"]
    for w in forbidden:
        if w in s:
            return False
    return True


def _has_english_columns(columns):
    """检查结果列名是否含纯英文列（违反「中文别名」规则，需要模型重生成）"""
    return any(isinstance(c, str) and c.strip() and c.isascii() for c in columns)


def ask(question):
    """对外主入口：问题 -> 大模型 -> SQL -> 安全校验 -> 执行 -> 结果。
    失败时把原因喂回大模型自我修正，最多重试 1 次。"""
    if not LLM_API_KEY:
        return {"error": "未配置大模型 API Key，请在 backend/.env 填写 LLM_API_KEY"}

    error_hint = None
    for attempt in range(2):
        try:
            result = generate_sql(question, error_hint)
        except ValueError as e:
            # JSON 解析失败 / 缺字段：喂回模型重试一次（比 SQL 执行失败更常见，最该重试）
            if attempt == 0:
                error_hint = {
                    "detail": f"输出无法解析（{e}），请严格只输出一个含 sql/chart/explanation 的 JSON 对象"
                }
                continue
            return {"error": "大模型输出解析失败", "detail": str(e)}
        except Exception as e:
            return {"error": "大模型调用失败", "detail": str(e)}

        sql = (result.get("sql") or "").strip()
        if not sql:
            return {"error": "无法生成查询", "detail": result.get("explanation", "")}
        if not is_safe_sql(sql):
            return {"error": "生成的 SQL 不安全，已拦截", "sql": sql}

        try:
            columns, rows = run_query(sql)
        except Exception as e:
            if attempt == 0:
                error_hint = {"sql": sql, "detail": str(e)}
                continue
            return {"error": "SQL 执行失败", "sql": sql, "detail": str(e)}

        # 中文别名强制校验：模型偶尔无视规则输出英文列名（如 total_sales），
        # 这里在代码层兜底，把违规 SQL 喂回模型强制重新生成
        if attempt == 0 and _has_english_columns(columns):
            bad_cols = ", ".join(c for c in columns if c.isascii())
            error_hint = {
                "sql": sql,
                "detail": f"结果列名是英文（{bad_cols}），违反规则4。每一列都必须加中文别名，"
                          f"例如 SUM(amount) AS 销售额、COUNT(*) AS 订单数，请重新生成完整 SQL",
            }
            continue
        break

    return {
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "chart": result.get("chart", "table"),
        "explanation": result.get("explanation", ""),
    }
