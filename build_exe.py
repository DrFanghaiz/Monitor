"""
使用 PyInstaller 打包公用机管理系统为 EXE
运行: python build_exe.py
"""
import subprocess
import sys
import os

def main():
    # 确保 pyinstaller 已安装
    try:
        import PyInstaller
        print(f"✓ PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 获取当前目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # PyInstaller 参数
    args = [
        "pyinstaller",
        "--name=公用机管理系统",           # EXE 名称
        "--onefile",                       # 打包为单个文件
        "--windowed",                      # 无控制台窗口 (GUI 应用)
        "--noconfirm",                     # 覆盖现有输出
        # 添加隐藏导入（customtkinter 和其他库需要）
        "--hidden-import=customtkinter",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=pystray._win32",
        "--hidden-import=matplotlib.backends.backend_tkagg",
        # 新增模块
        "--hidden-import=remote_monitor",
        "--hidden-import=web_server",
        "--hidden-import=tunnel",
        # 收集 customtkinter 的所有数据文件
        "--collect-all=customtkinter",
        # 包含 Web 模板目录
        "--add-data=web;web",
        # 入口点
        "timer.py"
    ]
    
    print("\n开始打包...")
    print(f"命令: {' '.join(args)}\n")
    
    subprocess.run(args)
    
    print("\n" + "="*50)
    print("打包完成！")
    print(f"EXE 位置: {os.path.join(script_dir, 'dist', '公用机管理系统.exe')}")
    print("="*50)

if __name__ == "__main__":
    main()
