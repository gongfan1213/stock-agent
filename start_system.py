#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChinaStockAgents 系统启动脚本
同时启动前端和后端服务
"""

import subprocess
import sys
import os
import time
import threading
import signal
from pathlib import Path

class TradingAgentsSystem:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
    def start_backend(self):
        """启动后端服务"""
        try:
            print("🚀 启动后端服务...")
            backend_dir = Path("backend")
            if not backend_dir.exists():
                print("❌ 错误: backend 目录不存在")
                return False
                
            os.chdir(backend_dir)
            
            # 检查依赖
            if not Path("requirements.txt").exists():
                print("❌ 错误: requirements.txt 不存在")
                return False
                
            # 安装依赖（如果需要）
            print("📦 检查后端依赖...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                             check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print("⚠️  依赖安装可能有问题，继续启动...")
            
            # 启动后端服务
            print("🔧 启动 FastAPI 服务...")
            self.backend_process = subprocess.Popen([
                sys.executable, "start_simple_server.py"
            ])
            
            print("✅ 后端服务启动成功")
            print("📡 后端地址: http://localhost:8000")
            print("🔗 WebSocket: ws://localhost:8000/ws")
            print("📚 API文档: http://localhost:8000/docs")
            
            return True
            
        except Exception as e:
            print(f"❌ 后端启动失败: {e}")
            return False
    
    def start_frontend(self):
        """启动前端服务"""
        try:
            print("🚀 启动前端服务...")
            frontend_dir = Path("frontend")
            if not frontend_dir.exists():
                print("❌ 错误: frontend 目录不存在")
                return False
                
            os.chdir(frontend_dir)
            
            # 检查 Node.js
            try:
                subprocess.run(["node", "--version"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ 错误: Node.js 未安装或不在 PATH 中")
                return False
            
            # 检查 package.json
            if not Path("package.json").exists():
                print("❌ 错误: package.json 不存在")
                return False
                
            # 安装依赖（如果需要）
            if not Path("node_modules").exists():
                print("📦 安装前端依赖...")
                subprocess.run(["npm", "install"], check=True)
            
            # 启动前端服务
            print("🌐 启动 React 开发服务器...")
            self.frontend_process = subprocess.Popen(["npm", "start"])
            
            print("✅ 前端服务启动成功")
            print("📡 前端地址: http://localhost:3000")
            
            return True
            
        except Exception as e:
            print(f"❌ 前端启动失败: {e}")
            return False
    
    def start_system(self):
        """启动整个系统"""
        print("🎯 ChinaStockAgents 中国股市智能体分析系统")
        print("=" * 50)
        
        # 启动后端
        backend_success = self.start_backend()
        if not backend_success:
            print("❌ 系统启动失败")
            return
        
        # 等待后端启动
        time.sleep(3)
        
        # 启动前端
        frontend_success = self.start_frontend()
        if not frontend_success:
            print("❌ 前端启动失败，但后端仍在运行")
            return
        
        print("\n🎉 系统启动成功！")
        print("=" * 50)
        print("📱 前端界面: http://localhost:3000")
        print("🔧 后端API: http://localhost:8000")
        print("📚 API文档: http://localhost:8000/docs")
        print("⏹️  按 Ctrl+C 停止所有服务")
        print("=" * 50)
        
        # 等待用户中断
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️  正在停止服务...")
            self.stop_system()
    
    def stop_system(self):
        """停止所有服务"""
        self.running = False
        
        if self.frontend_process:
            print("🛑 停止前端服务...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
        
        if self.backend_process:
            print("🛑 停止后端服务...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
        
        print("✅ 所有服务已停止")

def main():
    # 检查当前目录
    if not Path("backend").exists() or not Path("frontend").exists():
        print("❌ 错误: 请在项目根目录下运行此脚本")
        print("   确保 backend 和 frontend 目录存在")
        sys.exit(1)
    
    # 创建系统实例
    system = TradingAgentsSystem()
    
    # 设置信号处理
    def signal_handler(signum, frame):
        print("\n⏹️  收到停止信号...")
        system.stop_system()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动系统
    system.start_system()

if __name__ == "__main__":
    main() 