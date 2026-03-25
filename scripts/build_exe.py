"""
打包脚本 - 将 network_monitor.py 打包成 exe 可执行文件
运行: python build_exe.py
"""

import os
import sys
import subprocess
import shutil
import datetime

def main():
    print("=" * 60)
    print("NJUPT 校园网监控 - exe 打包工具")
    print("=" * 60)
    
    # 检查 PyInstaller 是否已安装
    print("\n[1/5] 检查依赖...")
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("✗ PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyInstaller"])
        print("✓ PyInstaller 安装完成")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    build_dir = os.path.join(project_root, "build")
    dist_dir = os.path.join(project_root, "dist")
    spec_file = os.path.join(project_root, "NJUPTNetworkMonitor.spec")

    # 确保依赖已安装
    print("\n[2/5] 安装 Python 依赖...")
    req_file = os.path.join(project_root, "requirements.txt")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file, "-q"], cwd=project_root)
    print("✓ 依赖安装完成")
    
    # 清理之前的构建
    print("\n[3/5] 清理旧文件...")
    for folder in [build_dir, dist_dir]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"✓ 删除 {os.path.basename(folder)}/")
    
    # 运行 PyInstaller
    print("\n[4/5] 开始打包 (这可能需要 1-2 分钟)...")
    
    network_monitor_path = os.path.join(project_root, "src", "network_monitor.py")
    config_sample_path = os.path.join(project_root, "config", "config_sample.json")
    icon_path = os.path.join(project_root, "app.ico")
    add_data_sep = ";" if os.name == "nt" else ":"
    
    # PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=NJUPTNetworkMonitor",           # exe 名称
        "--onefile",                            # 单文件模式
        "--windowed",                           # 隐藏控制台窗口（可选，改为 --console 显示控制台）
        f"--icon={icon_path}",                  # 图标（可选，可能没有）
        f"--add-data={config_sample_path}{add_data_sep}.",  # 添加配置示例文件
        "--collect-all=requests",               # 收集 requests 依赖
        "--collect-all=urllib3",                # 收集 urllib3 依赖
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        network_monitor_path
    ]
    
    # 移除 --icon 参数（如果文件不存在）
    if not os.path.exists(icon_path):
        cmd = [c for c in cmd if not c.startswith("--icon=")]
    
    try:
        subprocess.check_call(cmd, cwd=project_root)
        print("✓ 打包完成")
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        return False
    
    # 移动 exe 到项目根目录
    print("\n[5/5] 整理文件...")
    exe_src = os.path.join(dist_dir, "NJUPTNetworkMonitor.exe")
    exe_dst = os.path.join(project_root, "NJUPTNetworkMonitor.exe")
    
    if os.path.exists(exe_src):
        final_exe_path = exe_dst
        try:
            if os.path.exists(exe_dst):
                os.remove(exe_dst)
            shutil.copy2(exe_src, exe_dst)
        except PermissionError:
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            fallback_name = f"NJUPTNetworkMonitor-{timestamp}.exe"
            final_exe_path = os.path.join(project_root, fallback_name)
            shutil.copy2(exe_src, final_exe_path)
            print(f"[!] 默认输出文件被占用，已改为: {fallback_name}")

        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir)
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        if os.path.exists(spec_file):
            os.remove(spec_file)
        print(f"✓ exe 已生成: {os.path.basename(final_exe_path)}")
    else:
        print(f"✗ 找不到生成的 exe 文件")
        return False
    
    print("\n" + "=" * 60)
    print("✓ 打包完成！")
    print("=" * 60)
    print("\n使用方法:")
    print("1. 双击 NJUPTNetworkMonitor.exe 运行")
    print("2. 或右键 → 以管理员身份运行（推荐）")
    print("3. 可以将 exe 放在任何位置（需要同目录有 config.json）")
    print("\n提示:")
    print("- 第一次运行会弹出 UAC 权限提升请求（正常，因为要修改网络适配器）")
    print("- 可以配置开机自启（见 docs/SETUP_GUIDE.md）")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
