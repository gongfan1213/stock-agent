"""
中国股票数据获取工具 - 基于 AKShare
AKShare 是一个完全免费的金融数据接口包
"""

import akshare as ak
import pandas as pd
from typing import Annotated, Optional, Dict, Any
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class AKShareUtils:
    """中国股票数据获取工具类"""
    
    @staticmethod
    def get_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取股票历史价格数据"""
        try:
            if '.' not in symbol:
                if symbol.startswith('6'):
                    symbol = f"{symbol}.SH"
                else:
                    symbol = f"{symbol}.SZ"
            
            stock_data = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            column_mapping = {
                '日期': 'Date',
                '开盘': 'Open',
                '收盘': 'Close',
                '最高': 'High',
                '最低': 'Low',
                '成交量': 'Volume'
            }
            
            stock_data = stock_data.rename(columns=column_mapping)
            stock_data['Date'] = pd.to_datetime(stock_data['Date'])
            stock_data = stock_data.set_index('Date')
            
            return stock_data
            
        except Exception as e:
            print(f"获取股票数据失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_info(symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        try:
            if '.' not in symbol:
                if symbol.startswith('6'):
                    symbol = f"{symbol}.SH"
                else:
                    symbol = f"{symbol}.SZ"
            
            stock_info = ak.stock_individual_info_em(symbol=symbol)
            info_dict = {}
            for _, row in stock_info.iterrows():
                info_dict[row.iloc[0]] = row.iloc[1]
            
            return info_dict
            
        except Exception as e:
            print(f"获取股票信息失败: {e}")
            return {}
    
    @staticmethod
    def get_financial_data(
        symbol: str,
        report_type: str = "资产负债表"
    ) -> pd.DataFrame:
        """
        获取财务报表数据
        
        Args:
            symbol: 股票代码
            report_type: 报表类型 ("资产负债表", "利润表", "现金流量表")
            
        Returns:
            DataFrame: 财务报表数据
        """
        try:
            # 处理股票代码格式
            if '.' not in symbol:
                if symbol.startswith('6'):
                    symbol = f"{symbol}.SH"
                else:
                    symbol = f"{symbol}.SZ"
            
            if report_type == "资产负债表":
                return ak.stock_balance_sheet_by_report_em(symbol=symbol)
            elif report_type == "利润表":
                return ak.stock_profit_sheet_by_report_em(symbol=symbol)
            elif report_type == "现金流量表":
                return ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
            else:
                raise ValueError(f"不支持的报表类型: {report_type}")
                
        except Exception as e:
            print(f"获取财务报表失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_news_data(
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取股票相关新闻
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 新闻数据
        """
        try:
            # 获取股票名称
            stock_info = ak.stock_individual_info_em(symbol=symbol)
            stock_name = stock_info.iloc[0, 1] if not stock_info.empty else symbol
            
            # 获取新闻数据（这里使用东方财富的新闻接口）
            news_data = ak.stock_news_em(symbol=symbol)
            
            # 过滤日期范围
            news_data['发布时间'] = pd.to_datetime(news_data['发布时间'])
            mask = (news_data['发布时间'] >= start_date) & (news_data['发布时间'] <= end_date)
            filtered_news = news_data.loc[mask]
            
            return filtered_news
            
        except Exception as e:
            print(f"获取新闻数据失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_market_data() -> pd.DataFrame:
        """
        获取市场整体数据（上证指数、深证成指等）
        
        Returns:
            DataFrame: 市场数据
        """
        try:
            # 获取主要指数数据
            indices = {
                '上证指数': '000001',
                '深证成指': '399001',
                '创业板指': '399006',
                '沪深300': '000300'
            }
            
            market_data = {}
            for name, code in indices.items():
                try:
                    data = ak.stock_zh_index_daily(symbol=code)
                    market_data[name] = data
                except:
                    continue
            
            return market_data
            
        except Exception as e:
            print(f"获取市场数据失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_technical_indicators(
        symbol: str,
        indicator: str = "MACD"
    ) -> pd.DataFrame:
        """
        获取技术指标数据
        
        Args:
            symbol: 股票代码
            indicator: 技术指标类型 ("MACD", "KDJ", "RSI", "BOLL")
            
        Returns:
            DataFrame: 技术指标数据
        """
        try:
            # 处理股票代码格式
            if '.' not in symbol:
                if symbol.startswith('6'):
                    symbol = f"{symbol}.SH"
                else:
                    symbol = f"{symbol}.SZ"
            
            if indicator == "MACD":
                return ak.stock_macd(symbol=symbol)
            elif indicator == "KDJ":
                return ak.stock_kdj(symbol=symbol)
            elif indicator == "RSI":
                return ak.stock_rsi(symbol=symbol)
            elif indicator == "BOLL":
                return ak.stock_bollinger_bands(symbol=symbol)
            else:
                raise ValueError(f"不支持的技术指标: {indicator}")
                
        except Exception as e:
            print(f"获取技术指标失败: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_industry_data(symbol: str) -> pd.DataFrame:
        """
        获取行业数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            DataFrame: 行业数据
        """
        try:
            # 处理股票代码格式
            if '.' not in symbol:
                if symbol.startswith('6'):
                    symbol = f"{symbol}.SH"
                else:
                    symbol = f"{symbol}.SZ"
            
            # 获取股票所属行业信息
            stock_info = ak.stock_individual_info_em(symbol=symbol)
            
            # 提取行业信息
            industry_info = {}
            for _, row in stock_info.iterrows():
                if '所属行业' in str(row.iloc[0]):
                    industry_info['所属行业'] = row.iloc[1]
                elif '行业' in str(row.iloc[0]):
                    industry_info['行业'] = row.iloc[1]
            
            # 转换为DataFrame
            if industry_info:
                return pd.DataFrame([industry_info])
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"获取行业数据失败: {e}")
            return pd.DataFrame()

# 创建全局实例
akshare_utils = AKShareUtils() 