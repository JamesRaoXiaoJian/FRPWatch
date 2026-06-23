# FRP 设备在线状态监控

## 功能
直接探测 frps 暴露的端口，判断设备 4090 是否在线，状态变化时通过 Gmail 发送邮件提醒。

## 原理
frpc 客户端连接 frps 后，frps 会开放一个端口（即 frpc 配置中的 `remote_port`）。本脚本直接尝试 TCP 连接该端口：
- **连接成功** → 设备在线
- **连接失败** → 设备离线

比查 Dashboard API 更直接、更可靠。

## 使用步骤

### 1. 填写配置
编辑 `monitor.py`，找到 `CONFIG` 字典，填写以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `FRPS_PORT` | 4090 设备在 frps 上暴露的端口（即 frpc 的 `remote_port`） | `6000` |
| `GMAIL_USER` | Gmail 发件邮箱 | `yourname@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail 应用专用密码（16位） | `abcd efgh ijkl mnop` |
| `ALERT_TO` | 收件人邮箱 | `yourname@gmail.com` |

> `FRPS_HOST` 默认为 `203.195.160.134`，如需修改请一并调整。

### 2. 获取 Gmail 应用专用密码
1. 登录 https://myaccount.google.com/
2. 左侧菜单 → **安全性**
3. 确保已开启 **两步验证**
4. 访问 https://myaccount.google.com/apppasswords
5. 创建一个应用专用密码（名称随意，如 `frp_monitor`）
6. 复制生成的 16 位密码，填入 `GMAIL_APP_PASSWORD`

> ⚠️ **必须使用应用专用密码，不能使用 Gmail 登录密码。**

### 3. 测试运行
```bash
cd /home/james/Project/FRP_state
uv run monitor.py
```
看到 `FRP 设备监控启动` 说明正常。按 `Ctrl+C` 停止。

### 4. 设为后台服务（开机自启）
```bash
mkdir -p ~/.config/systemd/user
cp /home/james/Project/FRP_state/frp_monitor.service ~/.config/systemd/user/
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
- `frp_monitor.service` — systemd 服务文件
- `state.json` — 运行时状态记录（自动生成）
- `monitor.log` — 运行日志（自动生成）
# FRPWatch
