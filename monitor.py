#!/usr/bin/env python3
"""
FRP 设备在线状态监控脚本
通过 FRP Dashboard API 查询设备在线状态，状态变化时发送 Gmail 邮件提醒。
"""

import json
import logging
import os
import smtplib
import sys
import time
from datetime import datetime
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

# 加载 .env 文件
load_dotenv()

# ============================================================
#  用户配置区 - 从环境变量读取
# ============================================================

CONFIG = {
    # FRP Dashboard 配置
    "FRP_HOST": os.getenv("FRP_HOST", "localhost"),
    "FRP_PORT": int(os.getenv("FRP_PORT", "7500")),
    "FRP_USER": os.getenv("FRP_USER", ""),
    "FRP_PASS": os.getenv("FRP_PASS", ""),
    "FRP_DEVICE_NAME": os.getenv("FRP_DEVICE_NAME", "my_device"),

    # Gmail 配置
    "GMAIL_USER": os.getenv("GMAIL_USER", ""),
    "GMAIL_APP_PASSWORD": os.getenv("GMAIL_APP_PASSWORD", ""),
    "ALERT_TO": os.getenv("ALERT_TO", ""),

    # 监控参数
    "POLL_INTERVAL": int(os.getenv("POLL_INTERVAL", "30")),
    "STATE_FILE": os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json"),
}

# ============================================================
#  日志配置
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor.log"),
            encoding="utf-8",
        ),
    ],
)
log = logging.getLogger("frp_monitor")

# ============================================================
#  FRP API 探测
# ============================================================

PROXY_TYPES = ["tcp", "udp", "http", "https", "stcp", "xtcp", "sudp"]


def frp_base_url() -> str:
    return f"http://{CONFIG['FRP_HOST']}:{CONFIG['FRP_PORT']}"


def frp_auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(CONFIG["FRP_USER"], CONFIG["FRP_PASS"])


def probe_device() -> list[dict]:
    """
    遍历所有 proxy type，查找名为 CONFIG['FRP_DEVICE_NAME'] 开头的所有 proxy。
    返回匹配的 proxy 列表。
    """
    target = CONFIG["FRP_DEVICE_NAME"]
    found = []
    for ptype in PROXY_TYPES:
        url = f"{frp_base_url()}/api/proxy/{ptype}"
        try:
            resp = requests.get(url, auth=frp_auth(), timeout=10)
            if resp.status_code != 200:
                continue
            data = resp.json()
            proxies = data.get("proxies") if isinstance(data, dict) else data
            if not isinstance(proxies, list):
                continue
            for p in proxies:
                name = p.get("name", "")
                if name == target or name.startswith(target + "."):
                    found.append({
                        "name": name,
                        "type": ptype,
                        "status": p.get("status", "unknown"),
                        "todayTrafficIn": p.get("todayTrafficIn", 0),
                        "todayTrafficOut": p.get("todayTrafficOut", 0),
                        "curConns": p.get("curConns", 0),
                        "lastStartTime": p.get("lastStartTime", ""),
                        "lastCloseTime": p.get("lastCloseTime", ""),
                    })
        except Exception as e:
            log.warning(f"请求 {ptype} 失败: {e}")
    return found


# ============================================================
#  状态持久化
# ============================================================


def load_state() -> dict:
    path = CONFIG["STATE_FILE"]
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_state(state: dict):
    with open(CONFIG["STATE_FILE"], "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ============================================================
#  邮件发送
# ============================================================


def send_alert(subject: str, body: str):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = CONFIG["GMAIL_USER"]
    msg["To"] = CONFIG["ALERT_TO"]

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(CONFIG["GMAIL_USER"], CONFIG["GMAIL_APP_PASSWORD"])
            server.sendmail(CONFIG["GMAIL_USER"], CONFIG["ALERT_TO"], msg.as_string())
        log.info(f"邮件已发送: {subject}")
    except Exception as e:
        log.error(f"邮件发送失败: {e}")


def _format_proxies(proxies: list[dict]) -> str:
    lines = []
    for p in proxies:
        lines.append(f"  - {p['name']} ({p['type']}) → {p['status']}")
    return "\n".join(lines)


def notify_online(proxies: list[dict]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_alert(
        f"[FRP] ✅ 设备 {CONFIG['FRP_DEVICE_NAME']} 已上线",
        f"设备已上线\n\n"
        f"{_format_proxies(proxies)}\n\n"
        f"  检测时间: {now}\n",
    )


def notify_offline(proxies: list[dict]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_alert(
        f"[FRP] ❌ 设备 {CONFIG['FRP_DEVICE_NAME']} 已离线",
        f"设备已离线\n\n"
        f"{_format_proxies(proxies)}\n\n"
        f"  检测时间: {now}\n",
    )


def notify_not_found():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_alert(
        f"[FRP] ⚠️ 设备 {CONFIG['FRP_DEVICE_NAME']} 未在 Dashboard 中找到",
        f"在 FRP Dashboard 所有 proxy 类型中均未找到名为 "
        f"'{CONFIG['FRP_DEVICE_NAME']}' 的设备。\n\n"
        f"  Dashboard: {frp_base_url()}\n"
        f"  检测时间:  {now}\n",
    )


# ============================================================
#  主循环
# ============================================================


def validate_config():
    required = ["FRP_USER", "FRP_PASS", "GMAIL_USER", "GMAIL_APP_PASSWORD", "ALERT_TO"]
    missing = [k for k in required if not CONFIG.get(k)]
    if missing:
        log.error(f"以下配置项未填写: {', '.join(missing)}")
        raise SystemExit(1)


def main():
    validate_config()
    log.info(
        f"FRP 设备监控启动 — 目标: {CONFIG['FRP_DEVICE_NAME']} @ {frp_base_url()}"
    )

    state = load_state()
    last_status = state.get("status")
    notified_not_found = False

    while True:
        try:
            proxies = probe_device()

            if not proxies:
                current = "not_found"
            elif any(p["status"].lower() in ("online", "running") for p in proxies):
                current = "online"
            else:
                current = "offline"

            detail = ", ".join(f"{p['name']}={p['status']}" for p in proxies) if proxies else "无"
            log.info(f"设备 '{CONFIG['FRP_DEVICE_NAME']}' — 状态: {current} ({detail})")

            if last_status is None:
                log.info("首次运行，记录初始状态。")
            elif current != last_status:
                log.info(f"状态变化: {last_status} → {current}")
                if current == "online":
                    notify_online(proxies)
                elif current == "offline":
                    notify_offline(proxies)
                elif current == "not_found" and not notified_not_found:
                    notify_not_found()
                    notified_not_found = True

            last_status = current
            save_state({
                "status": current,
                "proxies": proxies,
                "last_check": datetime.now().isoformat(),
            })

        except Exception as e:
            log.error(f"监控循环异常: {e}", exc_info=True)

        time.sleep(CONFIG["POLL_INTERVAL"])


if __name__ == "__main__":
    main()
