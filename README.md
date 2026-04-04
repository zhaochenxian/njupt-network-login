# NJUPT Campus Network Auto Login

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-0078d4)

自动登录南京邮电大学（NJUPT）校园网的精简方案，支持智能断网时间表与后台监控。

---

## 特性

- **自动登录** — 检测到需要认证时自动发起登录请求
- **智能断网时间表** — 按校园网实际断网规律自动禁用/启用有线网
- **每日定时启用** — 早上到达配置时间后自动启用网卡并登录
- **后台持续监控** — 24/7 无人值守运行
- **开机自启支持** — 配合 Windows 任务计划程序使用

---

## 校园网断网规律

| 日期 | 断网 |
|------|------|
| 周一 ~ 周四（工作日非最后一天） | 23:30 断网 |
| 周五（工作日最后一天） | **不断网** |
| 周六（休息日非最后一天） | **不断网** |
| 周日（休息日最后一天） | 23:30 断网 |

脚本会在断网时间前 2 分钟（可配置）自动禁用有线网，第二天早上再自动启用并登录。

---

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置账号密码
cp config/config_sample.json config/config.json
# 编辑 config/config.json，填入你的学号和密码

# 3. 启动监控（需要管理员权限）
python src/network_monitor.py
```

---

## 配置文件

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
    "login_retry_cooldown": 300,
    "interval": 5
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `account` | 学号（格式：`,0,学号@cmcc`） | — |
| `password` | 密码 | — |
| `adapter_name` | 有线网卡名称 | `linenet` |
| `morning_hour` | 早上自动启用时间（时） | `7` |
| `morning_minute` | 早上自动启用时间（分） | `0` |
| `cutoff_hour` | 校园网断网时间（时） | `23` |
| `cutoff_minute` | 校园网断网时间（分） | `30` |
| `disable_advance_min` | 提前多少分钟禁用有线网 | `2` |
| `check_interval` | 主循环检查间隔（秒） | `60` |
| `login_retry_cooldown` | 登录重试冷却时间（秒） | `300` |

---

## 项目结构

```
njupt-login/
├── README.md
├── LICENSE
├── requirements.txt
├── src/
│   ├── main.py              # 一次性登录脚本
│   └── network_monitor.py   # 后台监控脚本（主程序）
├── scripts/
│   └── build_exe.py         # EXE 打包脚本（可选）
├── config/
│   ├── config_sample.json   # 配置示例
│   └── config.json          # 实际配置（不提交 Git）
└── docs/
    └── SETUP_GUIDE.md       # 详细设置指南
```

---

## 文档

- [详细设置指南](docs/SETUP_GUIDE.md)

---

## 许可证

[MIT License](LICENSE)

---

**最后更新**: 2026-04-04
