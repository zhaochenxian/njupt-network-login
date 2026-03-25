code
Markdown
# NJUPT Campus Network Auto Login

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-0078d4)

自动登录南京邮电大学（NJUPT）校园网的精简方案，支持自动网卡管理与后台监控。

---

## ✨ 特性

- 🤖 **自动登录** - 一键登录校园网，支持循环维持连接
- 🔄 **智能网卡管理** - 校园网断开时自动禁用有线网，减少困扰
- ⏰ **定时启动** - 每天早上自动启用网卡并登录
- 📡 **后台监控** - 24/7 持续运行，无需人工干预
- 🖥️ **开机自启** - 支持任务计划程序和启动文件夹
- 📝 **详细日志** - 所有操作都有记录，便于调试

---

## 🚀 快速开始

### 使用 Python 脚本

```bash
# 1. 克隆项目
git clone https://github.com/YOUR_USERNAME/njupt-login.git
cd njupt-login

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置账号密码
cp config/config_sample.json config/config.json
# 编辑 config/config.json，填入你的账号密码

# 4. 运行监控脚本
python src/network_monitor.py

# 或者运行一次登录脚本
python src/main.py
```

---

## 📋 配置文件

编辑 `config/config.json`：

```json
{
  "account": "你的学号",
  "password": "你的密码"
}
```

详见 [详细设置指南](docs/SETUP_GUIDE.md)

---

## 📁 项目结构

```
njupt-login/
├── README.md                         # 项目文档
├── LICENSE                           # MIT 许可证
├── requirements.txt                  # Python 依赖
├── .gitignore                        # Git 忽略文件
│
├── src/                              # 源代码
│   ├── main.py                       # 登录脚本
│   └── network_monitor.py            # 监控脚本
│
├── scripts/                          # 工具脚本
│   └── build_exe.py                  # EXE 打包脚本（可选）
│
├── config/                           # 配置文件
│   ├── config_sample.json            # 配置示例
│   └── config.json                   # 实际配置（不提交）
│
└── docs/                             # 文档
  └── SETUP_GUIDE.md                # 详细设置与排障
```

---

## 🔧 配置说明

编辑 `src/network_monitor.py` 中的变量：

```python
ADAPTER_NAME = "linenet"              # 网络适配器名称
CHECK_INTERVAL = 60                   # 检查间隔（秒）
MORNING_HOUR = 7                      # 早上启用时间
```

---

## 📚 文档

- [详细设置指南](docs/SETUP_GUIDE.md) - 包括开机自启和故障排除

---

## 📜 许可证

[MIT License](LICENSE)

---

## 🤝 贡献

欢迎 Issue 和 Pull Request！

---

**最后更新**: 2026-03-26

    