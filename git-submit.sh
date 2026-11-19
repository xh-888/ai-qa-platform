#!/usr/bin/env bash
# ============================================================
# AI问数 · Git 一键提交脚本
# 用法（在 WSL Ubuntu 终端运行）：
#   1. 先在 GitHub/Gitee 网页上创建一个【空仓库】（不要勾选初始化 README）
#   2. 复制仓库地址，然后运行：
#      bash git-submit.sh https://github.com/你的用户名/仓库名.git
# ============================================================
set -e
cd "$(dirname "$0")"

REPO_URL="$1"
if [ -z "$REPO_URL" ]; then
    echo "❌ 用法：bash git-submit.sh <仓库地址>"
    echo "   例如：bash git-submit.sh https://gitee.com/xuhao/ai-qa-platform.git"
    exit 1
fi

echo "==> [1/5] 检查 git"
if ! command -v git >/dev/null 2>&1; then
    sudo apt-get update -y && sudo apt-get install -y git
fi

echo "==> [2/5] 初始化仓库"
git init -b main

# 配置提交者身份（只需第一次；已有全局配置会被本地覆盖）
read -p "请输入你的 GitHub/Gitee 用户名: " GIT_NAME
read -p "请输入你的邮箱: " GIT_EMAIL
git config user.name  "$GIT_NAME"
git config user.email "$GIT_EMAIL"

echo "==> [3/5] 添加文件并提交"
git add .
echo "---- 将提交以下文件 ----"
git status --short | head -30
echo "------------------------"
read -p "确认无误后按回车继续提交（Ctrl+C 取消）..."
git commit -m "AI问数：企业级销售经管数据问答平台（Text2SQL demo）

- 前端：React + Vite + ECharts，复刻原型对话页交互
- 后端：FastAPI + SQLite，Text2SQL 核心链路（LLM 生成 SQL + 安全校验 + 失败自修正重试 + 中文别名兜底）
- 数据：销售主题 4 表示例数据（seed.py 动态生成到当日）
- 文档：功能分析与问题诊断、Linux 部署说明
- 测试：pytest 17 项单元测试
- 部署：deploy.sh 一键部署，单进程托管前端与 API"

echo "==> [4/5] 关联远程仓库"
git remote add origin "$REPO_URL"

echo "==> [5/5] 推送到远程（可能要求输入账号密码/令牌）"
git push -u origin main

echo ""
echo "✅ 完成！打开你的仓库网页确认代码已上传，然后把链接回复到招聘方邮箱。"
