"""
校园网一次性登录脚本

用法：
  python src/main.py           # 自动重试直到登录成功
  python src/main.py --once    # 只尝试一次，不重试
"""

import requests
import socket
import random
import json
import os
import sys
import time
import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_config() -> dict:
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config", "config.json"
    )
    if not os.path.exists(config_path):
        print("[!] 错误: 找不到配置文件 config/config.json")
        sys.exit(1)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] 读取配置文件失败: {e}")
        sys.exit(1)


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def do_login_request(account: str, password: str) -> bool:
    """
    执行一次登录请求。
    返回 True  = 成功（已登录 或 已在线）
    返回 False = 失败，需要重试
    """
    url = "https://p.njupt.edu.cn:802/eportal/portal/login"
    current_ip = get_local_ip()
    now_time = datetime.datetime.now().strftime("%H:%M:%S")

    params = {
        "callback": "dr1003",
        "login_method": "1",
        "user_account": account,
        "user_password": password,
        "wlan_user_ip": current_ip,
        "wlan_user_ipv6": "",
        "wlan_user_mac": "000000000000",
        "wlan_ac_ip": "",
        "wlan_ac_name": "",
        "jsVersion": "4.1.3",
        "terminal_type": "1",
        "lang": "zh-cn",
        "v": str(random.randint(1000, 9999)),
    }
    headers = {
        "Host": "p.njupt.edu.cn:802",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        ),
        "Referer": "https://p.njupt.edu.cn/",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, verify=False, timeout=8)
        text = resp.text

        if resp.status_code == 200:
            if '"result":1' in text or "Portal协议认证成功" in text:
                print(f"[{now_time}] [+] 登录成功！(IP: {current_ip})")
                return True
            elif "AC999" in text or '"ret_code":2' in text:
                print(f"[{now_time}] [=] 设备已在线，无需重复登录。")
                return True
            else:
                print(f"[{now_time}] [?] 登录未成功，响应: {text[:100]}")
                return False
        else:
            print(f"[{now_time}] [!] HTTP 状态码异常: {resp.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[{now_time}] [!] 网络异常: {e}")
        return False


def main():
    print("--- 校园网登录脚本启动 ---")

    only_once = "--once" in sys.argv

    cfg = load_config()
    account = cfg.get("account")
    password = cfg.get("password")
    interval = int(cfg.get("interval", 5))

    if not account or not password:
        print("[!] config.json 中 account 或 password 未填写")
        return

    if only_once:
        do_login_request(account, password)
        return

    while True:
        try:
            if do_login_request(account, password):
                print("--- 登录完成，程序退出 ---")
                break
            time.sleep(interval)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[!] 意外错误: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
