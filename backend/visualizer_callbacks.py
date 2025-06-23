# -*- coding: utf-8 -*-
"""
LangChain Callback Handler for AnalysisVisualizer
This module provides a callback handler to connect the execution of LangChain agents
with the AnalysisVisualizer, allowing for real-time logging of LLM and tool interactions.
"""

import time
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from backend.analysis_visualizer import AnalysisVisualizer

class VisualizerCallbackHandler(BaseCallbackHandler):
    """
    Callback handler that logs LLM and tool interactions to the AnalysisVisualizer.
    It acts as a "probe" into the LangChain execution, reporting every significant event.
    """

    def __init__(self, visualizer: AnalysisVisualizer, step_id: str):
        """
        Initializes the callback handler.
        Args:
            visualizer: The AnalysisVisualizer instance to log to.
            step_id: The ID of the current analysis step to associate logs with.
        """
        self.visualizer = visualizer
        self.step_id = step_id
        # Dictionaries to track the start times and parameters of runs
        self.llm_starts: Dict[UUID, Dict[str, Any]] = {}
        self.tool_starts: Dict[UUID, Dict[str, Any]] = {}

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], *, run_id: UUID, **kwargs: Any
    ) -> None:
        """Called when an LLM run starts."""
        self.llm_starts[run_id] = {
            "start_time": time.time(),
            "prompt": "\n".join(prompts),
            "model_name": serialized.get("kwargs", {}).get("model_name", "unknown_model")
        }
        # 日志
        self.visualizer.add_log(
            agent="LLM",
            event="llm_call_start",
            detail=f"LLM模型 {self.llm_starts[run_id]['model_name']} 开始推理。Prompt: {self.llm_starts[run_id]['prompt'][:100]}...",
            status="running"
        )

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        """Called when an LLM run ends."""
        if run_id not in self.llm_starts:
            return

        start_info = self.llm_starts.pop(run_id)
        
        token_usage = response.llm_output.get("token_usage", {}) if response.llm_output else {}
        
        # Record the detailed LLM interaction using the visualizer
        self.visualizer.record_llm_interaction(
            step_id=self.step_id,
            model_name=start_info["model_name"],
            prompt=start_info["prompt"],
            response=response.generations[0][0].text,
            prompt_tokens=token_usage.get("prompt_tokens", 0),
            completion_tokens=token_usage.get("completion_tokens", 0),
            success=True,
        )
        # 日志
        self.visualizer.add_log(
            agent="LLM",
            event="llm_call_end",
            detail=f"LLM模型 {start_info['model_name']} 推理完成。输出: {response.generations[0][0].text[:100]}...",
            status="completed"
        )

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, *, run_id: UUID, **kwargs: Any
    ) -> None:
        """Called when a tool run starts."""
        self.tool_starts[run_id] = {
            "start_time": time.time(),
            "tool_name": serialized.get("name", "unknown_tool"),
            "params_str": input_str,
        }
        # 日志
        self.visualizer.add_log(
            agent="TOOL",
            event="tool_call_start",
            detail=f"工具 {self.tool_starts[run_id]['tool_name']} 开始调用，参数: {input_str[:100]}...",
            status="running"
        )

    def on_tool_end(
        self, output: str, *, run_id: UUID, **kwargs: Any
    ) -> None:
        """Called when a tool run ends successfully."""
        if run_id not in self.tool_starts:
            return

        start_info = self.tool_starts.pop(run_id)
        
        try:
            # LangChain sometimes passes a stringified dict
            params = json.loads(start_info["params_str"])
        except json.JSONDecodeError:
            params = {"input": start_info["params_str"]}

        # Record the successful tool call
        self.visualizer.record_tool_call(
            step_id=self.step_id,
            tool_name=start_info["tool_name"],
            parameters=params,
            result=output,
            success=True,
        )
        # 日志
        self.visualizer.add_log(
            agent="TOOL",
            event="tool_call_end",
            detail=f"工具 {start_info['tool_name']} 调用完成，输出: {output[:100]}...",
            status="completed"
        )

    def on_tool_error(
        self, error: Exception | KeyboardInterrupt, *, run_id: UUID, **kwargs: Any
    ) -> None:
        """Called when a tool run fails."""
        if run_id not in self.tool_starts:
            return
        
        start_info = self.tool_starts.pop(run_id)
        
        try:
            params = json.loads(start_info["params_str"])
        except json.JSONDecodeError:
            params = {"input": start_info["params_str"]}
            
        # Record the failed tool call
        self.visualizer.record_tool_call(
            step_id=self.step_id,
            tool_name=start_info["tool_name"],
            parameters=params,
            result="",
            success=False,
            error_message=str(error)
        )
        # 日志
        self.visualizer.add_log(
            agent="TOOL",
            event="tool_call_error",
            detail=f"工具 {start_info['tool_name']} 调用失败，错误: {str(error)}",
            status="error"
        ) 