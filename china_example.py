#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChinaStockAgents 中国股市使用示例
"""

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.config import get_china_market_config

def analyze_china_stock(ticker: str, date: str = "2025-06-21"):
    """
    分析中国股票
    
    Args:
        ticker: 股票代码，如 '000001', '600036'
        date: 分析日期，格式 'YYYY-MM-DD'
    """
    print(f"开始分析中国股票: {ticker}")
    print("=" * 50)
    
    # 获取中国股市优化配置
    config = get_china_market_config()
    
    # 初始化分析器
    ta = TradingAgentsGraph(debug=True, config=config)
    
    try:
        # 执行分析
        _, decision = ta.propagate(ticker, date)
        
        print(f"\n{ticker} 分析完成！")
        print("=" * 50)
        print("投资建议:")
        print(decision)
        
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
        print("请检查:")
        print("1. 股票代码是否正确")
        print("2. 网络连接是否正常")
        print("3. API配置是否正确")

def main():
    """主函数"""
    print("ChinaStockAgents 中国股市分析示例")
    print("=" * 50)
    
    # 示例股票列表
    stocks = [
        ("000001", "平安银行"),
        ("600036", "招商银行"),
        ("000002", "万科A"),
        ("600000", "浦发银行")
    ]
    
    print("可分析的股票:")
    for i, (code, name) in enumerate(stocks, 1):
        print(f"{i}. {code} - {name}")
    
    print("\n选择要分析的股票:")
    print("1. 分析平安银行 (000001)")
    print("2. 分析招商银行 (600036)")
    print("3. 分析万科A (000002)")
    print("4. 分析浦发银行 (600000)")
    print("5. 自定义股票代码")
    
    choice = input("\n请选择 (1-5): ").strip()
    
    if choice == "1":
        analyze_china_stock("000001")
    elif choice == "2":
        analyze_china_stock("600036")
    elif choice == "3":
        analyze_china_stock("000002")
    elif choice == "4":
        analyze_china_stock("600000")
    elif choice == "5":
        custom_ticker = input("请输入股票代码: ").strip()
        if custom_ticker:
            analyze_china_stock(custom_ticker)
        else:
            print("股票代码不能为空")
    else:
        print("无效选择，使用默认股票")
        analyze_china_stock("000001")

if __name__ == "__main__":
    main() 