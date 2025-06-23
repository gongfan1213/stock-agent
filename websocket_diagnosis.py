#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 连接诊断工具
帮助诊断和解决 WebSocket 连接问题
"""

import asyncio
import websockets
import json
import requests
import socket
import subprocess
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

class WebSocketDiagnostic:
    def __init__(self):
        self.host = "localhost"
        self.port = 8000
        self.ws_url = f"ws://{self.host}:{self.port}/ws"
        self.http_url = f"http://{self.host}:{self.port}"
        self.results = {}
    
    def print_header(self, title: str):
        """打印标题"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_success(self, message: str):
        """打印成功信息"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """打印错误信息"""
        print(f"❌ {message}")
    
    def print_warning(self, message: str):
        """打印警告信息"""
        print(f"⚠️ {message}")
    
    def print_info(self, message: str):
        """打印信息"""
        print(f"ℹ️ {message}")
    
    def check_port_availability(self) -> bool:
        """检查端口是否可用"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except Exception as e:
            self.print_error(f"端口检查失败: {e}")
            return False
    
    def check_http_endpoint(self) -> bool:
        """检查HTTP端点"""
        try:
            response = requests.get(f"{self.http_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"HTTP API 正常 - {data.get('status', 'unknown')}")
                return True
            else:
                self.print_error(f"HTTP API 响应异常: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_error("无法连接到HTTP服务器")
            return False
        except Exception as e:
            self.print_error(f"HTTP检查失败: {e}")
            return False
    
    async def test_websocket_connection(self) -> bool:
        """测试WebSocket连接"""
        try:
            self.print_info(f"正在连接: {self.ws_url}")
            
            async with websockets.connect(self.ws_url, timeout=10) as websocket:
                self.print_success("WebSocket 连接已建立")
                
                # 等待连接确认
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    self.print_success(f"收到连接确认: {data.get('message', 'Unknown')}")
                    
                    # 发送测试消息
                    test_msg = {
                        "type": "test",
                        "message": "Diagnostic test",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(test_msg, ensure_ascii=False))
                    self.print_success("测试消息发送成功")
                    
                    return True
                    
                except asyncio.TimeoutError:
                    self.print_warning("等待连接确认超时")
                    return True  # 连接建立成功，只是没有收到确认
                except json.JSONDecodeError:
                    self.print_warning("连接确认消息格式异常")
                    return True
                    
        except websockets.exceptions.ConnectionRefusedError:
            self.print_error("WebSocket 连接被拒绝")
            return False
        except websockets.exceptions.InvalidURI:
            self.print_error("无效的 WebSocket URI")
            return False
        except asyncio.TimeoutError:
            self.print_error("WebSocket 连接超时")
            return False
        except Exception as e:
            self.print_error(f"WebSocket 连接失败: {e}")
            return False
    
    def check_process_status(self) -> Dict[str, Any]:
        """检查进程状态"""
        processes = {
            "backend": {
                "name": "Python后端服务",
                "ports": [8000],
                "commands": ["python", "uvicorn", "fastapi"]
            },
            "frontend": {
                "name": "React前端服务", 
                "ports": [3000],
                "commands": ["node", "npm"]
            }
        }
        
        results = {}
        
        for service, config in processes.items():
            self.print_info(f"检查 {config['name']}...")
            
            # 检查端口
            port_status = {}
            for port in config["ports"]:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(("localhost", port))
                sock.close()
                port_status[port] = result == 0
            
            # 检查进程
            process_status = {}
            for cmd in config["commands"]:
                try:
                    result = subprocess.run(
                        ["tasklist", "/FI", f"IMAGENAME eq {cmd}.exe"], 
                        capture_output=True, 
                        text=True
                    )
                    process_status[cmd] = "No tasks" not in result.stdout
                except:
                    process_status[cmd] = False
            
            results[service] = {
                "ports": port_status,
                "processes": process_status
            }
            
            # 打印结果
            port_ok = all(port_status.values())
            process_ok = any(process_status.values())
            
            if port_ok and process_ok:
                self.print_success(f"{config['name']} 运行正常")
            elif port_ok:
                self.print_warning(f"{config['name']} 端口可用但进程可能异常")
            else:
                self.print_error(f"{config['name']} 未运行")
        
        return results
    
    def check_network_config(self) -> Dict[str, Any]:
        """检查网络配置"""
        config = {}
        
        # 检查防火墙
        try:
            result = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles"], 
                capture_output=True, 
                text=True
            )
            config["firewall"] = result.returncode == 0
        except:
            config["firewall"] = False
        
        # 检查代理设置
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                              r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as key:
                proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
                config["proxy_enabled"] = proxy_enable == 1
        except:
            config["proxy_enabled"] = False
        
        return config
    
    def generate_recommendations(self) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        # 基于检查结果生成建议
        if not self.results.get("port_available", False):
            recommendations.extend([
                "1. 确保后端服务正在运行:",
                "   - 进入 backend 目录",
                "   - 运行: python start_simple_server.py",
                "",
                "2. 检查端口是否被占用:",
                "   - 运行: netstat -ano | findstr :8000",
                "   - 如果端口被占用，终止相关进程或更改端口"
            ])
        
        if not self.results.get("http_ok", False):
            recommendations.extend([
                "3. 检查后端服务配置:",
                "   - 确认 requirements.txt 中的依赖已安装",
                "   - 检查防火墙设置",
                "   - 确认服务绑定到正确的地址"
            ])
        
        if not self.results.get("websocket_ok", False):
            recommendations.extend([
                "4. WebSocket 连接问题:",
                "   - 检查 CORS 配置",
                "   - 确认 WebSocket 端点正确",
                "   - 检查浏览器控制台错误"
            ])
        
        if not recommendations:
            recommendations.append("🎉 所有检查都通过了！WebSocket 应该可以正常工作。")
        
        return recommendations
    
    async def run_diagnosis(self):
        """运行完整诊断"""
        self.print_header("WebSocket 连接诊断工具")
        self.print_info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 检查端口可用性
        self.print_header("端口可用性检查")
        self.results["port_available"] = self.check_port_availability()
        
        # 2. 检查HTTP端点
        self.print_header("HTTP API 检查")
        self.results["http_ok"] = self.check_http_endpoint()
        
        # 3. 检查WebSocket连接
        self.print_header("WebSocket 连接检查")
        self.results["websocket_ok"] = await self.test_websocket_connection()
        
        # 4. 检查进程状态
        self.print_header("服务进程检查")
        self.results["processes"] = self.check_process_status()
        
        # 5. 检查网络配置
        self.print_header("网络配置检查")
        self.results["network"] = self.check_network_config()
        
        # 6. 生成建议
        self.print_header("修复建议")
        recommendations = self.generate_recommendations()
        for rec in recommendations:
            print(rec)
        
        # 7. 总结
        self.print_header("诊断总结")
        total_checks = 3
        passed_checks = sum([
            self.results.get("port_available", False),
            self.results.get("http_ok", False),
            self.results.get("websocket_ok", False)
        ])
        
        print(f"检查项目: {total_checks}")
        print(f"通过项目: {passed_checks}")
        print(f"失败项目: {total_checks - passed_checks}")
        
        if passed_checks == total_checks:
            self.print_success("🎉 所有检查都通过了！")
        else:
            self.print_error("⚠️ 发现问题，请按照上述建议进行修复")
        
        return self.results

async def main():
    """主函数"""
    diagnostic = WebSocketDiagnostic()
    await diagnostic.run_diagnosis()

if __name__ == "__main__":
    asyncio.run(main()) 