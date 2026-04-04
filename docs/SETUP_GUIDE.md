# 校园网自动化监控 - 使用指南

## 快速开始

### 方式 A：Python 运行（推荐开发者）

1. 安装依赖：

```
pip install -r requirements.txt
```

2. 配置账号：

```
cp config/config_sample.json config/config.json
```

编辑 `config/config.json`，填入学号和密码。

3. 启动监控（**需要管理员权限**）：

```
python src/network_monitor.py
```

程序会自动请求 UAC 权限提升。

---

### 方式 B：Release EXE（推荐普通使用）

1. 从 Release 页面下载 `NJUPTNetworkMonitor.exe`
2. 右键 exe → 以管理员身份运行
3. 将 `config.json` 放在 exe 同目录下

---

## 开机自启（任务计划程序）

1. Win + R 输入 `taskschd.msc`
2. 点击"创建任务"
3. **常规** 选项卡：
   - 名称：`NJUPT 校园网监控`
   - 勾选"使用最高权限运行"
4. **触发器** 选项卡：
   - 新建触发器 → 开始任务选"计算机启动时"
5. **操作** 选项卡（Python 版）：
   - 程序或脚本：`python.exe` 完整路径（例如 `C:\Python311\python.exe`）
   - 添加参数：`src\network_monitor.py`
   - 起始于：仓库根目录（例如 `C:\njupt-login`）
6. **条件** 选项卡：
   - 取消勾选"只在计算机使用交流电时启动任务"

---

## 配置说明

编辑 `config/config.json`：

```json
{
    "account": ",0,学号@cmcc",
    "password": "你的密码",
    "adapter_name": "linenet",
    "morning_hour": 7,
    "morning_minute": 0,
    "cutoff_hour": 23,
    "cutoff_minute": 30,
    "disable_advance_min": 2,
    "check_interval": 60,
    "login_retry_cooldown": 300
}
```

| 字段 | 说明 |
|------|------|
| `adapter_name` | 有线网卡名称，用 `ipconfig /all` 查看 |
| `morning_hour/minute` | 早上几点自动启用有线网并登录 |
| `cutoff_hour/minute` | 校园网几点断网（默认 23:30） |
| `disable_advance_min` | 提前几分钟禁用有线网（默认 2 分钟） |
| `check_interval` | 主循环检查间隔（秒） |
| `login_retry_cooldown` | 登录失败后多久再重试（秒） |

### 断网日历

程序内置的断网逻辑（不需要手动配置）：

- 周一 ~ 周四：23:30 断网
- 周五：**不断网**
- 周六：**不断网**
- 周日：23:30 断网

如果你的学校断网规律不同，修改 `network_monitor.py` 中的 `is_cutoff_day()` 函数即可。

---

## 日志

日志文件默认生成在运行目录下，文件名：`network_monitor.log`

查看日志：

```
type network_monitor.log
```

---

## 故障排除

### 网卡名不对，无法禁用/启用

用 `ipconfig /all` 查看你的有线网卡名称，然后修改 `config.json` 中的 `adapter_name`。

常见网卡名：`linenet`、`Ethernet`、`以太网`、`本地连接`

### 无管理员权限导致网卡操作失败

- Python 版：脚本会自动弹出 UAC 提升请求，点"是"即可
- 任务计划程序：确认已勾选"使用最高权限运行"

### 登录失败

- 检查 `config.json` 中 `account` 格式是否为 `,0,学号@cmcc`
- 查看 `network_monitor.log` 中的具体错误信息
- 手动运行 `python src/main.py` 测试登录

### 脚本在断网日没有自动禁用网卡

检查日志，确认 `should_disable_now` 时间窗口是否覆盖了你的实际情况：
- 默认在断网前 2 分钟（23:28）触发，到断网后 30 分钟内均会重试
- 可以调大 `disable_advance_min`（例如改为 5）让触发时间更早
