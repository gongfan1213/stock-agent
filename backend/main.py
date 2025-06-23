#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChinaStockAgents FastAPI 后端服务
生产级别的中国股市智能体分析系统
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
from datetime import datetime
import uvicorn
from contextlib import asynccontextmanager
import random

# 导入TradingAgents相关模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.analysis_visualizer import AnalysisVisualizer, AnalysisStep, ToolCall, LLMInteraction
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.dataflows.config import set_config
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.china_interface import ChinaInterface

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
active_connections: List[WebSocket] = []
analysis_tasks: Dict[str, asyncio.Task] = {}
analysis_reports: Dict[str, Dict[str, Any]] = {}

class AnalysisRequest(BaseModel):
    """分析请求模型"""
    ticker: str = Field(..., description="股票代码", example="000001")
    date: str = Field(..., description="分析日期", example="2025-01-21")
    market_type: str = Field(default="china", description="市场类型", example="china")
    selected_analysts: List[str] = Field(
        default=["social"], 
        description="选择的分析师", 
        example=["social", "news", "fundamentals", "market"]
    )
    research_depth: int = Field(default=1, description="研究深度", example=1)
    look_back_days: int = Field(default=30, description="回看天数", example=30)

class AnalysisResponse(BaseModel):
    """分析响应模型"""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

class AgentStatus(BaseModel):
    """智能体状态模型"""
    agent_name: str
    status: str  # "pending", "thinking", "completed", "error"
    progress: float = 0.0
    message: str = ""

class AnalysisProgress(BaseModel):
    """分析进度模型"""
    task_id: str
    status: str
    agents: List[AgentStatus]
    messages: List[Dict[str, Any]]
    current_report: Optional[str] = None
    final_decision: Optional[str] = None

class StockInfoRequest(BaseModel):
    """股票信息请求模型"""
    ticker: str = Field(..., description="股票代码", example="000001")

class MarketOverviewResponse(BaseModel):
    """市场概况响应模型"""
    status: str
    data: Dict[str, Any]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("启动TradingAgents FastAPI服务...")
    yield
    logger.info("关闭TradingAgents FastAPI服务...")

