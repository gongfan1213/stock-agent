#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动简化版 ChinaStockAgents FastAPI 服务
"""

import uvicorn
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 启动 ChinaStockAgents 简化版 FastAPI 服务...")
    print("📡 服务地址: http://localhost:8000")
    print("🔗 WebSocket: ws://localhost:8000/ws")
    print("📚 API文档: http://localhost:8000/docs")
    print("⏹️  按 Ctrl+C 停止服务")
    print("-" * 50)
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 