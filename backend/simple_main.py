#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChinaStockAgents 简化版 FastAPI 后端服务
避免与现有项目依赖冲突的版本
"""
import sys
import os

# 将项目根目录添加到Python路径中，以确保可以找到tradingagents模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
from datetime import datetime
import uvicorn
from contextlib import asynccontextmanager

# ChinaStockAgents 核心库
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
active_connections: List[WebSocket] = []
analysis_tasks: Dict[str, asyncio.Task] = {}

class AnalysisRequest(BaseModel):
    """分析请求模型"""
    ticker: str = Field(..., description="股票代码", example="000001")
    date: str = Field(..., description="分析日期", example="2025-06-21")
    market_type: str = Field(default="china", description="市场类型", example="china")
    selected_analysts: List[str] = Field(
        default=["market", "social", "news", "fundamentals"], 
        description="选择的分析师", 
        example=["social", "news", "fundamentals"]
    )
    research_depth: int = Field(default=1, description="研究深度", example=1)

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
        """添加消息"""
        message_data = {
            "type": "message",
            "sender": sender,
            "content": content,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat()
        }
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

# 全局分析器实例
analyzer = TradingAgentsAnalyzer()

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "ChinaStockAgents API 服务运行中",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/system-info")
async def get_system_info():
    """获取系统信息"""
    features = [
        "多智能体协作分析",
        "实时数据获取",
        "技术面分析",
        "基本面分析",
        "新闻情绪分析",
        "多维度风险评估",
        "智能投资决策"
    ]
    agent_teams = [
        {
            "team_name": "分析师团队",
            "members": [
                {
                    "name": "市场分析师",
                    "role": "技术面分析，价格趋势预测",
                    "description": "作为一名专业的中国股市技术分析师，深入研究股票的技术指标。通过分析移动平均线、MACD、RSI等多种技术图表，识别市场趋势、支撑位和阻力位，为交易决策提供精准的技术层面支持。",
                    "tools": ["技术指标", "价格数据", "成交量分析"]
                },
                {
                    "name": "基本面分析师", 
                    "role": "财务指标分析，估值评估",
                    "description": "作为一名专业的中国股市基本面分析师，全面评估公司的财务健康状况。通过解读财务报表、分析盈利能力、现金流和内幕交易数据，揭示公司的内在价值和长期增长潜力。",
                    "tools": ["财务报表", "财务比率", "估值模型"]
                },
                {
                    "name": "新闻分析师",
                    "role": "政策影响，市场热点分析", 
                    "description": "作为一名专业的中国股市新闻分析师，敏锐捕捉市场动态和宏观经济脉搏。通过分析最新的全球和国内新闻、政策变动和行业趋势，评估其对市场情绪和特定股票的潜在影响。", 
                    "tools": ["新闻数据", "政策解读", "市场情绪"]
                },
                {
                    "name": "社交媒体分析师",
                    "role": "投资者情绪分析",
                    "description": "作为一名专业的社交媒体分析师，专注于挖掘网络舆情和投资者情绪。通过监控主流社交平台和论坛，分析公众对特定公司的讨论热点和情绪倾向，为投资决策提供独特的社会视角。",
                    "tools": ["社交媒体", "情绪分析", "市场热度"]
                },
                {
                    "name": "玄学分析师",
                    "role": "基于中国传统玄学的股票分析",
                    "description": "作为一名精通周易玄学和中国传统文化的分析师，结合五行、八卦、天干地支等理论，对股票走势进行独特的玄学分析，辅助投资决策。",
                    "tools": ["五行理论", "八卦分析", "天干地支", "黄历择时"]
                }
            ]
        },
        {
            "team_name": "研究与交易团队",
            "members": [
                {
                    "name": "多头研究员",
                    "role": "看涨理由和机会分析",
                    "description": "作为一名乐观的多头研究员，致力于发现并论证股票的投资亮点。通过深入分析公司的增长潜力、竞争优势和积极的市场信号，构建强有力的买入理由，并有力地反驳看跌观点。",
                    "tools": ["机会识别", "增长分析", "乐观因素"]
                },
                {
                    "name": "空头研究员",
                    "role": "风险提示和谨慎观点",
                    "description": "作为一名审慎的空头研究员，专注于识别和评估潜在的投资风险。通过深入挖掘公司面临的挑战、财务疑点和市场负面信号，提出有力的卖出或规避理由，并对多头论点进行严格审视。",
                    "tools": ["风险识别", "负面因素", "谨慎分析"]
                },
                {
                    "name": "研究经理",
                    "role": "综合分析和投资建议",
                    "description": "作为一名经验丰富的研究经理，负责协调多头和空头研究员的辩论。在全面评估双方论点后，做出'买入'、'卖出'或'持有'的初步投资建议，并为交易员制定详细的投资计划。",
                    "tools": ["综合分析", "决策支持", "策略制定"]
                },
                {
                    "name": "交易员",
                    "role": "具体交易策略和时机",
                    "description": "作为一名果断的交易员，基于研究经理的投资计划和自身的市场洞察，制定并执行最终的交易策略。在精确的时机进行操作，并对交易结果负责。",
                    "tools": ["交易策略", "时机选择", "仓位管理"]
                }
            ]
        },
        {
            "team_name": "决策与风险管理团队",
            "members": [
                {
                    "name": "激进分析师",
                    "role": "高风险高收益策略",
                    "description": "作为一名激进的风险分析师，勇于拥抱高风险高回报的投资机会。专注于发现并论证那些具有颠覆性潜力但风险较高的策略，挑战保守和中立的观点，追求超额收益。",
                    "tools": ["激进策略", "高风险机会", "杠杆分析"]
                },
                {
                    "name": "中性分析师",
                    "role": "平衡策略分析",
                    "description": "作为一名中立的风险分析师，致力于在风险和回报之间寻求最佳平衡。通过客观评估不同策略的利弊，挑战激进和保守两方的极端观点，提出稳健且具增长潜力的均衡方案。",
                    "tools": ["平衡策略", "风险收益", "中性建议"]
                },
                {
                    "name": "保守分析师",
                    "role": "低风险稳健策略",
                    "description": "作为一名保守的风险分析师，将资本安全置于首位。专注于设计低风险、稳定回报的投资策略，通过严格的风险控制和对市场波动的审慎评估，保护投资组合免受重大损失。",
                    "tools": ["保守策略", "风险控制", "稳健投资"]
                },
                {
                    "name": "投资组合经理",
                    "role": "最终投资决策",
                    "description": "作为最终决策者，主持由激进、中立和保守分析师参与的风险评估辩论。在全面权衡所有观点和潜在风险后，对交易员的计划进行最终审批或调整，做出最终的'买入/卖出/持有'决策。",
                    "tools": ["最终决策", "投资组合", "风险控制"]
                }
            ]
        }
    ]
    data_sources = [
        "AKShare - 中国股票数据",
        "实时价格数据",
        "财务报表数据",
        "新闻数据",
        "技术指标数据"
    ]
    total_agents = sum(len(team["members"]) for team in agent_teams)
    return {
        "system_name": "ChinaStockAgents 中国股市智能体分析系统",
        "version": "1.0.0",
        "description": "基于多智能体大语言模型的金融交易分析框架",
        "features": features,
        "agent_teams": agent_teams,
        "data_sources": data_sources,
        "total_agents": total_agents,
        "data_sources_count": len(data_sources),
        "analysis_features_count": len(features)
    }

@app.post("/api/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest):
    """开始分析"""
    try:
        # 重置分析器状态
        analyzer.agent_status = {k: "pending" for k in analyzer.agent_status.keys()}
        analyzer.messages = []
        analyzer.current_report = None
        analyzer.final_decision = None
        
        # 发送开始消息
        await analyzer.add_message("系统", f"开始分析 {request.ticker} 在 {request.date} 的数据", "info")
        
        # 创建异步任务
        task = asyncio.create_task(
            run_analysis_task(request)
        )
        
        return AnalysisResponse(
            status="started",
            message="分析已开始，请通过WebSocket连接获取实时进度"
        )
        
    except Exception as e:
        logger.error(f"启动分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_analysis_task(request: AnalysisRequest):
    """运行真实的TradingAgents分析任务"""
    try:
        await analyzer.add_message("系统", f"正在初始化分析环境...", "info")
        
        # 1. 设置配置
        config = DEFAULT_CONFIG.copy()
        config["market_type"] = request.market_type
        config["default_ticker"] = request.ticker
        config["max_debate_rounds"] = request.research_depth
        config["online_tools"] = True # 强制使用在线工具
        
        # 可以在这里设置更多的配置，例如LLM provider, keys等
        
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

        # 用于累积最终状态
        final_state = init_state.copy()

        # 4. 流式执行并广播结果
        async for chunk in ta.graph.astream(init_state, **graph_args):
            print("==== RAW CHUNK ==== ")
            print(chunk)
            print("===================")
            node_name = list(chunk.keys())[0]
            state_update = chunk[node_name]

            # 新增：捕获所有 LLM中间产出并流式推送
            agent_name = get_agent_chinese_name(node_name)
            if isinstance(state_update, dict):
                final_state.update(state_update)
            elif isinstance(state_update, list):
                for msg in state_update:
                    await analyzer.add_message(
                        sender=agent_name,
                        content=str(msg),
                        message_type="llm_stream"
                    )
            else:
                await analyzer.add_message(
                    sender=agent_name,
                    content=str(state_update),
                    message_type="llm_stream"
                )

            # 更新状态为 "thinking"
            await analyzer.update_agent_status(agent_name, "thinking", "正在分析...")

            # 模拟思考时间
            await asyncio.sleep(1.5)

            # 提取并广播报告/消息
            if isinstance(state_update, dict):
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
                            sender = msg.split(":")[0] if ":" in msg else agent_name
                            await analyzer.add_message(sender, msg, "discussion")

            # 更新状态为 "completed"
            await analyzer.update_agent_status(agent_name, "completed", "分析完成")

        await analyzer.add_message("系统", "分析流程完成！正在生成最终报告...", "success")

        # 5. 流程结束后，发送完整的最终报告
        try:
            # 从累积的最终状态中提取详细信息
            # 注意：这里的key需要和AgentState中的字段完全对应
            investment_debate = final_state.get("investment_debate_state", {})
            bull_history = investment_debate.get('bull_history', '无相关内容')
            bear_history = investment_debate.get('bear_history', '无相关内容')
            
            final_analysis_payload = {
                "bull_report": bull_history,
                "bear_report": bear_history,
                "investment_plan": final_state.get("investment_plan", "无相关内容"),
                "risk_assessment": final_state.get("risk_debate_state", {}), # 风险评估可能是个复杂对象
                "final_decision": final_state.get("final_trade_decision", "未生成最终决策")
            }
            
            # 广播最终分析报告
            await manager.broadcast(json.dumps({
                "type": "final_analysis",
                "payload": final_analysis_payload
            }, ensure_ascii=False))
            
            await analyzer.add_message("系统", "最终报告已发送至前端。", "success")

        except Exception as e:
            logger.error(f"发送最终报告失败: {e}", exc_info=True)
            await analyzer.add_message("系统", f"发送最终报告时出现错误: {str(e)}", "error")

    except Exception as e:
        logger.error(f"分析任务执行失败: {e}", exc_info=True)
        await analyzer.add_message("系统", f"分析过程中出现严重错误: {str(e)}", "error")

def get_agent_chinese_name(analyst_type: str) -> str:
    """获取分析师中文名称"""
    mapping = {
        "market_analyst": "市场分析师",
        "social_media_analyst": "社交媒体分析师",
        "news_analyst": "新闻分析师",
        "fundamentals_analyst": "基本面分析师",
        "bull_researcher": "多头研究员",
        "bear_researcher": "空头研究员",
        "research_manager": "研究经理",
        "trader": "交易员",
        "risky_debator": "激进分析师",
        "neutral_debator": "中性分析师",
        "safe_debator": "保守分析师",
        "risk_manager": "投资组合经理",
        "metaphysics_analyst": "玄学分析师"
    }
    return mapping.get(analyst_type, analyst_type.replace("_", " ").title())

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
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 