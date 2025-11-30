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
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] 读取配置文件失败: {e}")
        sys.exit(1)


def get_local_ip():
    """获取本机 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def do_login_request(account, password):
    """
    执行登录逻辑
    返回: True (表示任务完成，可以退出); False (表示需要重试)
    """
    url = "https://p.njupt.edu.cn:802/eportal/portal/login"
    current_ip = get_local_ip()
    random_v = str(random.randint(1000, 9999))
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
        response = requests.get(url, params=params, headers=headers, verify=False, timeout=5)
        text = response.text

        if response.status_code == 200:
            # --- 关键修改：根据你提供的日志修正判断逻辑 ---

            # 情况1: 登录成功
            # 服务器返回: {"result":1,"msg":"Portal协议认证成功！"} (注意1没有引号)
            if '"result":1' in text or 'Portal协议认证成功' in text:
                print(f"[{now_time}] [+] 登录成功！(IP: {current_ip})")
                return True  # 返回 True 表示应该退出了

            # 情况2: 已经登录过了
            # 服务器返回: {"result":0,"msg":"AC999","ret_code":2}
            elif 'AC999' in text or '"ret_code":2' in text:
                print(f"[{now_time}] [=] 检测到设备已在线，无需重复登录。")
                return True  # 返回 True 表示应该退出了

            # 情况3: 其他错误 (如密码错误，账号欠费等)
            else:
                print(f"[{now_time}] [?] 登录未成功，响应: {text[:80]}...")
                return False  # 继续重试
        else:
            print(f"[{now_time}] [!] HTTP 状态码错误: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[{now_time}] [!] 网络异常 (可能未连接WiFi): {e}")
        return False


def main():
    print("--- 校园网自动登录脚本启动 ---")

    config = load_config()
    account = config.get('account')
    password = config.get('password')
    interval = config.get('interval', 5)  # 默认重试间隔5秒

    if not account or not password:
        print("[!] config.json 配置不完整")
        return

    while True:
        try:
            # 执行登录请求
            is_success = do_login_request(account, password)

            # 如果成功（或已在线），直接退出程序
            if is_success:
                print("--- 程序即将退出 ---")
                time.sleep(2)  # 稍微停顿一下让用户看清提示
                break

            # 如果失败，等待后重试
            time.sleep(interval)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[!] 发生意外错误: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()