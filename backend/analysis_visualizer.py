#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析流程可视化模块
详细记录每个分析步骤的工具调用、消息传递、LLM交互和结论生成
"""

import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class StepType(Enum):
    """分析步骤类型"""
    TOOL_CALL = "tool_call"
    LLM_INTERACTION = "llm_interaction"
    MESSAGE_SEND = "message_send"
    MESSAGE_RECEIVE = "message_receive"
    REPORT_GENERATION = "report_generation"
    DECISION_MAKING = "decision_making"
    DATA_PROCESSING = "data_processing"
    AGENT_COLLABORATION = "agent_collaboration"

class AgentType(Enum):
    """智能体类型"""
    MARKET_ANALYST = "市场分析师"
    FUNDAMENTAL_ANALYST = "基本面分析师"
    NEWS_ANALYST = "新闻分析师"
    SOCIAL_ANALYST = "社交媒体分析师"
    BULL_RESEARCHER = "多头研究员"
    BEAR_RESEARCHER = "空头研究员"
    RESEARCH_MANAGER = "研究经理"
    TRADER = "交易员"
    AGGRESSIVE_DEBATOR = "激进分析师"
    NEUTRAL_DEBATOR = "中性分析师"
    CONSERVATIVE_DEBATOR = "保守分析师"
    PORTFOLIO_MANAGER = "投资组合经理"

@dataclass
class ToolCall:
    """工具调用记录"""
    tool_name: str
    parameters: Dict[str, Any]
    start_time: float
    end_time: float
    duration: float
    success: bool
    result: str
    error_message: Optional[str] = None
    data_size: Optional[int] = None
    api_calls: Optional[int] = None

@dataclass
class LLMInteraction:
    """LLM交互记录"""
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    start_time: float
    end_time: float
    duration: float
    prompt: str
    response: str
    temperature: float
    max_tokens: int
    success: bool
    error_message: Optional[str] = None

@dataclass
class Message:
    """消息记录"""
    sender: str
    receiver: str
    message_type: str
    content: str
    timestamp: float
    message_id: str
    priority: str = "normal"
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AnalysisStep:
    """分析步骤记录"""
    step_id: str
    step_type: StepType
    agent: AgentType
    step_name: str
    start_time: float
    end_time: float
    duration: float
    description: str
    tool_calls: List[ToolCall]
    llm_interactions: List[LLMInteraction]
    messages: List[Message]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    conclusions: List[str]
    confidence_score: float
    metadata: Dict[str, Any]

@dataclass
class AnalysisReport:
    """分析报告记录"""
    report_id: str
    ticker: str
    analysis_date: str
    start_time: float
    end_time: float
    total_duration: float
    steps: List[AnalysisStep]
    final_decision: str
    confidence_score: float
    risk_assessment: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    summary: str

class AnalysisVisualizer:
    """分析流程可视化器"""
    
    def __init__(self):
        self.current_analysis: Optional[AnalysisReport] = None
        self.step_counter = 0
        self.tool_call_counter = 0
        self.llm_interaction_counter = 0
        self.message_counter = 0
        self.logs: List[Dict[str, Any]] = []  # 新增日志流
        self.ws_callback = None  # WebSocket推送回调
        
    def set_ws_callback(self, callback):
        """设置WebSocket推送回调"""
        self.ws_callback = callback

    def add_log(self, agent: str, event: str, detail: str, status: str = "info", extra: Optional[Dict[str, Any]] = None):
        """添加详细日志并推送到前端"""
        log = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "agent": agent,
            "event": event,
            "detail": detail,
            "status": status,
        }
        if extra:
            log.update(extra)
        self.logs.append(log)
        if self.ws_callback:
            try:
                asyncio.create_task(self.ws_callback(json.dumps({"type": "log", "data": log})))
            except Exception as e:
                logger.error(f"WebSocket日志推送失败: {e}")

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.logs
    
    def start_analysis(self, ticker: str, analysis_date: str) -> str:
        """开始新的分析"""
        analysis_id = str(uuid.uuid4())
        self.current_analysis = AnalysisReport(
            report_id=analysis_id,
            ticker=ticker,
            analysis_date=analysis_date,
            start_time=time.time(),
            end_time=0,
            total_duration=0,
            steps=[],
            final_decision="",
            confidence_score=0.0,
            risk_assessment={},
            performance_metrics={},
            summary=""
        )
        logger.info(f"开始分析 {ticker} 在 {analysis_date} 的数据")
        return analysis_id
    
    def add_step(self, 
                 step_type: StepType,
                 agent: AgentType,
                 step_name: str,
                 description: str) -> str:
        """添加分析步骤"""
        if not self.current_analysis:
            raise ValueError("没有正在进行的分析")
        
        step_id = f"step_{self.step_counter:04d}"
        self.step_counter += 1
        
        step = AnalysisStep(
            step_id=step_id,
            step_type=step_type,
            agent=agent,
            step_name=step_name,
            start_time=time.time(),
            end_time=0,
            duration=0,
            description=description,
            tool_calls=[],
            llm_interactions=[],
            messages=[],
            input_data={},
            output_data={},
            conclusions=[],
            confidence_score=0.0,
            metadata={}
        )
        
        self.current_analysis.steps.append(step)
        logger.info(f"添加步骤: {step_name} - {agent.value}")
        return step_id
    
    def record_tool_call(self, 
                        step_id: str,
                        tool_name: str,
                        parameters: Dict[str, Any],
                        result: str,
                        success: bool = True,
                        error_message: Optional[str] = None) -> str:
        """记录工具调用"""
        if not self.current_analysis:
            raise ValueError("没有正在进行的分析")
        
        step = self._find_step(step_id)
        if not step:
            raise ValueError(f"找不到步骤: {step_id}")
        
        tool_call_id = f"tool_{self.tool_call_counter:04d}"
        self.tool_call_counter += 1
        
        start_time = time.time() - 0.1  # 模拟调用时间
        end_time = time.time()
        duration = end_time - start_time
        
        tool_call = ToolCall(
            tool_name=tool_name,
            parameters=parameters,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success=success,
            result=result,
            error_message=error_message,
            data_size=len(result) if result else 0,
            api_calls=1
        )
        
        step.tool_calls.append(tool_call)
        logger.info(f"工具调用: {tool_name} - {'成功' if success else '失败'}")
        return tool_call_id
    
    def record_llm_interaction(self,
                              step_id: str,
                              model_name: str,
                              prompt: str,
                              response: str,
                              prompt_tokens: int,
                              completion_tokens: int,
                              temperature: float = 0.7,
                              max_tokens: int = 2000,
                              success: bool = True,
                              error_message: Optional[str] = None) -> str:
        """记录LLM交互"""
        if not self.current_analysis:
            raise ValueError("没有正在进行的分析")
        
        step = self._find_step(step_id)
        if not step:
            raise ValueError(f"找不到步骤: {step_id}")
        
        interaction_id = f"llm_{self.llm_interaction_counter:04d}"
        self.llm_interaction_counter += 1
        
        start_time = time.time() - 0.5  # 模拟交互时间
        end_time = time.time()
        duration = end_time - start_time
        
        llm_interaction = LLMInteraction(
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            prompt=prompt,
            response=response,
            temperature=temperature,
            max_tokens=max_tokens,
            success=success,
            error_message=error_message
        )
        
        step.llm_interactions.append(llm_interaction)
        logger.info(f"LLM交互: {model_name} - {prompt_tokens + completion_tokens} tokens")
        return interaction_id
    
    def record_message(self,
                      step_id: str,
                      sender: str,
                      receiver: str,
                      message_type: str,
                      content: str,
                      priority: str = "normal",
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """记录消息"""
        if not self.current_analysis:
            raise ValueError("没有正在进行的分析")
        
        step = self._find_step(step_id)
        if not step:
            raise ValueError(f"找不到步骤: {step_id}")
        
        message_id = f"msg_{self.message_counter:04d}"
        self.message_counter += 1
        
        message = Message(
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            content=content,
            timestamp=time.time(),
            message_id=message_id,
            priority=priority,
            metadata=metadata or {}
        )
        
        step.messages.append(message)
        logger.info(f"消息: {sender} -> {receiver} ({message_type})")
        return message_id
    
    def update_step_data(self,
                        step_id: str,
                        input_data: Optional[Dict[str, Any]] = None,
                        output_data: Optional[Dict[str, Any]] = None,
                        conclusions: Optional[List[str]] = None,
                        confidence_score: Optional[float] = None,
                        metadata: Optional[Dict[str, Any]] = None):
        """更新步骤数据"""
        if not self.current_analysis:
            raise ValueError("没有正在进行的分析")
        
        step = self._find_step(step_id)
        if not step:
            raise ValueError(f"找不到步骤: {step_id}")
        
        step.end_time = time.time()
        step.duration = step.end_time - step.start_time
        
        if input_data:
            step.input_data.update(input_data)
        if output_data:
            step.output_data.update(output_data)
        if conclusions:
            step.conclusions.extend(conclusions)
        if confidence_score is not None:
            step.confidence_score = confidence_score
        if metadata:
            step.metadata.update(metadata)
    
    def end_analysis(self, 
                    final_decision: str,
                    confidence_score: float,
                    risk_assessment: Dict[str, Any],
                    summary: str):
        """结束分析"""
        if not self.current_analysis:
            raise ValueError("没有正在进行的分析")
        
        self.current_analysis.end_time = time.time()
        self.current_analysis.total_duration = self.current_analysis.end_time - self.current_analysis.start_time
        self.current_analysis.final_decision = final_decision
        self.current_analysis.confidence_score = confidence_score
        self.current_analysis.risk_assessment = risk_assessment
        self.current_analysis.summary = summary
        
        # 计算性能指标
        self.current_analysis.performance_metrics = self._calculate_performance_metrics()
        
        logger.info(f"分析完成: {self.current_analysis.ticker} - 决策: {final_decision}")
    
    def _find_step(self, step_id: str) -> Optional[AnalysisStep]:
        """查找步骤"""
        for step in self.current_analysis.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """计算性能指标"""
        if not self.current_analysis:
            return {}
        
        total_tool_calls = sum(len(step.tool_calls) for step in self.current_analysis.steps)
        total_llm_interactions = sum(len(step.llm_interactions) for step in self.current_analysis.steps)
        total_messages = sum(len(step.messages) for step in self.current_analysis.steps)
        total_tokens = sum(
            interaction.total_tokens 
            for step in self.current_analysis.steps 
            for interaction in step.llm_interactions
        )
        
        avg_step_duration = sum(step.duration for step in self.current_analysis.steps) / len(self.current_analysis.steps) if self.current_analysis.steps else 0
        
        return {
            "total_steps": len(self.current_analysis.steps),
            "total_tool_calls": total_tool_calls,
            "total_llm_interactions": total_llm_interactions,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "avg_step_duration": avg_step_duration,
            "successful_tool_calls": sum(
                sum(1 for tool in step.tool_calls if tool.success)
                for step in self.current_analysis.steps
            ),
            "successful_llm_interactions": sum(
                sum(1 for llm in step.llm_interactions if llm.success)
                for step in self.current_analysis.steps
            )
        }
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        if not self.current_analysis:
            return {}
        
        return {
            "report_id": self.current_analysis.report_id,
            "ticker": self.current_analysis.ticker,
            "analysis_date": self.current_analysis.analysis_date,
            "total_duration": self.current_analysis.total_duration,
            "final_decision": self.current_analysis.final_decision,
            "confidence_score": self.current_analysis.confidence_score,
            "performance_metrics": self.current_analysis.performance_metrics,
            "summary": self.current_analysis.summary
        }
    
    def export_analysis_report(self, filepath: str):
        """导出分析报告"""
        if not self.current_analysis:
            raise ValueError("没有正在进行的分析")
        
        report_data = asdict(self.current_analysis)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"分析报告已导出到: {filepath}")
    
    def generate_visualization_data(self) -> Dict[str, Any]:
        """生成可视化数据"""
        if not self.current_analysis:
            return {}
        
        # 步骤时间线数据
        timeline_data = []
        for step in self.current_analysis.steps:
            timeline_data.append({
                "step_id": step.step_id,
                "agent": step.agent.value,
                "step_name": step.step_name,
                "start_time": step.start_time,
                "end_time": step.end_time,
                "duration": step.duration,
                "step_type": step.step_type.value
            })
        
        # 工具调用统计
        tool_stats = {}
        for step in self.current_analysis.steps:
            for tool in step.tool_calls:
                if tool.tool_name not in tool_stats:
                    tool_stats[tool.tool_name] = {
                        "total_calls": 0,
                        "successful_calls": 0,
                        "total_duration": 0,
                        "total_data_size": 0
                    }
                tool_stats[tool.tool_name]["total_calls"] += 1
                tool_stats[tool.tool_name]["total_duration"] += tool.duration
                tool_stats[tool.tool_name]["total_data_size"] += tool.data_size or 0
                if tool.success:
                    tool_stats[tool.tool_name]["successful_calls"] += 1
        
        # LLM交互统计
        llm_stats = {}
        for step in self.current_analysis.steps:
            for llm in step.llm_interactions:
                if llm.model_name not in llm_stats:
                    llm_stats[llm.model_name] = {
                        "total_interactions": 0,
                        "total_tokens": 0,
                        "total_duration": 0,
                        "avg_temperature": 0
                    }
                llm_stats[llm.model_name]["total_interactions"] += 1
                llm_stats[llm.model_name]["total_tokens"] += llm.total_tokens
                llm_stats[llm.model_name]["total_duration"] += llm.duration
                llm_stats[llm.model_name]["avg_temperature"] += llm.temperature
        
        # 计算平均值
        for model in llm_stats:
            if llm_stats[model]["total_interactions"] > 0:
                llm_stats[model]["avg_temperature"] /= llm_stats[model]["total_interactions"]
        
        # 消息流数据
        message_flow = []
        for step in self.current_analysis.steps:
            for msg in step.messages:
                message_flow.append({
                    "timestamp": msg.timestamp,
                    "sender": msg.sender,
                    "receiver": msg.receiver,
                    "message_type": msg.message_type,
                    "content_length": len(msg.content),
                    "priority": msg.priority
                })
        
        return {
            "timeline_data": timeline_data,
            "tool_stats": tool_stats,
            "llm_stats": llm_stats,
            "message_flow": message_flow,
            "performance_metrics": self.current_analysis.performance_metrics,
            "risk_assessment": self.current_analysis.risk_assessment
        }

# 全局可视化器实例
visualizer = AnalysisVisualizer() 