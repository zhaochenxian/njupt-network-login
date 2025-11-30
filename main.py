import requests
import socket
import random
import json
import os
import sys
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
    """获取本机 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def login():
    # 1. 读取配置
    config = load_config()
    account = config.get('account')
    password = config.get('password')

    if not account or not password:
        print("[!] 错误: config.json 中缺少 account 或 password 字段")
        return

    # 2. 准备动态参数
    url = "https://p.njupt.edu.cn:802/eportal/portal/login"
    current_ip = get_local_ip()
    random_v = str(random.randint(1000, 9999))

    print(f"[-] 当前 IP: {current_ip}")
    print(f"[-] 读取账号: {account}")

    # 3. 构造参数
    # requests 会自动处理 URL 编码，所以这里直接传原始字符串即可
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

    # 4. 发送请求
    try:
        print("[-] 正在登录...")
        response = requests.get(url, params=params, headers=headers, verify=False)

        if response.status_code == 200:
            # 简单判断结果
            if '"result":"1"' in response.text or 'success' in response.text:
                print("[+] 登录成功！")
            elif "已登录" in response.text:
                print("[+] 已经是登录状态。")
            else:
                print(f"[?] 服务器返回: {response.text[:100]}...")  # 只打印前100字符
        else:
            print(f"[!] 请求失败: {response.status_code}")

    except Exception as e:
        print(f"[!] 发生网络错误: {e}")


if __name__ == "__main__":
    login()