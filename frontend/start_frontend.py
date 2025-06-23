#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动 ChinaStockAgents 前端服务
"""

import subprocess
import sys
import os

def main():
    print("🚀 启动 ChinaStockAgents 前端服务...")
    print("📡 前端地址: http://localhost:3000")
    print("🔗 后端API: http://localhost:8000")
    print("⏹️  按 Ctrl+C 停止服务")
    print("-" * 50)
    
    # 检查是否在正确的目录
    if not os.path.exists("package.json"):
        print("❌ 错误: 请在 frontend 目录下运行此脚本")
        sys.exit(1)
    
    try:
        # 检查是否已安装依赖
        if not os.path.exists("node_modules"):
            print("📦 安装前端依赖...")
            subprocess.run(["npm", "install"], check=True)
        
        # 启动开发服务器
        print("🌐 启动开发服务器...")
        subprocess.run(["npm", "start"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  服务已停止")
        sys.exit(0)

if __name__ == "__main__":
    main() 