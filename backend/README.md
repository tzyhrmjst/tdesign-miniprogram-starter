# 黄金价格提醒后端

轻量 FastAPI 服务，第一版提供：

- `GET /api/gold/latest`
- `GET /api/gold/history`
- `POST /api/auth/wx-login`
- `GET /api/alerts`
- `POST /api/alerts`
- `PUT /api/alerts/{id}`
- `PATCH /api/alerts/{id}/status`
- `DELETE /api/alerts/{id}`
- `GET /api/alert-history`

本地启动：

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

小程序联调时把根目录 `config.js` 中的 `isMock` 改为 `false`，`baseUrl` 改为后端 HTTPS 地址。

微信登录换取 `openid` 需要配置环境变量：

```bash
cp .env.example .env
```

然后编辑 `backend/.env`：

```bash
WECHAT_APPID="你的小程序 AppID"
WECHAT_SECRET="你的小程序 AppSecret"
WECHAT_SUBSCRIBE_TEMPLATE_ID="你的订阅消息模板 ID"
WECHAT_MINIPROGRAM_STATE="trial"
```

未配置或配置错误时，小程序前端会自动使用本地 demo 用户，方便继续开发联调。

订阅消息模板当前使用“产品价格变动提醒”，字段映射为：

- `amount4`：当前价格
- `time5`：提醒触发时间
- `time11`：价格变动时间
- `thing15`：产品名称
- `thing6`：备注
