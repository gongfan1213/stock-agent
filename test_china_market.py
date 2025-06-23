#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国股市智能体分析系统测试脚本
"""

import os
import sys
import asyncio
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.dataflows.china_interface import (
    get_china_stock_data,
    get_china_stock_info,
    get_china_market_overview,
    get_china_stock_news,
    get_china_fundamentals_analysis
)
from tradingagents.dataflows.akshare_utils import AKShareUtils

def test_china_data_interface():
    """测试中国股市数据接口"""
    print("=" * 60)
    print("测试中国股市数据接口")
    print("=" * 60)
    
    # 测试参数
    test_ticker = "000001"  # 平安银行
    test_date = datetime.now().strftime("%Y-%m-%d")
    look_back_days = 30
    
    try:
        # 测试1: 获取股票数据
        print(f"\n1. 测试获取股票数据: {test_ticker}")
        stock_data = get_china_stock_data(test_ticker, test_date, look_back_days)
        print(f"✓ 股票数据获取成功，数据长度: {len(stock_data)}")
        
        # 测试2: 获取股票信息
        print(f"\n2. 测试获取股票信息: {test_ticker}")
        stock_info = get_china_stock_info(test_ticker)
        print(f"✓ 股票信息获取成功")
        
        # 测试3: 获取市场概况
        print(f"\n3. 测试获取市场概况")
        market_overview = get_china_market_overview()
        print(f"✓ 市场概况获取成功")
        
        # 测试4: 获取股票新闻
        print(f"\n4. 测试获取股票新闻: {test_ticker}")
        stock_news = get_china_stock_news(test_ticker, test_date, 7)
        print(f"✓ 股票新闻获取成功")
        
        # 测试5: 获取基本面分析
        print(f"\n5. 测试获取基本面分析: {test_ticker}")
        fundamentals = get_china_fundamentals_analysis(test_ticker, test_date)
        print(f"✓ 基本面分析获取成功")
        
        print(f"\n✅ 所有数据接口测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    return True

def test_akshare_utils():
    """测试AKShare工具类"""
    print("\n" + "=" * 60)
    print("测试AKShare工具类")
    print("=" * 60)
    
    test_ticker = "000001"
    akshare_utils = AKShareUtils()
    
    try:
        # 测试1: 获取股票数据
        print(f"\n1. 测试AKShare获取股票数据: {test_ticker}")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        stock_data = akshare_utils.get_stock_data(test_ticker, start_date, end_date)
        if not stock_data.empty:
            print(f"✓ 股票数据获取成功，数据行数: {len(stock_data)}")
        else:
            print("⚠ 股票数据为空")
        
        # 测试2: 获取股票信息
        print(f"\n2. 测试AKShare获取股票信息: {test_ticker}")
        stock_info = akshare_utils.get_stock_info(test_ticker)
        if stock_info:
            print(f"✓ 股票信息获取成功，信息项数: {len(stock_info)}")
        else:
            print("⚠ 股票信息为空")
        
        # 测试3: 获取技术指标
        print(f"\n3. 测试AKShare获取技术指标: {test_ticker}")
        tech_data = akshare_utils.get_technical_indicators(test_ticker, "MACD")
        if not tech_data.empty:
            print(f"✓ 技术指标获取成功，数据行数: {len(tech_data)}")
        else:
            print("⚠ 技术指标数据为空")
        
        print(f"\n✅ AKShare工具类测试完成！")
        
    except Exception as e:
        print(f"❌ AKShare工具类测试失败: {e}")
        return False
    
    return True

def test_api_endpoints():
    """测试API端点"""
    print("\n" + "=" * 60)
    print("测试API端点")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    test_ticker = "000001"
    test_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # 测试1: 健康检查
        print(f"\n1. 测试健康检查")
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print(f"✓ 健康检查通过: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
        
        # 测试2: 系统信息
        print(f"\n2. 测试系统信息")
        response = requests.get(f"{base_url}/api/system-info")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 系统信息获取成功: {data['system_name']}")
            print(f"  市场类型: {data['market_type']}")
        else:
            print(f"❌ 系统信息获取失败: {response.status_code}")
            return False
        
        # 测试3: 股票信息
        print(f"\n3. 测试股票信息: {test_ticker}")
        response = requests.get(f"{base_url}/api/stock-info/{test_ticker}")
        if response.status_code == 200:
            print(f"✓ 股票信息获取成功")
        else:
            print(f"❌ 股票信息获取失败: {response.status_code}")
        
        # 测试4: 市场概况
        print(f"\n4. 测试市场概况")
        response = requests.get(f"{base_url}/api/market-overview")
        if response.status_code == 200:
            print(f"✓ 市场概况获取成功")
        else:
            print(f"❌ 市场概况获取失败: {response.status_code}")
        
        # 测试5: 股票数据
        print(f"\n5. 测试股票数据: {test_ticker}")
        params = {"date": test_date, "look_back_days": 30}
        response = requests.get(f"{base_url}/api/stock-data/{test_ticker}", params=params)
        if response.status_code == 200:
            print(f"✓ 股票数据获取成功")
        else:
            print(f"❌ 股票数据获取失败: {response.status_code}")
        
        print(f"\n✅ API端点测试完成！")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务器，请确保服务器正在运行")
        return False
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False
    
    return True

def test_china_toolkit():
    """测试中国股市工具包"""
    print("\n" + "=" * 60)
    print("测试中国股市工具包")
    print("=" * 60)
    
    try:
        from tradingagents.agents.utils.china_toolkit import ChinaToolkit
        
        toolkit = ChinaToolkit()
        test_ticker = "000001"
        test_date = datetime.now().strftime("%Y-%m-%d")
        
        # 测试工具包方法
        print(f"\n1. 测试工具包股票数据获取: {test_ticker}")
        result = toolkit.get_china_stock_data_online(test_ticker, "2024-01-01", test_date)
        print(f"✓ 工具包股票数据获取成功")
        
        print(f"\n2. 测试工具包股票信息获取: {test_ticker}")
        result = toolkit.get_china_stock_info_online(test_ticker)
        print(f"✓ 工具包股票信息获取成功")
        
        print(f"\n3. 测试工具包市场概况获取")
        result = toolkit.get_china_market_overview()
        print(f"✓ 工具包市场概况获取成功")
        
        print(f"\n✅ 中国股市工具包测试完成！")
        
    except Exception as e:
        print(f"❌ 中国股市工具包测试失败: {e}")
        return False
    
    return True

async def main():
    """主测试函数"""
    print("🚀 开始中国股市智能体分析系统测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行所有测试
    tests = [
        ("数据接口测试", test_china_data_interface),
        ("AKShare工具类测试", test_akshare_utils),
        ("中国股市工具包测试", test_china_toolkit),
        ("API端点测试", test_api_endpoints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
                
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("🎉 所有测试通过！中国股市适配成功！")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")

if __name__ == "__main__":
    asyncio.run(main()) 