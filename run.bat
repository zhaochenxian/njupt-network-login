@echo off
chcp 65001 >nul
title NJUPT 校园网自动登录

:: ── 检查管理员权限 ──────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 需要管理员权限才能控制网卡，正在请求提权...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: ── 切换到脚本所在目录 ───────────────────────────
cd /d "%~dp0"

:: ── 检查 config.json ────────────────────────────
if not exist "config\config.json" (
    echo [!] 未找到 config\config.json
    echo     请先将 config\config_sample.json 复制为 config\config.json 并填写账号密码
    pause
    exit /b 1
)

:: ── 检查 Python ──────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: ── 安装依赖（如尚未安装）──────────────────────
echo [*] 检查依赖...
pip show requests >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] 安装依赖...
    pip install -r requirements.txt -q
)

:: ── 启动守护进程 ─────────────────────────────────
echo.
echo ============================================
echo   NJUPT 校园网自动登录守护进程
echo   按 Ctrl+C 退出
echo ============================================
echo.
python src\network_monitor.py

pause
