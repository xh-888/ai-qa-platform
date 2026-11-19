# AI问数 · 企业级销售经管数据管理平台

基于**大模型的 Text2SQL（自然语言转 SQL）** 应用：用户以自然语言提问，平台自动完成
「理解问题 → 生成 SQL → 查询数据库 → 表格/图表可视化」全链路。

- **前端**：React 18 + Vite + ECharts
- **后端**：Python + FastAPI + SQLite
- **大模型**：任意 OpenAI 兼容 API（默认智谱 GLM-4-Flash，可配置替换）

---

## 一、快速开始

### 1. 后端

```bash
cd backend
pip install -r requirements.txt          # 依赖：fastapi uvicorn openai python-dotenv
# 配置大模型密钥：复制 .env.example 为 .env，填入 LLM_API_KEY
python data/seed.py                       # 生成示例数据库 sales.db（首次运行）
uvicorn main:app --reload --port 8000     # 启动 API
```

验证：访问 `http://127.0.0.1:8000/api/health` 返回 `{"status":"ok"}`。

### 2. 前端

```bash
cd frontend
npm install
npm run dev                               # 启动后访问 http://localhost:5173
```

开发期前端会把 `/api` 请求代理到后端 8000 端口（见 `vite.config.js`）。

### 3. 部署到 Linux

采用**单进程部署**：后端 `npm run build` 产物（`frontend/dist`）由 FastAPI 直接托管，
Linux 上仅需 Python 环境。详见 [`docs/Linux部署.md`](docs/Linux部署.md)，或直接运行：

```bash
bash deploy.sh          # 一键部署，完成后浏览器访问 http://localhost:8000
```

---

## 二、项目结构

```
ai-qa-platform/
├── backend/
│   ├── main.py            # FastAPI 入口：/api/health、/api/ask
│   ├── text2sql.py        # 核心：大模型生成 SQL + 安全校验 + 失败自动重试
│   ├── db.py              # SQLite 只读查询 + 自动读取表结构
│   ├── config.py          # 配置中心（.env），换厂商只改一处
│   ├── .env.example       # 配置模板
│   └── data/
│       ├── seed.py        # 示例数据生成脚本
│       └── sales.db       # SQLite 数据库（4 张表）
├── frontend/
│   ├── src/App.jsx        # 对话页组件 + 图表渲染
│   ├── src/index.css      # 样式
│   └── vite.config.js     # 含 /api 代理
└── docs/
    └── 功能分析与问题诊断.md
```

---

## 三、核心设计

### Text2SQL 数据流

```
用户提问 ──► 后端 /api/ask
              ├─ 1. 读取表结构（schema）作为「菜单」喂给大模型
              ├─ 2. 大模型生成 { sql, chart, explanation }
              ├─ 3. 安全校验（仅放行 SELECT/WITH，拦截写操作与注入）
              ├─ 4. 执行 SQL（SQLite 只读连接）
              └─ 5. 失败时把报错喂回模型自我修正（最多重试 1 次）
            ──► 返回 { sql, columns, rows, chart, explanation } ──► 前端渲染
```

### 数据库表设计（4 张表）

| 表 | 说明 | 关键字段 |
|---|---|---|
| `customers` | 客户 | customer_id, name, region, industry |
| `products` | 产品 | product_id, name, category, price |
| `orders` | 订单 | order_id, customer_id, product_id, order_date, region, quantity, amount, status |
| `sales_goals` | 销售目标 | goal_id, region, year_month, target_amount |

`orders.region` 为冗余字段：既能回答简单单表查询，也能覆盖跨表 JOIN 场景。

### 安全设计

- 仅放行 `SELECT` / `WITH` 查询，拦截 `INSERT/UPDATE/DELETE/DROP` 等写操作及注入关键字。
- 使用 SQLite **只读连接**（`file:...?mode=ro`），从数据库层兜底。
- 大模型输出视为不可信输入，一律先校验再执行。

### 大模型可替换

后端采用 OpenAI 兼容协议，`.env` 中改 `LLM_BASE_URL` / `LLM_MODEL` 即可切换
DeepSeek / 通义千问 / 智谱 等任意厂商，代码零改动。
