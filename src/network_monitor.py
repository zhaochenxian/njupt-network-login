"""
校园网智能监控守护进程

功能：
  1. 断网前自动禁用有线网卡（防止系统卡在等待 DHCP 续约）
  2. 早晨指定时间自动启用有线网卡并登录
  3. 随时检测到未认证状态时自动触发登录
  4. 联网查询法定节假日（NateScarlet/holiday-cn），自动处理调休

断网规则：
  - 今晚要不要断网 = 明天要不要上班
  - 明天是工作日（含调休上班）→ 今晚23:30断网 → 需要禁用网卡
  - 明天是休息日（含法定假日）→ 今晚不断网 → 不用禁用网卡

用法：
  python src/network_monitor.py          # 正常启动守护进程
  python src/network_monitor.py --once   # 只执行一次登录（用于调试）
"""

import os
import sys
import json
import time
import socket
import datetime
import subprocess
import random
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ──────────────────────────────────────────────
#  节假日数据
# ──────────────────────────────────────────────

# holiday-cn 数据源（按优先级尝试）
_HOLIDAY_URLS = [
    "https://cdn.jsdelivr.net/gh/NateScarlet/holiday-cn@master/{year}.json",
    "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json",
]

# 本地缓存文件目录（与 config/ 同级）
_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")

# 内存缓存：{年份: {日期字符串: is_off_day(True=休息)}}
_holiday_cache: dict = {}
# 记录每年数据的最后联网拉取日期，用于每天尝试刷新
_holiday_fetch_date: dict = {}


def _cache_file(year: int) -> str:
    """返回本地缓存文件路径。"""
    return os.path.join(_CACHE_DIR, f"holiday_{year}.json")


def _load_local_cache(year: int) -> dict:
    """从本地文件加载节假日缓存，文件不存在则返回空字典。"""
    path = _cache_file(year)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[holiday] 从本地缓存加载 {year} 年节假日数据（{len(data)} 条）")
        return data
    except Exception as e:
        print(f"[holiday] 读取本地缓存失败: {e}")
        return {}


def _save_local_cache(year: int, data: dict):
    """将节假日数据写入本地缓存文件。"""
    path = _cache_file(year)
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"[holiday] 写入本地缓存失败: {e}")


def _fetch_holiday_year(year: int) -> dict:
    """
    从 holiday-cn 获取指定年份的特殊日期映射。
    联网成功时同步写入本地缓存文件。
    联网失败时尝试读取本地缓存文件。
    均失败则返回空字典（回退到星期规则）。
    """
    for url_tpl in _HOLIDAY_URLS:
        url = url_tpl.format(year=year)
        try:
            resp = requests.get(url, timeout=10, verify=False)
            if resp.status_code == 200:
                data = resp.json()
                result = {d["date"]: bool(d["isOffDay"]) for d in data.get("days", [])}
                print(f"[holiday] 已联网加载 {year} 年节假日数据（{len(result)} 条特殊日期）")
                _save_local_cache(year, result)
                return result
        except Exception as e:
            print(f"[holiday] {url[:60]} 失败: {e}")

    # 联网全部失败，尝试本地缓存
    local = _load_local_cache(year)
    if local:
        print(f"[holiday] 无网络，使用本地缓存数据（{year} 年，{len(local)} 条）")
        return local

    print(f"[holiday] 警告：无法获取 {year} 年节假日数据，回退到星期规则")
    return {}


def is_workday(date: datetime.date) -> bool:
    """
    判断指定日期是否为工作日。
    优先使用在线节假日数据，联网失败时使用本地缓存，
    两者均无时回退到星期规则（周一~五=工作日）。
    每天至多尝试一次联网刷新缓存。
    """
    year = date.year
    today = datetime.date.today()

    # 首次加载 或 今天还没联网刷新过该年份数据
    if year not in _holiday_cache or _holiday_fetch_date.get(year) != today:
        fetched = _fetch_holiday_year(year)
        _holiday_cache[year] = fetched
        # 仅当联网成功（数据非空或本地有缓存）时才标记今天已刷新
        if fetched or os.path.exists(_cache_file(year)):
            _holiday_fetch_date[year] = today

    date_str = date.strftime("%Y-%m-%d")
    special = _holiday_cache.get(year, {})

    if date_str in special:
        # True = 休息日（法定假日或调休休息），False = 调休上班日
        return not special[date_str]

    # 普通日期：周一(0)~周五(4) 是工作日
    return date.weekday() <= 4


