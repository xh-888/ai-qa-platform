# Linux 部署说明（WSL / 云服务器通用）

本项目采用「**单进程部署**」方案：FastAPI 同时托管前端静态页面（`frontend/dist`）与 `/api` 接口，
因此 **Linux 上只需要 Python 环境**，不需要 Node.js，也无需单独配置 Nginx 或 CORS。

## 一、前置条件

- 一台 Linux 环境（WSL Ubuntu 或云服务器），能访问外网（下载依赖）。
- 已在前端构建产物：`frontend/dist/`（本项目已构建好，如改动前端需重新 `npm run build`）。
- 后端 `backend/.env` 中已配置 `LLM_API_KEY`（本项目已配置）。

## 二、WSL 部署步骤（本机）

1. 双击桌面 `Ubuntu.lnk`（或开始菜单搜 "Ubuntu"）打开 WSL 终端。

2. 进入项目目录（WSL 通过 `/mnt/c/...` 访问 Windows 磁盘）：

   ```bash
   cd /mnt/c/Users/hw/WorkBuddy/2026-11-12-10-23-39/ai-qa-platform
   ```

3. 运行一键部署脚本：

   ```bash
   bash deploy.sh
   ```

   首次运行会提示输入 `sudo` 密码（你的 WSL 用户名密码），用于安装 Python 依赖。

4. 看到 `✅ 部署完成` 后，在 **Windows 浏览器**打开：

   ```
   http://localhost:8000
   ```

   WSL2 会自动把 localhost 转发到 Linux，所以浏览器直接访问即可。

## 三、云服务器部署步骤（可选，更接近真实生产）

1. 把 `ai-qa-platform/` 整个目录上传到服务器（`scp` 或 `git clone`）。
2. 服务器上执行与上述相同的 `bash deploy.sh`。
3. 在云控制台「安全组」放行 8000 端口。
4. 用 `http://<服务器公网IP>:8000` 访问。
5. （进阶）用 `systemd` 或 `nohup` 让服务常驻后台。

## 四、手动部署（不用脚本，便于理解每一步）

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python data/seed.py
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 五、常见问题

| 问题 | 解决 |
|---|---|
| `sudo: command not found` 或无权限 | 确认当前是 WSL 默认用户，`whoami` 查看 |
| 依赖下载超时 | 脚本已优先用清华镜像；仍失败则重跑一次 |
| 端口 8000 被占用 | `lsof -i:8000` 找进程，或换端口 `--port 8001` |
| 浏览器打不开 | 确认 uvicorn 已显示启动日志、未报错 |
| 改动前端后页面没更新 | 在 Windows 侧重新 `npm run build` 后重启 uvicorn |
