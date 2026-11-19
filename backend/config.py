# -*- coding: utf-8 -*-
"""全局配置：从 backend/.env 读取，支持任意 OpenAI 兼容大模型"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent  # backend 目录
load_dotenv(BASE_DIR / ".env")

# 大模型配置
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "glm-4-flash").strip()

# 数据库路径：.env 中可写相对路径（相对 backend 目录），统一转为绝对路径，
# 避免因启动目录不同导致 "unable to open database file"
_db_path = os.getenv("DB_PATH", "data/sales.db")
DB_PATH = str(Path(_db_path)) if Path(_db_path).is_absolute() else str(BASE_DIR / _db_path)
