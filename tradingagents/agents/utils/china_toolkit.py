"""
中国股市专用工具包
替换原有的美国股市工具，适配中国股市数据获取和分析
"""

from typing import Annotated, Dict, Any
from langchain_core.tools import tool
from datetime import datetime, timedelta
import pandas as pd
import logging

from tradingagents.dataflows.china_interface import ChinaInterface
from tradingagents.dataflows.akshare_utils import AKShareUtils
from tradingagents.default_config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

class ChinaToolkit:
    """中国股市专用工具包"""
    
    def __init__(self, config=None):
        self.config = config
        self.china_interface = ChinaInterface(config)
    
    @tool
    def get_stock_data(
        self,
        ticker: Annotated[str, "股票代码，如 '000001' 或 '600000'"],
        curr_date: Annotated[str, "当前日期，格式 YYYY-MM-DD"],
        look_back_days: Annotated[int, "回看天数"],
    ) -> str:
        """
        获取中国股票历史价格数据（在线版本）
        
        Args:
            ticker: 股票代码
            curr_date: 当前日期
            look_back_days: 回看天数
            
        Returns:
            str: 格式化的股票数据报告
        """
        try:
            return self.china_interface.get_stock_data(ticker, curr_date, look_back_days)
        except Exception as e:
            return f"获取 {ticker} 股票数据失败: {str(e)}"
    
    @tool
    def get_stock_info(self, ticker: Annotated[str, "股票代码"]) -> str:
        """
        获取中国股票基本信息（在线版本）
        
        Args:
            ticker: 股票代码
            
        Returns:
            str: 股票基本信息报告
        """
        try:
            return self.china_interface.get_stock_info(ticker)
        except Exception as e:
            return f"获取 {ticker} 股票信息失败: {str(e)}"
    
    @tool
    def get_market_overview(self) -> str:
        """
        获取中国股市相关宏观新闻（在线版本）
        
        Returns:
            str: 宏观新闻摘要
        """
        try:
            # 获取市场概况，包含宏观信息
            return self.china_interface.get_market_overview()
        except Exception as e:
            return f"获取宏观新闻失败: {str(e)}"
    
    @tool
    def get_stock_news(
        self,
        ticker: Annotated[str, "股票代码"],
        curr_date: Annotated[str, "当前日期"],
        look_back_days: Annotated[int, "回看天数"],
    ) -> str:
        """
        获取中国股票相关新闻（在线版本）
        
        Args:
            ticker: 股票代码
            curr_date: 当前日期
            look_back_days: 回看天数
            
        Returns:
            str: 新闻摘要报告
        """
        try:
            return self.china_interface.get_stock_news(ticker, curr_date, look_back_days)
        except Exception as e:
            return f"获取 {ticker} 相关新闻失败: {str(e)}"
    
    @tool
    def get_fundamentals_analysis(
        self,
        ticker: Annotated[str, "股票代码"],
        curr_date: Annotated[str, "当前日期"],
    ) -> str:
        """
        获取中国股票基本面分析（在线版本）
        
        Args:
            ticker: 股票代码
            curr_date: 当前日期
            
        Returns:
            str: 基本面分析报告
        """
        try:
            return self.china_interface.get_fundamentals_analysis(ticker, curr_date)
        except Exception as e:
            return f"获取 {ticker} 基本面分析失败: {str(e)}"
    
    @tool
    def get_china_technical_indicators_online(
        ticker: Annotated[str, "股票代码"],
        indicator: Annotated[str, "技术指标类型：MACD, KDJ, RSI, BOLL"],
        curr_date: Annotated[str, "当前日期，格式 YYYY-MM-DD"],
        look_back_days: Annotated[int, "回看天数"] = 30,
    ) -> str:
        """
        获取中国股票技术指标数据（在线版本）
        
        Args:
            ticker: 股票代码
            indicator: 技术指标类型
            curr_date: 当前日期
            look_back_days: 回看天数
            
        Returns:
            str: 技术指标分析报告
        """
        try:
            # 获取股票数据
            stock_data = self.china_interface.get_stock_data(ticker, curr_date, look_back_days)
            
            # 获取技术指标
            tech_data = AKShareUtils.get_technical_indicators(ticker, indicator)
            
            if tech_data.empty:
                return f"无法获取 {ticker} 的 {indicator} 技术指标数据"
            
            # 生成技术指标报告
            report = f"""
## {ticker} {indicator} 技术指标分析报告

### 数据概览
- 分析日期: {curr_date}
- 回看天数: {look_back_days}
- 技术指标: {indicator}

### 技术指标数据
{tech_data.to_string()}

### 分析建议
基于 {indicator} 指标的分析结果，请结合其他技术指标和基本面数据进行综合判断。
"""
            
            return report
            
        except Exception as e:
            return f"获取 {ticker} 技术指标失败: {str(e)}"
    
    @tool
    def get_china_global_news_online(
        curr_date: Annotated[str, "当前日期，格式 YYYY-MM-DD"],
    ) -> str:
        """
        获取中国股市相关宏观新闻（在线版本）
        
        Args:
            curr_date: 当前日期
            
        Returns:
            str: 宏观新闻摘要
        """
        try:
            # 获取市场概况，包含宏观信息
            market_overview = self.china_interface.get_market_overview()
            
            # 添加一些宏观新闻关键词
            keywords = ["政策", "央行", "证监会", "经济", "GDP", "通胀", "利率"]
            news_summary = f"""
## 中国股市宏观新闻摘要 ({curr_date})

### 市场概况
{market_overview}

### 重点关注领域
- 宏观经济政策动向
- 央行货币政策
- 证监会监管政策
- 行业政策变化
- 国际形势影响

### 建议关注关键词
{', '.join(keywords)}
"""
            
            return news_summary
            
        except Exception as e:
            return f"获取宏观新闻失败: {str(e)}"
    
    @tool
    def get_china_financial_statements(
        ticker: Annotated[str, "股票代码"],
        report_type: Annotated[str, "报表类型：资产负债表, 利润表, 现金流量表"],
        curr_date: Annotated[str, "当前日期，格式 YYYY-MM-DD"],
    ) -> str:
        """
        获取中国股票财务报表数据
        
        Args:
            ticker: 股票代码
            report_type: 报表类型
            curr_date: 当前日期
            
        Returns:
            str: 财务报表分析报告
        """
        try:
            financial_data = AKShareUtils.get_financial_data(ticker, report_type)
            
            if financial_data.empty:
                return f"无法获取 {ticker} 的 {report_type} 数据"
            
            # 生成财务报表报告
            report = f"""
## {ticker} {report_type} 分析报告

### 报表概览
- 股票代码: {ticker}
- 报表类型: {report_type}
- 分析日期: {curr_date}

### 财务报表数据
{financial_data.to_string()}

### 关键财务指标分析
请基于以上财务数据，结合行业标准和历史趋势进行综合分析。
"""
            
            return report
            
        except Exception as e:
            return f"获取 {ticker} 财务报表失败: {str(e)}"
    
    @tool
    def get_china_market_sentiment(
        curr_date: Annotated[str, "当前日期，格式 YYYY-MM-DD"],
    ) -> str:
        """
        获取中国股市整体情绪分析
        
        Args:
            curr_date: 当前日期
            
        Returns:
            str: 市场情绪分析报告
        """
        try:
            market_overview = self.china_interface.get_market_overview()
            
            # 添加情绪分析
            sentiment_analysis = f"""
## 中国股市情绪分析报告 ({curr_date})

### 市场概况
{market_overview}

### 情绪指标分析
- 市场热度: 基于成交量和换手率分析
- 投资者信心: 基于涨跌停板数量分析
- 资金流向: 基于北向资金和融资融券数据
- 板块轮动: 基于各板块表现分析

### 情绪评估
请结合以上指标，综合评估当前市场情绪状态。
"""
            
            return sentiment_analysis
            
        except Exception as e:
            return f"获取市场情绪分析失败: {str(e)}"
    
    @tool
    def get_china_industry_analysis(
        ticker: Annotated[str, "股票代码"],
        curr_date: Annotated[str, "当前日期，格式 YYYY-MM-DD"],
    ) -> str:
        """
        获取中国股票所属行业分析（在线版本）
        
        Args:
            ticker: 股票代码
            curr_date: 当前日期
            
        Returns:
            str: 行业分析报告
        """
        try:
            # 获取股票基本信息
            stock_info = self.china_interface.get_stock_info(ticker)
            
            # 获取行业数据
            industry_data = AKShareUtils.get_industry_data(ticker)
            
            report = f"""
## {ticker} 行业分析报告 ({curr_date})

### 股票基本信息
{stock_info}

### 行业数据
{industry_data.to_string() if not industry_data.empty else "暂无行业数据"}

### 行业分析建议
基于行业数据，请结合公司具体情况进行分析。
"""
            
            return report
            
        except Exception as e:
            return f"获取 {ticker} 行业分析失败: {str(e)}"

    @tool
    def get_traditional_calendar_info(
        curr_date: Annotated[str, "当前日期，格式 YYYY-MM-DD"],
    ) -> str:
        """
        获取传统历法信息，包括农历日期、节气、天干地支等
        
        Args:
            curr_date: 当前日期
            
        Returns:
            str: 传统历法信息报告
        """
        try:
            from datetime import datetime
            import calendar
            
            # 解析日期
            date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
            
            # 获取农历信息（简化版本）
            lunar_info = ChinaToolkit._get_lunar_date(date_obj)
            
            # 获取节气信息
            solar_term = ChinaToolkit._get_solar_term(date_obj)
            
            # 获取天干地支
            heavenly_stem, earthly_branch = ChinaToolkit._get_heavenly_stems_earthly_branches(date_obj)
            
            # 获取五行属性
            five_elements = ChinaToolkit._get_five_elements(date_obj)
            
            report = f"""
## 传统历法信息 ({curr_date})

### 农历信息
- 农历日期: {lunar_info['lunar_date']}
- 农历年份: {lunar_info['lunar_year']}
- 生肖: {lunar_info['zodiac']}

### 节气信息
- 当前节气: {solar_term}

### 天干地支
- 天干: {heavenly_stem}
- 地支: {earthly_branch}
- 组合: {heavenly_stem}{earthly_branch}

### 五行属性
- 年五行: {five_elements['year']}
- 月五行: {five_elements['month']}
- 日五行: {five_elements['day']}

### 传统分析建议
基于当前天干地支组合，市场可能呈现以下特征：
- 天干 {heavenly_stem} 代表: {ChinaToolkit._get_stem_meaning(heavenly_stem)}
- 地支 {earthly_branch} 代表: {ChinaToolkit._get_branch_meaning(earthly_branch)}
- 五行 {five_elements['day']} 主导: {ChinaToolkit._get_element_meaning(five_elements['day'])}
"""
            
            return report
            
        except Exception as e:
            return f"获取传统历法信息失败: {str(e)}"

    @staticmethod
    def _get_lunar_date(date_obj):
        """获取农历日期信息（简化版本）"""
        # 这里使用简化的农历计算，实际应用中可以使用专门的农历库
        lunar_months = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]
        lunar_days = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
                     "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
                     "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"]
        
        zodiac_animals = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
        
        # 简化的农历计算（实际应用中需要更精确的算法）
        lunar_month = lunar_months[(date_obj.month - 1) % 12]
        lunar_day = lunar_days[(date_obj.day - 1) % 30]
        lunar_year = date_obj.year
        zodiac = zodiac_animals[(lunar_year - 4) % 12]
        
        return {
            "lunar_date": f"{lunar_month}月{lunar_day}",
            "lunar_year": lunar_year,
            "zodiac": zodiac
        }

    @staticmethod
    def _get_solar_term(date_obj):
        """获取节气信息"""
        solar_terms = [
            "小寒", "大寒", "立春", "雨水", "惊蛰", "春分",
            "清明", "谷雨", "立夏", "小满", "芒种", "夏至",
            "小暑", "大暑", "立秋", "处暑", "白露", "秋分",
            "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"
        ]
        
        # 简化的节气判断（实际应用中需要精确的节气时间）
        month = date_obj.month
        day = date_obj.day
        
        # 根据月份和日期判断节气
        if month == 1 and day >= 5 and day <= 20:
            return "小寒"
        elif month == 1 and day >= 20:
            return "大寒"
        elif month == 2 and day <= 4:
            return "立春"
        elif month == 2 and day >= 18 and day <= 23:
            return "雨水"
        elif month == 3 and day >= 5 and day <= 10:
            return "惊蛰"
        elif month == 3 and day >= 20 and day <= 25:
            return "春分"
        elif month == 4 and day >= 4 and day <= 10:
            return "清明"
        elif month == 4 and day >= 19 and day <= 25:
            return "谷雨"
        elif month == 5 and day >= 5 and day <= 10:
            return "立夏"
        elif month == 5 and day >= 20 and day <= 25:
            return "小满"
        elif month == 6 and day >= 5 and day <= 10:
            return "芒种"
        elif month == 6 and day >= 21 and day <= 25:
            return "夏至"
        elif month == 7 and day >= 6 and day <= 12:
            return "小暑"
        elif month == 7 and day >= 22 and day <= 28:
            return "大暑"
        elif month == 8 and day >= 7 and day <= 13:
            return "立秋"
        elif month == 8 and day >= 22 and day <= 28:
            return "处暑"
        elif month == 9 and day >= 7 and day <= 13:
            return "白露"
        elif month == 9 and day >= 22 and day <= 28:
            return "秋分"
        elif month == 10 and day >= 8 and day <= 14:
            return "寒露"
        elif month == 10 and day >= 23 and day <= 29:
            return "霜降"
        elif month == 11 and day >= 7 and day <= 13:
            return "立冬"
        elif month == 11 and day >= 22 and day <= 28:
            return "小雪"
        elif month == 12 and day >= 6 and day <= 12:
            return "大雪"
        elif month == 12 and day >= 21 and day <= 27:
            return "冬至"
        else:
            return "无特殊节气"

    @staticmethod
    def _get_heavenly_stems_earthly_branches(date_obj):
        """获取天干地支"""
        heavenly_stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        earthly_branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        
        # 简化的天干地支计算
        year_stem = heavenly_stems[(date_obj.year - 4) % 10]
        year_branch = earthly_branches[(date_obj.year - 4) % 12]
        
        return year_stem, year_branch

    @staticmethod
    def _get_five_elements(date_obj):
        """获取五行属性"""
        five_elements = ["木", "火", "土", "金", "水"]
        
        # 简化的五行计算
        year_element = five_elements[(date_obj.year - 4) % 5]
        month_element = five_elements[(date_obj.month - 1) % 5]
        day_element = five_elements[(date_obj.day - 1) % 5]
        
        return {
            "year": year_element,
            "month": month_element,
            "day": day_element
        }

    @staticmethod
    def _get_stem_meaning(stem):
        """获取天干含义"""
        meanings = {
            "甲": "阳木，代表生长、扩张，适合投资成长型股票",
            "乙": "阴木，代表柔韧、适应，适合投资小盘股",
            "丙": "阳火，代表热情、上升，适合投资科技股",
            "丁": "阴火，代表智慧、光明，适合投资消费股",
            "戊": "阳土，代表厚重、稳定，适合投资蓝筹股",
            "己": "阴土，代表包容、承载，适合投资地产股",
            "庚": "阳金，代表收敛、收获，适合投资金融股",
            "辛": "阴金，代表精致、贵重，适合投资贵金属股",
            "壬": "阳水，代表智慧、流动，适合投资科技股",
            "癸": "阴水，代表智慧、灵活，适合投资医药股"
        }
        return meanings.get(stem, "未知")

    @staticmethod
    def _get_branch_meaning(branch):
        """获取地支含义"""
        meanings = {
            "子": "子时，代表开始、新生，适合开仓",
            "丑": "丑时，代表积累、准备，适合观望",
            "寅": "寅时，代表行动、突破，适合积极投资",
            "卯": "卯时，代表成长、发展，适合投资成长股",
            "辰": "辰时，代表稳定、厚重，适合投资蓝筹股",
            "巳": "巳时，代表智慧、变化，适合投资科技股",
            "午": "午时，代表高峰、热情，适合投资热门股",
            "未": "未时，代表收获、满足，适合获利了结",
            "申": "申时，代表收敛、整理，适合谨慎投资",
            "酉": "酉时，代表收获、完成，适合平仓",
            "戌": "戌时，代表守护、防御，适合投资防御股",
            "亥": "亥时，代表智慧、内敛，适合投资价值股"
        }
        return meanings.get(branch, "未知")

    @staticmethod
    def _get_element_meaning(element):
        """获取五行含义"""
        meanings = {
            "木": "代表生长、扩张，适合投资成长型、环保类股票",
            "火": "代表热情、上升，适合投资科技、能源、消费类股票",
            "土": "代表稳定、厚重，适合投资地产、基建、农业类股票",
            "金": "代表收敛、收获，适合投资金融、贵金属、机械类股票",
            "水": "代表智慧、流动，适合投资科技、医药、物流类股票"
        }
        return meanings.get(element, "未知")

# 创建工具包实例
china_toolkit = ChinaToolkit() 