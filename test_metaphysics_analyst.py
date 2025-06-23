#!/usr/bin/env python3
"""
测试传统分析师功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.analysts.metaphysics_analyst import create_metaphysics_analyst, MetaphysicsAnalysis
from tradingagents.agents.utils.china_toolkit import ChinaToolkit
from tradingagents.default_config import DEFAULT_CONFIG

async def test_metaphysics_analyst():
    """Test the metaphysics analyst functionality."""
    
    # Initialize the LLM
    # llm = 你的自定义 LLM 实例
    llm = None  # TODO: 这里请传入你的自定义 LLM 实例
    
    # Initialize the toolkit
    toolkit = ChinaToolkit()
    
    # Create the metaphysics analyst
    metaphysics_analyst = create_metaphysics_analyst(llm, toolkit)
    
    # Test state
    test_state = {
        "company_name": "平安银行",
        "messages": []
    }
    
    print("开始测试玄学分析师...")
    print("=" * 50)
    
    try:
        # Run the metaphysics analysis
        result_state = metaphysics_analyst(test_state)
        
        # Extract the analysis result
        messages = result_state["messages"]
        metaphysics_message = next((msg for msg in messages if msg.get("analyst_type") == "metaphysics"), None)
        
        if metaphysics_message:
            analysis = metaphysics_message.get("analysis")
            print("✅ 玄学分析完成！")
            print("\n📊 分析结果:")
            print("-" * 30)
            
            if hasattr(analysis, 'five_elements_analysis'):
                print(f"🔮 五行分析: {analysis.five_elements_analysis}")
                print()
            
            if hasattr(analysis, 'eight_trigrams_analysis'):
                print(f"☯️ 八卦分析: {analysis.eight_trigrams_analysis}")
                print()
            
            if hasattr(analysis, 'heavenly_stems_analysis'):
                print(f"🌙 天干地支分析: {analysis.heavenly_stems_analysis}")
                print()
            
            if hasattr(analysis, 'metaphysics_forecast'):
                print(f"🔮 玄学预测: {analysis.metaphysics_forecast}")
                print()
            
            if hasattr(analysis, 'auspicious_timing'):
                print(f"📅 吉时建议: {analysis.auspicious_timing}")
                print()
        else:
            print("❌ 未找到玄学分析结果")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def test_traditional_calendar():
    """测试传统历法工具"""
    print("=== 测试传统历法工具 ===\n")
    
    toolkit = ChinaToolkit()
    
    # 测试不同日期的传统历法信息
    test_dates = ["2024-01-15", "2024-02-04", "2024-03-21", "2024-06-21", "2024-12-22"]
    
    for date in test_dates:
        print(f"日期: {date}")
        try:
            calendar_info = toolkit.get_traditional_calendar_info(date)
            print(calendar_info)
            print("-" * 50)
        except Exception as e:
            print(f"获取历法信息失败: {e}")
            print("-" * 50)

if __name__ == "__main__":
    print("开始测试传统分析师功能...\n")
    
    # 测试传统历法工具
    test_traditional_calendar()
    
    print("\n" + "="*60 + "\n")
    
    # 测试玄学分析师
    asyncio.run(test_metaphysics_analyst())
    
    print("\n测试完成！") 