#!/usr/bin/env bash
# ============================================================
# AI问数 · Linux/WSL 一键部署脚本
# 用法：在 Linux 终端（WSL Ubuntu）中运行：  bash deploy.sh
# 完成后浏览器访问 http://localhost:8000
# ============================================================
set -e
cd "$(dirname "$0")"

echo "==> [1/4] 检查并安装 Python 环境"
if ! command -v python3 >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y python3
fi
if ! python3 -c "import venv" >/dev/null 2>&1; then
    sudo apt-get install -y python3-venv
fi
if ! command -v pip3 >/dev/null 2>&1 && ! python3 -m pip --version >/dev/null 2>&1; then
    sudo apt-get install -y python3-pip
fi

echo "==> [2/4] 创建虚拟环境并安装后端依赖"
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    || pip install -q -r requirements.txt

echo "==> [3/4] 生成示例数据库"
python data/seed.py

# 清理旧的 Python 字节码缓存，确保加载的是最新源码
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

if [ ! -d "../frontend/dist" ]; then
    echo ""
    echo "  ⚠️  未检测到前端构建产物 frontend/dist"
    echo "     请在 Windows 下执行： cd frontend && npm run build"
    echo "     （或将仓库里已构建的 dist 目录一并部署）"
    echo "     否则 8000 端口将只有 API、没有网页页面。"
    echo ""
fi

echo "==> [4/4] 启动服务（前端 + 后端 单进程）"
echo ""
echo "  ✅ 部署完成！请在 Windows 浏览器打开： http://localhost:8000"
echo "  （按 Ctrl+C 可停止服务）"
echo ""
uvicorn main:app --host 0.0.0.0 --port 8000
