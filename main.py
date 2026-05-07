"""
公用机管理系统 Pro - 程序入口
启动方式: python main.py
"""
import sys
import os

# Ensure project root is on Python path
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app_bootstrap import bootstrap

if __name__ == "__main__":
    bootstrap()
