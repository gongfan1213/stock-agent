"""
中国股票数据接口 - 基于 AKShare
"""

from typing import Annotated, Dict
from .akshare_utils import akshare_utils
from datetime import datetime, timedelta
import pandas as pd
import json
import os
from .config import get_config, DATA_DIR


class ChinaInterface:
    def __init__(self, config=None):
        if config is None:
            self.config = get_config()
        else:
            self.config = config

    def get_stock_data(
        self,
        ticker: Annotated[str, "股票代码，如 '000001' 或 '600000'"],
        curr_date: Annotated[str, "当前日期，格式 YYYY-MM-DD"],
        look_back_days: Annotated[int, "回看天数"],
    ) -> str:
        """
        获取中国股票历史数据
        
        Args:
            ticker: 股票代码
            curr_date: 当前日期
            look_back_days: 回看天数
            
        Returns:
            str: 格式化的股票数据报告
        """
        try:
            end_date = datetime.strptime(curr_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=look_back_days)
            
            stock_data = akshare_utils.get_stock_data(
                symbol=ticker,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=curr_date
            )
            
            if stock_data.empty:
                return f"无法获取 {ticker} 的股票数据"
            
            # 计算基本统计信息
            latest_price = stock_data['Close'].iloc[-1]
            price_change = stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[0]
            price_change_pct = (price_change / stock_data['Close'].iloc[0]) * 100
            
            report = f"""
## {ticker} 股票数据分析报告 ({start_date.strftime('%Y-%m-%d')} 至 {curr_date})

### 基本价格信息
- 最新收盘价: ¥{latest_price:.2f}
- 期间涨跌: ¥{price_change:.2f} ({price_change_pct:.2f}%)
- 最高价: ¥{stock_data['High'].max():.2f}
- 最低价: ¥{stock_data['Low'].min():.2f}
- 平均成交量: {stock_data['Volume'].mean():.0f}

### 技术指标
- 20日均价: ¥{stock_data['Close'].rolling(20).mean().iloc[-1]:.2f}
- 50日均价: ¥{stock_data['Close'].rolling(50).mean().iloc[-1]:.2f}
- 波动率: {stock_data['Close'].pct_change().std() * 100:.2f}%

### 最近5个交易日数据
"""
            
            # 添加最近5个交易日的数据
            recent_data = stock_data.tail(5)
            for date, row in recent_data.iterrows():
                report += f"""
**{date.strftime('%Y-%m-%d')}**
- 开盘: ¥{row['Open']:.2f}
- 收盘: ¥{row['Close']:.2f}
- 最高: ¥{row['High']:.2f}
- 最低: ¥{row['Low']:.2f}
- 成交量: {row['Volume']:.0f}
"""
            
            return report
            
        except Exception as e:
            return f"获取 {ticker} 股票数据时出错: {str(e)}"

    def get_stock_info(
        self,
        ticker: Annotated[str, "股票代码"],
    ) -> str:
        """
        获取中国股票基本信息
        
        Args:
            ticker: 股票代码
            
        Returns:
            str: 股票基本信息报告
        """
        try:
            stock_info = akshare_utils.get_stock_info(ticker)
            
            if not stock_info:
                return f"无法获取 {ticker} 的股票信息"
            
            report = f"""
## {ticker} 股票基本信息

### 公司信息
- 股票名称: {stock_info.get('股票简称', 'N/A')}
- 股票代码: {ticker}
- 所属行业: {stock_info.get('所属行业', 'N/A')}
- 上市日期: {stock_info.get('上市日期', 'N/A')}
- 总股本: {stock_info.get('总股本', 'N/A')}
- 流通股本: {stock_info.get('流通股本', 'N/A')}

### 财务指标
- 市盈率(TTM): {stock_info.get('市盈率(TTM)', 'N/A')}
- 市净率: {stock_info.get('市净率', 'N/A')}
- 每股收益: {stock_info.get('每股收益', 'N/A')}
- 每股净资产: {stock_info.get('每股净资产', 'N/A')}
- 净资产收益率: {stock_info.get('净资产收益率', 'N/A')}

### 交易信息
- 最新价: {stock_info.get('最新价', 'N/A')}
- 涨跌幅: {stock_info.get('涨跌幅', 'N/A')}
- 成交量: {stock_info.get('成交量', 'N/A')}
- 成交额: {stock_info.get('成交额', 'N/A')}
- 换手率: {stock_info.get('换手率', 'N/A')}
"""
            
            return report
            
        except Exception as e:
            return f"获取 {ticker} 股票信息时出错: {str(e)}"

    def get_market_overview(self) -> str:
        """
        获取中国股市整体概况
        
        Returns:
            str: 市场概况报告
        """
        try:
            # 获取主要指数数据
            indices = {
                '上证指数': '000001',
                '深证成指': '399001',
                '创业板指': '399006',
                '沪深300': '000300'
            }
            
            report = """
## 中国股市整体概况

### 主要指数表现
"""
            
            for name, code in indices.items():
                try:
                    data = akshare_utils.get_stock_data(
                        symbol=code,
                        start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                        end_date=datetime.now().strftime("%Y-%m-%d")
                    )
                    
                    if not data.empty:
                        latest_price = data['Close'].iloc[-1]
                        price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
                        price_change_pct = (price_change / data['Close'].iloc[0]) * 100
                        
                        report += f"""
**{name} ({code})**
- 最新点位: {latest_price:.2f}
- 30日涨跌: {price_change:.2f} ({price_change_pct:.2f}%)
"""
                except:
                    report += f"""
**{name} ({code})**
- 数据获取失败
"""
            
            return report
            
        except Exception as e:
            return f"获取市场概况时出错: {str(e)}"

    def get_stock_news(
        self,
        ticker: Annotated[str, "股票代码"],
        curr_date: Annotated[str, "当前日期"],
        look_back_days: Annotated[int, "回看天数"],
    ) -> str:
        """
        获取中国股票相关新闻（模拟实现）
        
        Args:
            ticker: 股票代码
            curr_date: 当前日期
            look_back_days: 回看天数
            
        Returns:
            str: 新闻摘要
        """
        try:
            # 这里可以集成新闻API，如新浪财经、东方财富等
            # 目前返回模拟数据
            report = f"""
## {ticker} 相关新闻摘要 ({look_back_days} 天内)

### 重要新闻
1. **公司公告**: 请关注公司最新公告和财报发布
2. **行业动态**: 关注所属行业的最新政策和发展趋势
3. **市场分析**: 关注分析师对该股票的最新评级和预测

### 建议关注
- 公司基本面变化
- 行业政策影响
- 市场情绪变化
- 技术面分析

*注: 实际使用时建议集成专业的新闻API服务*
"""
            
            return report
            
        except Exception as e:
            return f"获取 {ticker} 新闻时出错: {str(e)}"

    def get_fundamentals_analysis(
        self,
        ticker: Annotated[str, "股票代码"],
        curr_date: Annotated[str, "当前日期"],
    ) -> str:
        """
        获取中国股票基本面分析
        
        Args:
            ticker: 股票代码
            curr_date: 当前日期
            
        Returns:
            str: 基本面分析报告
        """
        try:
            stock_info = akshare_utils.get_stock_info(ticker)
            
            if not stock_info:
                return f"无法获取 {ticker} 的基本面数据"
            
            report = f"""
## {ticker} 基本面分析报告

### 估值指标
- 市盈率(TTM): {stock_info.get('市盈率(TTM)', 'N/A')}
- 市净率: {stock_info.get('市净率', 'N/A')}
- 市销率: {stock_info.get('市销率', 'N/A')}
- 股息率: {stock_info.get('股息率', 'N/A')}

### 盈利能力
- 每股收益: {stock_info.get('每股收益', 'N/A')}
- 净资产收益率: {stock_info.get('净资产收益率', 'N/A')}
- 毛利率: {stock_info.get('毛利率', 'N/A')}
- 净利率: {stock_info.get('净利率', 'N/A')}

### 成长性指标
- 营收增长率: {stock_info.get('营收增长率', 'N/A')}
- 净利润增长率: {stock_info.get('净利润增长率', 'N/A')}

### 财务健康度
- 资产负债率: {stock_info.get('资产负债率', 'N/A')}
- 流动比率: {stock_info.get('流动比率', 'N/A')}
- 速动比率: {stock_info.get('速动比率', 'N/A')}

### 投资建议
基于以上基本面指标，建议投资者：
1. 关注公司的盈利能力和成长性
2. 评估当前估值水平是否合理
3. 分析财务健康状况
4. 结合行业发展趋势做出判断
"""
            
            return report
            
        except Exception as e:
            return f"获取 {ticker} 基本面分析时出错: {str(e)}" 