def is_cutoff_night(dt: datetime.datetime) -> bool:
    """
    今晚要不要断网：若明天是工作日，今晚就断网。
    """
    tomorrow = (dt + datetime.timedelta(days=1)).date()
    return is_workday(tomorrow)


# ──────────────────────────────────────────────
#  配置加载
# ──────────────────────────────────────────────

def load_config() -> dict:
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config", "config.json"
    )
    if not os.path.exists(config_path):
        print("[!] 找不到 config/config.json，请先复制 config_sample.json 并填写账号密码")
        sys.exit(1)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] 读取配置文件失败: {e}")
        sys.exit(1)


# ──────────────────────────────────────────────
#  网卡控制
# ──────────────────────────────────────────────

def _run_netsh(action: str, adapter: str) -> bool:
    """
    用 netsh 启用/禁用网卡。需要管理员权限。
    action: "enable" 或 "disable"
    """
    cmd = ["netsh", "interface", "set", "interface", f'"{adapter}"', action]
    try:
        ret = subprocess.run(
            " ".join(cmd),
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if ret.returncode == 0:
            return True
        print(f"[netsh] 错误: {ret.stderr.strip() or ret.stdout.strip()}")
        return False
    except Exception as e:
        print(f"[netsh] 异常: {e}")
        return False


def disable_adapter(adapter: str) -> bool:
    ok = _run_netsh("disable", adapter)
    if ok:
        print(f"[网卡] 已禁用 '{adapter}'")
    else:
        print(f"[网卡] 禁用 '{adapter}' 失败（需要管理员权限？）")
    return ok


def enable_adapter(adapter: str) -> bool:
    ok = _run_netsh("enable", adapter)
    if ok:
        print(f"[网卡] 已启用 '{adapter}'")
    else:
        print(f"[网卡] 启用 '{adapter}' 失败（需要管理员权限？）")
    return ok


# ──────────────────────────────────────────────
#  网络状态检测
# ──────────────────────────────────────────────

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def needs_login() -> bool:
    """
    检测是否需要登录校园网（检测到 captive portal 重定向或无法访问外网）。
    """
    try:
        resp = requests.get(
            "http://connect.rom.miui.com/generate_204",
            timeout=5,
            allow_redirects=True,
            verify=False,
        )
        # 204 = 已联网；其他状态码或被重定向到认证页 = 需要登录
        if resp.status_code == 204:
            return False
        return True
    except requests.exceptions.ConnectionError:
        return True
    except Exception:
        return True


def is_adapter_up(adapter: str) -> bool:
    """
    检测网卡是否处于启用状态。
    """
    try:
        ret = subprocess.run(
            f'netsh interface show interface "{adapter}"',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return "已启用" in ret.stdout or "Enabled" in ret.stdout
    except Exception:
        return False


# ──────────────────────────────────────────────
#  登录请求
# ──────────────────────────────────────────────

def do_login(account: str, password: str) -> bool:
    """
    执行一次登录请求。
    返回 True = 成功（或已在线），False = 失败需重试。
    """
    url = "https://p.njupt.edu.cn:802/eportal/portal/login"
    ip = get_local_ip()
    now = datetime.datetime.now().strftime("%H:%M:%S")

    params = {
        "callback": "dr1003",
        "login_method": "1",
        "user_account": account,
        "user_password": password,
        "wlan_user_ip": ip,
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
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, verify=False, timeout=8)
        text = resp.text
        if '"result":1' in text or "Portal协议认证成功" in text:
            print(f"[{now}] [+] 登录成功！(IP: {ip})")
            return True
        elif "AC999" in text or '"ret_code":2' in text:
            print(f"[{now}] [=] 已在线，无需重复登录。")
            return True
        else:
            print(f"[{now}] [?] 登录未成功，响应: {text[:120]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[{now}] [!] 网络异常: {e}")
        return False


# ──────────────────────────────────────────────
#  守护主循环
# ──────────────────────────────────────────────

def monitor_loop(cfg: dict):
    account = cfg["account"]
    password = cfg["password"]
    adapter = cfg.get("adapter_name", "以太网")

    morning_hour   = int(cfg.get("morning_hour",   7))
    morning_minute = int(cfg.get("morning_minute", 0))
    cutoff_hour    = int(cfg.get("cutoff_hour",   23))
    cutoff_minute  = int(cfg.get("cutoff_minute", 30))
    advance_min    = int(cfg.get("disable_advance_min", 2))
    check_interval = int(cfg.get("check_interval", 60))
    login_cooldown = int(cfg.get("login_retry_cooldown", 300))

    # 状态标志
    adapter_disabled_tonight = False   # 今晚是否已经禁用了网卡
    morning_triggered_today  = False   # 今天早上是否已经触发了启用
    last_login_attempt       = 0.0    # 上次尝试登录的时间戳（用于冷却）

    # 每天零点重置标志位
    last_date = datetime.date.today()

    print(f"[monitor] 守护进程启动，检测间隔 {check_interval}s")
    print(f"[monitor] 网卡名称: {adapter}")
    print(f"[monitor] 早起时间: {morning_hour:02d}:{morning_minute:02d}")
    print(f"[monitor] 断网时间: {cutoff_hour:02d}:{cutoff_minute:02d}（提前 {advance_min} 分钟禁用）")

    # 启动时立即预加载当年及明年节假日数据
    today_init = datetime.date.today()
    is_workday(today_init)
    is_workday(today_init + datetime.timedelta(days=1))

    while True:
        try:
            now = datetime.datetime.now()
            today = now.date()

            # ── 跨天重置 ──────────────────────────────
            if today != last_date:
                last_date = today
                adapter_disabled_tonight = False
                morning_triggered_today  = False
                print(f"[monitor] 新的一天 {today}，重置状态标志")
                # 提前加载今年/明年节假日数据
                is_workday(today)
                is_workday(today + datetime.timedelta(days=1))

            # ── 路径A：断网前禁用网卡 ────────────────
            if not adapter_disabled_tonight and is_cutoff_night(now):
                cutoff_total   = cutoff_hour * 60 + cutoff_minute
                current_total  = now.hour * 60 + now.minute
                minutes_to_cut = cutoff_total - current_total

                # 在 [断网前 advance_min 分钟, 断网后 60 分钟] 窗口内触发
                if -60 <= minutes_to_cut <= advance_min:
                    print(f"[monitor] 今晚断网，距断网 {minutes_to_cut} 分钟，禁用网卡...")
                    if disable_adapter(adapter):
                        adapter_disabled_tonight = True
                        # 禁用成功后等到明天早上前，每5分钟检查一次就够了
                        time.sleep(300)
                        continue
                    # 禁用失败（权限不足等），按正常间隔重试

            # ── 路径B：早晨启用网卡并登录 ────────────
            if not morning_triggered_today:
                morning_total  = morning_hour * 60 + morning_minute
                current_total  = now.hour * 60 + now.minute

                # 已过早起时间：若网卡禁用则先启用，之后无论如何都尝试登录
                if current_total >= morning_total:
                    morning_triggered_today = True
                    if not is_adapter_up(adapter):
                        print(f"[monitor] 早起时间到，启用网卡...")
                        enable_adapter(adapter)
                        print("[monitor] 等待 10s DHCP 获取地址...")
                        time.sleep(10)
                    # 尝试登录（无论网卡原先是否启用）
                    do_login(account, password)
                    last_login_attempt = time.time()
                    time.sleep(check_interval)
                    continue

            # ── 路径C：随时检测未认证状态 ────────────
            # 网卡必须是启用状态才值得检测
            if is_adapter_up(adapter):
                now_ts = time.time()
                if now_ts - last_login_attempt >= login_cooldown:
                    if needs_login():
                        print(f"[monitor] 检测到未认证，尝试登录...")
                        do_login(account, password)
                        last_login_attempt = now_ts

        except KeyboardInterrupt:
            print("\n[monitor] 用户中断，退出。")
            break
        except Exception as e:
            print(f"[monitor] 意外错误: {e}")

        time.sleep(check_interval)


# ──────────────────────────────────────────────
#  入口
# ──────────────────────────────────────────────

def main():
    cfg = load_config()

    if "--once" in sys.argv:
        # 单次登录模式（用于调试或手动触发）
        do_login(cfg["account"], cfg["password"])
        return

    monitor_loop(cfg)


if __name__ == "__main__":
    main()
