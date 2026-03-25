"""
校园网自动化监控脚本
- 监控校园网连接状态
- 校园网断开时自动禁用有线网
- 每天早上自动启用有线网并连接
- 支持后台持续运行
"""

import os
import sys
import time
import datetime
import subprocess
import re
import requests
import urllib3

# 禁用安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置
ADAPTER_NAME = "linenet"  # 默认网络适配器名称（会被配置/自动探测覆盖）
LOG_FILE = "network_monitor.log"
CHECK_INTERVAL = 60  # 检查间隔（秒）
CAMPUS_NETWORK_URL = "https://p.njupt.edu.cn:802/"  # 校园网地址
MORNING_HOUR = 7  # 每天早上7点自动启用
LOGIN_RETRY_INTERVAL = 300  # 登录重试间隔（秒）

CONNECTIVITY_CHECK_URLS = [
    "https://www.baidu.com",
    "https://www.qq.com",
    "http://www.msftconnecttest.com/connecttest.txt"
]


def load_monitor_config():
    """读取监控配置（可选）"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
    if not os.path.exists(config_path):
        return {}

    try:
        import json
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_message(f"[!] 读取监控配置失败，将使用默认配置: {e}")
        return {}


def get_adapter_list():
    """获取系统网络适配器列表"""
    try:
        result = subprocess.run(
            ["netsh", "interface", "show", "interface"],
            capture_output=True,
            text=True,
            timeout=5,
            encoding="utf-8",
            errors="ignore"
        )
        if result.returncode != 0:
            return []

        adapters = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("---") or "Admin State" in line:
                continue
            parts = re.split(r"\s{2,}", line)
            if len(parts) >= 4:
                adapters.append({
                    "admin_state": parts[0],
                    "state": parts[1],
                    "type": parts[2],
                    "name": parts[3]
                })
        return adapters
    except Exception:
        return []


def resolve_adapter_name(preferred_name):
    """解析最终要使用的网络适配器名称（配置优先，自动探测兜底）"""
    adapters = get_adapter_list()
    if not adapters:
        return preferred_name

    names = [adapter["name"] for adapter in adapters]
    if preferred_name in names:
        return preferred_name

    candidate_names = ["linenet", "Ethernet", "以太网", "本地连接"]
    for candidate in candidate_names:
        if candidate in names:
            log_message(f"[*] 未找到配置网卡 '{preferred_name}'，自动使用 '{candidate}'")
            return candidate

    for adapter in adapters:
        if adapter["type"].lower() == "dedicated":
            log_message(f"[*] 未找到常见网卡名，自动使用首个有线网卡 '{adapter['name']}'")
            return adapter["name"]

    log_message(f"[*] 未探测到可用有线网卡，继续使用配置值 '{preferred_name}'")
    return preferred_name


def log_message(message):
    """输出日志"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = f"[{timestamp}] {message}"
    print(log_text)
    
    # 同时写入日志文件
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_text + '\n')
    except:
        pass


def run_command_as_admin(command):
    """以管理员身份运行命令"""
    try:
        # 使用 PowerShell 的 Start-Process -Verb RunAs
        ps_command = f'Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command {command}" -Verb RunAs -WindowStyle Hidden -Wait'
        subprocess.run(['powershell', '-Command', ps_command], check=True, capture_output=True)
        return True
    except Exception as e:
        log_message(f"[!] 命令执行失败: {e}")
        return False


