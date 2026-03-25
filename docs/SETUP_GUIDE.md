# 校园网自动化监控 - 使用指南

## 说明

当前仓库不再包含 `start_monitor.bat`，请使用以下两种方式之一启动：

- Python 脚本：`python src/network_monitor.py`
- Release 附件：下载并运行 `NJUPTNetworkMonitor.exe`

---

## 快速开始

### 方式 A：Python 运行（推荐开发者）

1. 安装依赖：

```
pip install -r requirements.txt
```

2. 配置账号：

- 复制 `config/config_sample.json` 为 `config/config.json`
- 填入学号和密码

3. 启动监控：

```
python src/network_monitor.py
```

---

### 方式 B：Release EXE（推荐普通使用）

1. 从 Release 页面下载 `NJUPTNetworkMonitor.exe`
2. 右键 exe → 以管理员身份运行

---

## 开机自启（任务计划程序）

### 方案 1：Python 版

1. Win + R 输入 `taskschd.msc`
2. 创建任务，触发器选“计算机启动时”
3. 操作选择“启动程序”
   - 程序或脚本：`python.exe` 的完整路径
   - 添加参数：`src\\network_monitor.py`
   - 起始于：仓库根目录（例如 `C:\\njupt-login`）
4. 在“常规”中勾选“使用最高权限运行”

### 方案 2：EXE 版

1. Win + R 输入 `taskschd.msc`
2. 创建任务，触发器选“计算机启动时”
3. 操作选择“启动程序”
   - 程序或脚本：`NJUPTNetworkMonitor.exe` 的完整路径
   - 起始于：exe 所在目录
4. 在“常规”中勾选“使用最高权限运行”

---

## 配置项

编辑 `src/network_monitor.py`：

```python
ADAPTER_NAME = "linenet"      # 网络适配器名称
CHECK_INTERVAL = 60           # 检查间隔（秒）
MORNING_HOUR = 7              # 自动启用时间（小时）
CAMPUS_NETWORK_URL = "https://p.njupt.edu.cn:802/"
```

同时也可以在 `config/config.json` 里覆盖这些参数：

```json
{
   "adapter_name": "linenet",
   "check_interval": 60,
   "morning_hour": 7
}
```

说明：
- `morning_hour` 采用“当天超过该时间后补执行一次”的逻辑。
- 例如电脑在 10:00 开机，也会执行当天的自动启用与登录。
- 如果 `adapter_name` 不存在，程序会自动探测常见有线网卡名（如 Ethernet/以太网）作为兜底。

---

## 日志

日志文件默认在运行目录下，文件名：`network_monitor.log`

查看方式：

```
type network_monitor.log
```

---

## 故障排除

1. 无管理员权限
   - 请右键“以管理员身份运行”
   - 任务计划程序中启用“使用最高权限运行”

2. 网卡操作失败
   - 用 `ipconfig /all` 确认网卡名
   - 修改 `ADAPTER_NAME`

3. 无法登录
   - 检查 `config/config.json`
   - 查看 `network_monitor.log` 错误信息
