import requests
import socket
import random
import json
import os
import sys
import time
import datetime
import urllib3

# 禁用安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_config():
    """读取配置文件"""
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print(f"[!] 错误: 找不到 {config_path} 文件。")
        print("请在同级目录下创建 config.json 并填入账号密码。")
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] 读取配置文件失败: {e}")
        sys.exit(1)


def get_local_ip():
    """获取本机 IP (每次循环都需要重新获取，防止IP变动)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def do_login_request(account, password):
    """执行单次登录逻辑"""
    url = "https://p.njupt.edu.cn:802/eportal/portal/login"
    current_ip = get_local_ip()
    random_v = str(random.randint(1000, 9999))

    # 获取当前时间用于日志打印
    now_time = datetime.datetime.now().strftime("%H:%M:%S")

    params = {
        'callback': 'dr1003',
        'login_method': '1',
        'user_account': account,
        'user_password': password,
        'wlan_user_ip': current_ip,
        'wlan_user_ipv6': '',
        'wlan_user_mac': '000000000000',
        'wlan_ac_ip': '',
        'wlan_ac_name': '',
        'jsVersion': '4.1.3',
        'terminal_type': '1',
        'lang': 'zh-cn',
        'v': random_v
    }

    headers = {
        'Host': 'p.njupt.edu.cn:802',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Referer': 'https://p.njupt.edu.cn/',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }

    try:
        # 这里的 timeout=5 是为了防止网络卡住导致程序死等
        response = requests.get(url, params=params, headers=headers, verify=False, timeout=5)

        if response.status_code == 200:
            if '"result":"1"' in response.text or 'success' in response.text:
                print(f"[{now_time}] [+] 登录成功 (IP: {current_ip})")
            elif "已登录" in response.text:
                print(f"[{now_time}] [=] 保持在线中... (IP: {current_ip})")
            else:
                print(f"[{now_time}] [?] 状态未知: {response.text[:50]}...")
        else:
            print(f"[{now_time}] [!] 状态码错误: {response.status_code}")

    except requests.exceptions.RequestException as e:
        # 捕获所有网络相关错误，不退出程序，只打印错误
        print(f"[{now_time}] [!] 网络请求异常 (可能未连接WiFi): {e}")


def main():
    print("--- 校园网自动登录脚本启动 ---")
    print("--- 按 Ctrl+C 停止脚本 ---")

    # 读取配置
    config = load_config()
    account = config.get('account')
    password = config.get('password')
    # 默认间隔 10 秒，如果配置文件没写
    interval = config.get('interval', 10)

    if not account or not password:
        print("[!] config.json 配置不完整")
        return

    # 循环主体
    while True:
        try:
            do_login_request(account, password)

            # 倒计时等待
            time.sleep(interval)

        except KeyboardInterrupt:
            print("\n[!] 用户手动停止程序。再见！")
            break
        except Exception as e:
            print(f"[!] 发生意外错误: {e}")
            time.sleep(5)  # 出错后稍微等一下再试


if __name__ == "__main__":
    main()