def set_adapter_state(state: str):
    """
    启用或禁用网络适配器
    state: "enable" 或 "disable"
    """
    if state.lower() == "enable":
        command = f'netsh interface set interface name="{ADAPTER_NAME}" admin=enable'
        log_message(f"正在尝试启用网络适配器 '{ADAPTER_NAME}'...")
    else:
        command = f'netsh interface set interface name="{ADAPTER_NAME}" admin=disable'
        log_message(f"正在尝试禁用网络适配器 '{ADAPTER_NAME}'...")
    
    # 使用 cmd /c 执行
    try:
        result = subprocess.run(['cmd', '/c', command], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            log_message(f"[+] 网络适配器操作成功")
            return True
        else:
            log_message(f"[!] 网络适配器操作可能失败: {result.stderr}")
            return False
    except Exception as e:
        log_message(f"[!] 执行网络适配器命令时出错: {e}")
        return False


def can_reach_internet():
    """检查是否可访问外网（用于判断是否已认证出网）"""
    for url in CONNECTIVITY_CHECK_URLS:
        try:
            response = requests.get(url, timeout=3, verify=False, allow_redirects=True)
            if response.status_code in (200, 204):
                return True
        except Exception:
            continue
    return False


def check_network_state():
    """
    检查网络状态：
    - authenticated: 已认证，可访问外网
    - captive: 可访问校园网登录页，但外网不可达（需要登录）
    - offline: 校园网与外网都不可达
    """
    portal_reachable = False

    try:
        requests.get(
            CAMPUS_NETWORK_URL,
            timeout=3,
            verify=False,
            allow_redirects=True
        )
        portal_reachable = True
    except requests.exceptions.Timeout:
        portal_reachable = False
    except requests.exceptions.ConnectionError:
        portal_reachable = False
    except Exception as e:
        log_message(f"[?] 校园网检测出错: {e}")
        portal_reachable = False

    internet_reachable = can_reach_internet()

    if internet_reachable:
        return "authenticated"
    if portal_reachable:
        return "captive"
    return "offline"


def run_login_script():
    """运行登录脚本"""
    try:
        log_message("正在运行登录脚本...")
        script_path = os.path.join(os.path.dirname(__file__), 'main.py')
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            log_message("[+] 登录脚本执行成功")
            return True
        else:
            log_message(f"[!] 登录脚本执行失败: {result.stderr}")
            return False
    except Exception as e:
        log_message(f"[!] 运行登录脚本时出错: {e}")
        return False


def should_enable_morning(current_time, last_morning_check):
    """检查是否应执行当天早间自动启用（超过阈值后当天补执行一次）"""
    if last_morning_check == current_time.date():
        return False
    return current_time.hour >= MORNING_HOUR


def main_monitor_loop():
    """主监控循环"""
    log_message("=" * 50)
    log_message("校园网自动化监控脚本已启动")
    log_message(f"网络适配器: {ADAPTER_NAME}")
    log_message(f"检查间隔: {CHECK_INTERVAL} 秒")
    log_message(f"早上启用时间: {MORNING_HOUR}:00")
    log_message("=" * 50)
    
    last_morning_check = None
    last_adapter_state = None
    last_network_state = None
    last_login_attempt = None
    
    while True:
        try:
            current_time = datetime.datetime.now()
            network_state = check_network_state()

            if network_state != last_network_state:
                if network_state == "authenticated":
                    log_message("[+] 网络已认证，可访问外网")
                elif network_state == "captive":
                    log_message("[!] 检测到校园网登录页可达，但外网不可达（需要登录）")
                else:
                    log_message("[-] 校园网与外网均不可达（离线）")
                last_network_state = network_state
            
            # 逻辑1: 如果校园网断开，禁用有线网适配器
            if network_state == "offline":
                if last_adapter_state != "disabled":
                    log_message("[*] 校园网已断开，正在禁用有线网适配器...")
                    set_adapter_state("disable")
                    last_adapter_state = "disabled"

            # 逻辑1.5: 如果是登录页状态（可达但未认证），自动尝试登录
            if network_state == "captive":
                now = datetime.datetime.now()
                can_retry = (
                    last_login_attempt is None
                    or (now - last_login_attempt).total_seconds() >= LOGIN_RETRY_INTERVAL
                )
                if can_retry:
                    log_message("[*] 正在尝试自动登录校园网...")
                    set_adapter_state("enable")
                    time.sleep(3)
                    run_login_script()
                    last_login_attempt = now
                    last_adapter_state = "enabled"
            
            # 逻辑2: 每天早上自动启用有线网并尝试连接
            if should_enable_morning(current_time, last_morning_check):
                if last_morning_check != current_time.date():
                    log_message(f"[*] 检测到早上 {MORNING_HOUR}:00，正在启用有线网并连接...")
                    set_adapter_state("enable")
                    time.sleep(10)  # 等待网卡启用
                    run_login_script()
                    last_morning_check = current_time.date()
                    last_adapter_state = "enabled"
            
            # 逻辑3: 校园网在线时，确保有线网已启用
            elif network_state in ("authenticated", "captive") and last_adapter_state != "enabled":
                log_message("[*] 校园网在线但有线网被禁用，正在重新启用...")
                set_adapter_state("enable")
                last_adapter_state = "enabled"
            
            # 等待下一轮检查
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log_message("[*] 监控脚本已停止")
            break
        except Exception as e:
            log_message(f"[!] 监控循环出错: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    # 检查是否是管理员权限
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False
    
    if not is_admin:
        log_message("[!] 检测到非管理员权限，正在以管理员身份重新启动...")
        try:
            import ctypes
            # 重新启动为管理员
            if hasattr(sys, 'frozen'):  # 如果是 exe
                script = sys.executable
            else:
                script = sys.executable
            
            params = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in sys.argv])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", script, params, None, 1)
            sys.exit()
        except Exception as e:
            log_message(f"[!] 权限提升失败: {e}")
            log_message("[!] 请右键选择'以管理员身份运行'")
            input("按 Enter 退出...")
            sys.exit(1)
    
    # 读取运行配置
    runtime_config = load_monitor_config()
    try:
        if "check_interval" in runtime_config:
            CHECK_INTERVAL = int(runtime_config.get("check_interval", CHECK_INTERVAL))
        if "morning_hour" in runtime_config:
            MORNING_HOUR = int(runtime_config.get("morning_hour", MORNING_HOUR))
    except Exception:
        pass

    configured_adapter = runtime_config.get("adapter_name", ADAPTER_NAME)
    ADAPTER_NAME = resolve_adapter_name(configured_adapter)

    log_message("✓ 已获取管理员权限")
    main_monitor_loop()
