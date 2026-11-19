# -*- coding: utf-8 -*-
"""AI问数 后端入口（FastAPI）

启动：cd backend && uvicorn main:app --reload --port 8000
生产部署：前端 build 产物（frontend/dist）会被本服务直接托管，
          单进程同时提供 API 与前端页面，浏览器访问 8000 端口即可。
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from text2sql import ask

app = FastAPI(title="AI问数 API", version="0.2.0")

# 后端代码版本标识：用于部署后确认服务加载的是哪一版代码
BACKEND_BUILD = "20261119.2"  # 0.2 = 英文列名兜底校验生效版本


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=200)


@app.get("/api/health")
def health():
    return {"status": "ok", "build": BACKEND_BUILD}


@app.post("/api/ask")
def api_ask(req: AskRequest):
    result = ask(req.question)
    if "error" in result:
        # 未配置 Key 属服务端配置问题（503）；其余为请求无法被满足（400）
        status = 503 if "未配置" in result.get("error", "") else 400
        return JSONResponse(status_code=status, content=result)
    return result


# 托管前端构建产物（若已 build），实现单进程部署。
# 注意：必须放在所有 /api 路由定义之后，作为兜底静态服务。
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
