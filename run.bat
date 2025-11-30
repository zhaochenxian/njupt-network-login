@echo off
:: 切换到当前 bat 文件所在的目录
cd /d %~dp0

:: 运行 Python 脚本
:: 如果你安装了多个 Python，可能需要把 'python' 换成 python.exe 的完整路径
python main.py

:: 保持窗口打开，出错可以看到（调试用）
:: pause