#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 连接测试脚本
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_websocket_connection():
    """测试WebSocket连接"""
    uri = "ws://localhost:8000/ws"
    
    print(f"🔗 正在连接 WebSocket: {uri}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接已建立")
            
            # 等待连接确认消息
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 收到连接确认: {message}")
                
                # 解析JSON消息
                try:
                    data = json.loads(message)
                    print(f"📊 消息类型: {data.get('type')}")
                    print(f"📊 消息内容: {data.get('message')}")
                    print(f"📊 时间戳: {data.get('timestamp')}")
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON解析失败: {e}")
                
            except asyncio.TimeoutError:
                print("⚠️ 等待连接确认超时")
            
            # 发送测试消息
            test_message = {
                "type": "test",
                "message": "Hello from Python client",
                "timestamp": datetime.now().isoformat(),
                "client": "test_websocket.py"
            }
            
            print(f"📤 发送测试消息: {json.dumps(test_message, ensure_ascii=False)}")
            await websocket.send(json.dumps(test_message, ensure_ascii=False))
            
            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 收到响应: {response}")
            except asyncio.TimeoutError:
                print("⚠️ 等待响应超时")
            
            # 保持连接一段时间
            print("⏳ 保持连接 10 秒...")
            await asyncio.sleep(10)
            
            print("🛑 关闭连接")
            
    except websockets.exceptions.ConnectionRefusedError:
        print("❌ 连接被拒绝 - 服务器可能未运行或端口被占用")
    except websockets.exceptions.InvalidURI:
        print("❌ 无效的 WebSocket URI")
    except Exception as e:
        print(f"❌ WebSocket 连接失败: {e}")
        print(f"❌ 错误类型: {type(e).__name__}")

async def test_multiple_connections():
    """测试多个并发连接"""
    uri = "ws://localhost:8000/ws"
    num_connections = 3
    
    print(f"🔗 测试 {num_connections} 个并发连接...")
    
    async def single_connection(conn_id):
        try:
            async with websockets.connect(uri) as websocket:
                print(f"✅ 连接 {conn_id} 已建立")
                
                # 发送消息
                message = {
                    "type": "test",
                    "connection_id": conn_id,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(message, ensure_ascii=False))
                
                # 等待响应
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    print(f"📨 连接 {conn_id} 收到: {response}")
                except asyncio.TimeoutError:
                    print(f"⚠️ 连接 {conn_id} 响应超时")
                
                await asyncio.sleep(2)
                print(f"🛑 连接 {conn_id} 已关闭")
                
        except Exception as e:
            print(f"❌ 连接 {conn_id} 失败: {e}")
    
    # 创建多个并发连接
    tasks = [single_connection(i) for i in range(num_connections)]
    await asyncio.gather(*tasks)

def test_http_endpoints():
    """测试HTTP端点"""
    import requests
    
    print("🌐 测试 HTTP 端点...")
    
    try:
        # 测试健康检查
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"📊 响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到HTTP服务器")
    except Exception as e:
        print(f"❌ HTTP测试失败: {e}")

async def main():
    """主函数"""
    print("🚀 WebSocket 连接测试工具")
    print("=" * 50)
    
    # 测试HTTP端点
    test_http_endpoints()
    print()
    
    # 测试单个WebSocket连接
    print("🔗 测试单个 WebSocket 连接")
    print("-" * 30)
    await test_websocket_connection()
    print()
    
    # 测试多个并发连接
    print("🔗 测试多个并发 WebSocket 连接")
    print("-" * 30)
    await test_multiple_connections()
    print()
    
    print("✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(main()) 