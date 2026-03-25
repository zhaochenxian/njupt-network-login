"""
校园网自动化监控脚本
- 监控校园网连接状态
- 校园网断开时自动禁用有线网
- 每天早上自动启用有线网并连接
- 支持后台持续运行
"""

import os
import sys
import json
import time
import datetime
import subprocess
import requests
import urllib3
import socket
from threading import Thread

# 禁用安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置
ADAPTER_NAME = "linenet"  # 网络适配器名称
LOG_FILE = "network_monitor.log"
CHECK_INTERVAL = 60  # 检查间隔（秒）
CAMPUS_NETWORK_URL = "https://p.njupt.edu.cn:802/"  # 校园网地址
MORNING_HOUR = 7  # 每天早上7点自动启用


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


def check_campus_network():
    """
    检查校园网是否在线
    返回: True (校园网在线) / False (校园网离线)
    """
    try:
        response = requests.get(
            CAMPUS_NETWORK_URL,
            timeout=3,
            verify=False,
            allow_redirects=True
        )
        # 如果能连接到校园网，说明在线
        log_message("[+] 检测到校园网在线")
        return True
    except requests.exceptions.Timeout:
        log_message("[-] 校园网响应超时，可能离线")
        return False
    except requests.exceptions.ConnectionError:
        log_message("[-] 无法连接校园网，可能离线")
        return False
    except Exception as e:
        log_message(f"[?] 校园网检测出错: {e}")
        return False


def run_login_script():
    """运行登录脚本"""
    try:
        log_message("正在运行登录脚本...")
        script_path = os.path.join(os.path.dirname(__file__), 'main.py')
        result = subprocess.run(
            ['python', script_path],
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


def should_enable_morning():
    """检查是否是早上启用时间"""
    current_hour = datetime.datetime.now().hour
    return current_hour == MORNING_HOUR


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
    
    while True:
        try:
            current_time = datetime.datetime.now()
            is_campus_online = check_campus_network()
            
            # 逻辑1: 如果校园网断开，禁用有线网适配器
            if not is_campus_online:
                if last_adapter_state != "disabled":
                    log_message("[*] 校园网已断开，正在禁用有线网适配器...")
                    set_adapter_state("disable")
                    last_adapter_state = "disabled"
            
            # 逻辑2: 每天早上自动启用有线网并尝试连接
            if should_enable_morning():
                if last_morning_check != current_time.date():
                    log_message(f"[*] 检测到早上 {MORNING_HOUR}:00，正在启用有线网并连接...")
                    set_adapter_state("enable")
                    time.sleep(10)  # 等待网卡启用
                    run_login_script()
                    last_morning_check = current_time.date()
                    last_adapter_state = "enabled"
            
            # 逻辑3: 校园网在线时，确保有线网已启用
            elif is_campus_online and last_adapter_state != "enabled":
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
    
    log_message("✓ 已获取管理员权限")
    main_monitor_loop()
