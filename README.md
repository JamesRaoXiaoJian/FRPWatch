# FRP 设备在线状态监控

## 功能
通过 FRP Dashboard API 查询设备在线状态，状态变化时发送 Gmail 邮件提醒。

## 使用步骤

### 1. 安装依赖
```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 2. 配置环境变量
复制示例配置文件并填入你的信息：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `FRP_HOST` | FRP Dashboard 地址 | `your_server_ip` |
| `FRP_PORT` | FRP Dashboard 端口 | `7500` |
| `FRP_USER` | FRP Dashboard 用户名 | `admin` |
| `FRP_PASS` | FRP Dashboard 密码 | `your_password` |
| `FRP_DEVICE_NAME` | 要监控的设备名称 | `4090` |
| `GMAIL_USER` | Gmail 发件邮箱 | `yourname@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail 应用专用密码（16位） | `abcd efgh ijkl mnop` |
| `ALERT_TO` | 收件人邮箱 | `yourname@gmail.com` |
| `POLL_INTERVAL` | 轮询间隔（秒） | `30` |

### 3. 获取 Gmail 应用专用密码
1. 登录 https://myaccount.google.com/
2. 左侧菜单 → **安全性**
3. 确保已开启 **两步验证**
4. 访问 https://myaccount.google.com/apppasswords
5. 创建一个应用专用密码（名称随意，如 `frp_monitor`）
6. 复制生成的 16 位密码，填入 `.env` 文件的 `GMAIL_APP_PASSWORD`

> ⚠️ **必须使用应用专用密码，不能使用 Gmail 登录密码。**

### 4. 测试运行
```bash
# 使用 uv
uv run monitor.py

# 或使用 python
python monitor.py
```
看到 `FRP 设备监控启动` 说明正常。按 `Ctrl+C` 停止。

### 5. 设为后台服务（开机自启）
```bash
mkdir -p ~/.config/systemd/user
cp frp_monitor.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable frp_monitor.service
systemctl --user start frp_monitor.service

# 查看状态
systemctl --user status frp_monitor.service

# 查看日志
journalctl --user -u frp_monitor.service -f
```

> 💡 SSH 断开后服务仍运行：`loginctl enable-linger james`

## 文件说明
- `monitor.py` — 主监控脚本
- `.env.example` — 环境变量示例文件
- `.env` — 实际配置文件（不提交到仓库）
- `frp_monitor.service` — systemd 服务文件
- `state.json` — 运行时状态记录（自动生成，不提交到仓库）
- `monitor.log` — 运行日志（自动生成，不提交到仓库）
# FRPWatch