# 创建FastAPI应用
app = FastAPI(
    title="ChinaStockAgents API",
    description="中国股市智能体分析系统API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"新的WebSocket连接，当前连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket连接断开，当前连接数: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """广播消息给所有连接的客户端"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

class TradingAgentsAnalyzer:
    """TradingAgents分析器"""
    
    def __init__(self):
        self.config = DEFAULT_CONFIG
        self.config["market_type"] = "china"
        set_config(self.config)
        self.visualizer = AnalysisVisualizer()
        
        # 添加缺失的属性
        self.agent_status = {
            "市场分析师": "pending",
            "社交媒体分析师": "pending", 
            "新闻分析师": "pending",
            "基本面分析师": "pending",
            "多头研究员": "pending",
            "空头研究员": "pending",
            "研究经理": "pending",
            "交易员": "pending",
            "激进分析师": "pending",
            "中性分析师": "pending",
            "保守分析师": "pending",
            "投资组合经理": "pending",
        }
        self.messages = []
        self.current_report = None
        self.final_decision = None
        
        # Pass the visualizer to the graph
        self.graph = TradingAgentsGraph(
            selected_analysts=["market", "social", "news", "fundamentals", "metaphysics"],
            config=self.config,
            visualizer=self.visualizer
        )
        # Assuming ChinaInterface provides necessary stock data functions
        self.data_interface = ChinaInterface(self.config)

    @staticmethod
    def is_long_english(text, min_length=300):
        import re
        if not text:
            return False
        # 只包含英文字符和常见标点，且长度大于 min_length
        english_chars = re.sub(r'[\x00-\x7F\s.,;:?!\'"()\[\]{}-]', '', text)
        return len(english_chars) < 0.05 * len(text) and len(text) > min_length

    async def update_agent_status(self, agent: str, status: str, message: str = ""):
        """更新智能体状态"""
        self.agent_status[agent] = status
        status_data = {
            "type": "agent_status",
            "agent": agent,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(json.dumps(status_data, ensure_ascii=False))
    
    async def add_message(self, sender: str, content: str, message_type: str = "info"):
        """添加消息，自动分离大段英文内容"""
        message_data = {
            "type": "message",
            "sender": sender,
            "content": content,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat()
        }
        # 检查是否为大段英文
        if self.is_long_english(content):
            message_data["english_content"] = content
            message_data["content"] = ""  # 其他地方不再显示英文大段
        self.messages.append(message_data)
        await manager.broadcast(json.dumps(message_data, ensure_ascii=False))
    
    async def update_report(self, report_type: str, content: str):
        """更新报告"""
        self.current_report = content
        report_data = {
            "type": "report_update",
            "report_type": report_type,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(json.dumps(report_data, ensure_ascii=False))
    
    async def set_final_decision(self, decision: str):
        """设置最终决策"""
        self.final_decision = decision
        decision_data = {
            "type": "final_decision",
            "decision": decision,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(json.dumps(decision_data, ensure_ascii=False))

    def initialize_graph(self, selected_analysts: List[str]) -> bool:
        """初始化分析图"""
        try:
            # 新增：分析师简写到全名的映射
            ANALYST_MAP = {
                "market": "market_analyst",
                "social": "social_media_analyst",
                "news": "news_analyst",
                "fundamentals": "fundamentals_analyst",
                "metaphysics": "metaphysics_analyst",
                "bull": "bull_researcher",
                "bear": "bear_researcher",
                "manager": "research_manager",
                "trader": "trader",
                "aggressive": "aggressive_debator",
                "neutral": "neutral_debator",
                "conservative": "conservative_debator",
                "portfolio": "investment_manager"
            }
            selected_analysts_full = [ANALYST_MAP.get(a, a) for a in selected_analysts]
            self.graph = TradingAgentsGraph(
                selected_analysts=selected_analysts_full,
                config=self.config,
                visualizer=self.visualizer
            )
            return True
        except Exception as e:
            logger.error(f"初始化分析图失败: {e}")
            return False

    async def run_analysis_task(self, websocket: WebSocket, company_name: str):
        """
        Runs the full, real-time analysis using TradingAgentsGraph and streams updates.
        """
        self.visualizer.start_analysis(company_name)
        self.visualizer.set_ws_callback(lambda msg: websocket.send_text(msg))  # 设置日志推送

        async def broadcast_update():
            """Callback function to send updates over WebSocket."""
            visualization_data = self.visualizer.to_dict() if hasattr(self.visualizer, 'to_dict') else {}
            await websocket.send_text(json.dumps(visualization_data))

        try:
            # Broadcast the initial "started" state
            await broadcast_update()

            trade_date = datetime.now().strftime("%Y-%m-%d")

            # Run the actual graph propagation with the callback
            final_state, final_decision = await self.graph.propagate(
                company_name=company_name,
                trade_date=trade_date,
                async_callback=broadcast_update
            )
            
            self.visualizer.finish_analysis(final_decision, final_state)

        except Exception as e:
            # Ensure the analysis is marked as finished even if an error occurs
            self.visualizer.finish_analysis(f"Error: {e}", {})
            print(f"An error occurred during analysis: {e}")
        finally:
            # Send the final state
            await broadcast_update()

# 全局分析器实例
analyzer = TradingAgentsAnalyzer()

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "ChinaStockAgents 中国股市智能体分析系统API服务运行中",
        "version": "1.0.0",
        "status": "running",
        "market_type": "china"
    }

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/system-info")
async def get_system_info():
    """获取系统信息，包括智能体团队"""
    agent_team = [
        {"name": "市场分析师", "role": "技术面分析, 价格趋势预测", "description": "通过分析历史价格图表、交易量和技术指标，预测未来市场走势，为交易决策提供技术支持。", "icon": "BarChartOutlined"},
        {"name": "基本面分析师", "role": "财务指标分析, 估值评估", "description": "深入研究公司的财务报表、行业地位和宏观经济因素，评估股票的内在价值，发现投资机会。", "icon": "InfoCircleOutlined"},
        {"name": "新闻分析师", "role": "政策影响, 市场热点分析", "description": "实时监控全球新闻、政策动态和市场情绪，分析突发事件对市场的影响，抓住交易时机。", "icon": "RocketOutlined"},
        {"name": "社交媒体分析师", "role": "投资者情绪分析", "description": "分析社交媒体平台上的讨论和情绪，洞察散户投资者的情绪变化，为交易决策提供参考。", "icon": "TeamOutlined"},
        {"name": "玄学分析师", "role": "传统历法, 神秘因素分析", "description": "运用东方传统历法、节气、天干地支等玄学理论，从独特的角度分析市场波动，提供另类投资视角。", "icon": "TrophyOutlined"},
        {"name": "多头研究员", "role": "发现增长机会", "description": "专注于寻找具有增长潜力的投资标的，通过深入研究和分析，为看涨决策提供支持。", "icon": "CheckCircleOutlined"},
        {"name": "空头研究员", "role": "识别潜在风险", "description": "致力于发现被高估或存在风险的投资标的，通过严谨的分析，为看跌决策提供依据。", "icon": "ExclamationCircleOutlined"},
        {"name": "研究经理", "role": "综合研究, 形成观点", "description": "负责协调多头和空头研究员的工作，综合各方观点，形成全面、客观的投资研究报告。", "icon": "SettingOutlined"},
        {"name": "交易员", "role": "执行交易, 管理仓位", "description": "根据研究报告和市场情况，制定并执行交易策略，负责具体的买入和卖出操作，并管理投资组合的风险。", "icon": "BarChartOutlined"},
        {"name": "激进辩手", "role": "挑战观点, 追求高收益", "description": "在投资决策辩论中扮演激进角色，倾向于高风险高回报的策略，挑战现有观点，激发深入思考。", "icon": "RocketOutlined"},
        {"name": "中立辩手", "role": "客观评估, 平衡风险", "description": "在投资决策辩论中保持中立，客观评估各种策略的利弊，寻求风险与收益的最佳平衡。", "icon": "ClockCircleOutlined"},
        {"name": "保守辩手", "role": "强调风险, 稳健投资", "description": "在投资决策辩论中代表保守立场，强调风险控制和资本保值，提倡稳健的投资策略。", "icon": "CheckCircleOutlined"},
        {"name": "投资经理", "role": "最终决策", "description": "综合所有分析和辩论结果，做出最终的投资决策，对投资组合的整体表现负责。", "icon": "SettingOutlined"},
        {"name": "风险经理", "role": "评估和管理风险", "description": "负责评估和管理整个投资过程中的风险，确保投资策略符合风险控制要求。", "icon": "SettingOutlined"},
    ]
    system_info = {
        "system_name": "ChinaStockAgents 中国股市智能体分析系统",
        "version": "1.0.0",
        "description": "基于多智能体大语言模型的金融交易分析框架",
        "total_agents": len(agent_team),
        "data_sources_count": 5,
        "analysis_features_count": 7,
        "agent_team": agent_team
    }
    return system_info

@app.post("/api/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest):
    """开始分析"""
    try:
        # 重置分析器状态
        analyzer.agent_status = {k: "pending" for k in analyzer.agent_status.keys()}
        analyzer.messages = []
        analyzer.current_report = None
        analyzer.final_decision = None
        
        # 初始化分析图
        if not analyzer.initialize_graph(request.selected_analysts):
            raise HTTPException(status_code=500, detail="初始化分析图失败")
        
        # 发送开始消息
        await analyzer.add_message("系统", f"开始分析 {request.ticker} 在 {request.date} 的数据", "info")
        
        # 创建异步任务 - 修复函数调用
        # 注意：这里需要传入WebSocket连接，但在这个上下文中没有WebSocket
        # 我们需要修改run_analysis_task函数或者创建一个新的任务函数
        task = asyncio.create_task(
            run_analysis_task_simple(request)
        )
        
        return AnalysisResponse(
            status="started",
            message="分析已开始，请通过WebSocket连接获取实时进度"
        )
        
    except Exception as e:
        logger.error(f"启动分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_analysis_task_simple(request: AnalysisRequest):
    """简化的分析任务，不依赖WebSocket"""
    try:
        await analyzer.add_message("系统", f"正在初始化分析环境...", "info")
        
        # 1. 设置配置
        config = DEFAULT_CONFIG.copy()
        config["market_type"] = request.market_type
        config["default_ticker"] = request.ticker
        config["max_debate_rounds"] = request.research_depth
        config["online_tools"] = True # 强制使用在线工具
        
        await analyzer.add_message("系统", f"配置加载完成，使用模型: {config['deep_think_llm']}", "info")
        
        # 2. 初始化 TradingAgentsGraph
        ta = TradingAgentsGraph(
            debug=True, 
            config=config,
            selected_analysts=request.selected_analysts
        )
        
        await analyzer.add_message("系统", "智能体图谱初始化完成", "info")
        
        # 3. 准备运行参数
        init_state = ta.propagator.create_initial_state(request.ticker, request.date)
        graph_args = ta.propagator.get_graph_args()

        # 4. 流式执行并广播结果
        async for chunk in ta.graph.astream(init_state, **graph_args):
            print("==== RAW CHUNK ==== ")
            print(chunk)
            print("===================")
            # chunk 的格式是 {node_name: state_update}
            node_name = list(chunk.keys())[0]
            state_update = chunk[node_name]
            
            agent_name = get_agent_chinese_name(node_name)
            
            # 更新状态为 "thinking"
            await analyzer.update_agent_status(agent_name, "thinking", "正在分析...")

            # 模拟思考时间
            await asyncio.sleep(1.5)

            # 提取并广播报告/消息
            if "market_report" in state_update and state_update["market_report"]:
                await analyzer.update_report("市场分析报告", state_update["market_report"])
                await analyzer.add_message(agent_name, "市场分析报告已生成。", "analysis")
            elif "fundamentals_report" in state_update and state_update["fundamentals_report"]:
                await analyzer.update_report("基本面分析报告", state_update["fundamentals_report"])
                await analyzer.add_message(agent_name, "基本面分析报告已生成。", "analysis")
            elif "news_report" in state_update and state_update["news_report"]:
                await analyzer.update_report("新闻分析报告", state_update["news_report"])
                await analyzer.add_message(agent_name, "新闻分析报告已生成。", "analysis")
            elif "sentiment_report" in state_update and state_update["sentiment_report"]:
                await analyzer.update_report("社交媒体情绪报告", state_update["sentiment_report"])
                await analyzer.add_message(agent_name, "社交媒体情绪报告已生成。", "analysis")
            elif "investment_plan" in state_update and state_update["investment_plan"]:
                await analyzer.update_report("初步投资计划", state_update["investment_plan"])
                await analyzer.add_message(agent_name, "已生成初步投资计划。", "discussion")
            elif "final_trade_decision" in state_update and state_update["final_trade_decision"]:
                await analyzer.set_final_decision(state_update["final_trade_decision"])
                await analyzer.add_message(agent_name, "已生成最终交易决策。", "decision")

            # 提取并广播辩论消息
            if "investment_debate_state" in state_update:
                if "current_response" in state_update["investment_debate_state"]:
                    msg = state_update["investment_debate_state"]["current_response"]
                    if msg:
                        # 从消息中解析出说话人
                        sender = msg.split(":")[0] if ":" in msg else agent_name
                        await analyzer.add_message(sender, msg, "discussion")

            # 更新状态为 "completed"
            await analyzer.update_agent_status(agent_name, "completed", "分析完成")

        await analyzer.add_message("系统", "分析流程完成！", "success")

    except Exception as e:
        logger.error(f"分析任务执行失败: {e}", exc_info=True)
        await analyzer.add_message("系统", f"分析过程中出现严重错误: {str(e)}", "error")

def get_agent_chinese_name(analyst_type: str) -> str:
    """获取智能体的中文名称"""
    name_mapping = {
        "market_analyst": "市场分析师",
        "social_media_analyst": "社交媒体分析师",
        "news_analyst": "新闻分析师",
        "fundamentals_analyst": "基本面分析师",
        "bull_researcher": "多头研究员",
        "bear_researcher": "空头研究员",
        "research_manager": "研究经理",
        "trader": "交易员",
        "aggressive_debator": "激进分析师",
        "neutral_debator": "中性分析师",
        "conservative_debator": "保守分析师",
        "investment_manager": "投资组合经理",
    }
    return name_mapping.get(analyst_type, analyst_type)

@app.get("/api/analysis-report/{analysis_id}")
async def get_analysis_report(analysis_id: str):
    """获取完整的分析报告详情"""
    report = analysis_reports.get(analysis_id)
    if not report:
        raise HTTPException(status_code=404, detail="找不到指定的分析报告")
    return report

@app.get("/api/stock-info/{ticker}")
async def get_stock_info(ticker: str):
    """获取股票基本信息"""
    try:
        stock_info = await analyzer.china_toolkit.get_china_stock_info(ticker)
        return {
            "status": "success",
            "ticker": ticker,
            "data": stock_info
        }
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-overview")
async def get_market_overview():
    """获取市场概况"""
    try:
        market_data = await analyzer.china_toolkit.get_china_market_overview()
        return MarketOverviewResponse(
            status="success",
            data={"overview": market_data}
        )
    except Exception as e:
        logger.error(f"获取市场概况失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock-data/{ticker}")
async def get_stock_data(ticker: str, date: str, look_back_days: int = 30):
    """获取股票历史数据"""
    try:
        stock_data = await analyzer.china_toolkit.get_china_stock_data(ticker, date, look_back_days)
        return {
            "status": "success",
            "ticker": ticker,
            "date": date,
            "look_back_days": look_back_days,
            "data": stock_data
        }
    except Exception as e:
        logger.error(f"获取股票数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock-news/{ticker}")
async def get_stock_news(ticker: str, date: str, look_back_days: int = 7):
    """获取股票相关新闻"""
    try:
        news_data = await analyzer.china_toolkit.get_china_stock_news(ticker, date, look_back_days)
        return {
            "status": "success",
            "ticker": ticker,
            "date": date,
            "look_back_days": look_back_days,
            "data": news_data
        }
    except Exception as e:
        logger.error(f"获取股票新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fundamentals/{ticker}")
async def get_fundamentals_analysis(ticker: str, date: str):
    """获取基本面分析"""
    try:
        fundamentals = await analyzer.china_toolkit.get_china_fundamentals_analysis(ticker, date)
        return {
            "status": "success",
            "ticker": ticker,
            "date": date,
            "data": fundamentals
        }
    except Exception as e:
        logger.error(f"获取基本面分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await manager.connect(websocket)
    try:
        # 发送连接确认
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "message": "WebSocket连接已建立",
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False),
            websocket
        )
        
        # 保持连接
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息（如果需要）
            logger.info(f"收到客户端消息: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 