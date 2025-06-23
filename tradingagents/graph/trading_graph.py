# ChinaStockAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date
from typing import Dict, Any, Tuple, List, Optional, Callable, Coroutine

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.interface import set_config
from tradingagents.agents.utils.china_toolkit import ChinaToolkit

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor

# Import the visualizer but handle potential circular imports or non-existence gracefully
try:
    from backend.analysis_visualizer import AnalysisVisualizer
except (ImportError, ModuleNotFoundError):
    AnalysisVisualizer = None

class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts: Optional[List[str]] = None,
        debug: bool = False,
        config: Optional[Dict[str, Any]] = None,
        visualizer: Optional[Any] = None, # Accept the visualizer instance
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include.
            debug: Whether to run in debug mode.
            config: Configuration dictionary. If None, uses default config.
            visualizer: An optional instance of AnalysisVisualizer for logging.
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG
        self.visualizer = visualizer # Store the visualizer
        
        # Use provided selected_analysts or default
        self.selected_analysts = selected_analysts or ["market_analyst", "social_media_analyst", "news_analyst", "fundamentals_analyst"]

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs
        if self.config["llm_provider"].lower() == "openai" or self.config["llm_provider"] == "ollama" or self.config["llm_provider"] == "openrouter":
            self.deep_thinking_llm = ChatOpenAI(
                model=self.config["deep_think_llm"],
                base_url=self.config["backend_url"],
                api_key=self.config["openai_api_key"]
            )
            self.quick_thinking_llm = ChatOpenAI(
                model=self.config["quick_think_llm"],
                base_url=self.config["backend_url"],
                api_key=self.config["openai_api_key"]
            )
        elif self.config["llm_provider"].lower() == "anthropic":
            self.deep_thinking_llm = ChatAnthropic(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatAnthropic(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "google":
            self.deep_thinking_llm = ChatGoogleGenerativeAI(model=self.config["deep_think_llm"])
            self.quick_thinking_llm = ChatGoogleGenerativeAI(model=self.config["quick_think_llm"])
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config['llm_provider']}")
        
        # Use the appropriate toolkit based on market type
        if self.config.get("market_type") == "china":
            self.toolkit = ChinaToolkit(config=self.config)
        else:
            # Assuming the original Toolkit is for US market
            from tradingagents.agents.utils.agent_utils import Toolkit
            self.toolkit = Toolkit(config=self.config)

        # Initialize memories
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)
        self.research_manager_memory = FinancialSituationMemory("research_manager_memory", self.config)

        # Create tool nodes for selected analysts
        self.tool_nodes = self._create_tool_nodes(self.selected_analysts)

        # Initialize components, passing the visualizer to the setup
        self.conditional_logic = ConditionalLogic()
        self.graph_setup = GraphSetup(
            quick_thinking_llm=self.quick_thinking_llm,
            deep_thinking_llm=self.deep_thinking_llm,
            toolkit=self.toolkit,
            tool_nodes=self.tool_nodes,
            bull_memory=self.bull_memory,
            bear_memory=self.bear_memory,
            trader_memory=self.trader_memory,
            invest_judge_memory=self.invest_judge_memory,
            risk_manager_memory=self.risk_manager_memory,
            research_manager_memory=self.research_manager_memory,
            conditional_logic=self.conditional_logic,
            visualizer=self.visualizer, # Pass visualizer
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph using the selected analysts
        self.graph = self.graph_setup.setup_graph(self.selected_analysts)

    def _create_tool_nodes(self, selected_analysts: List[str]) -> Dict[str, ToolNode]:
        """Create tool nodes for the selected analysts based on market type."""
        tool_nodes = {}
        
        if self.config.get("market_type") == "china":
            # Define all possible tool nodes for China market
            all_tool_nodes = {
                "market_analyst": ToolNode([self.toolkit.get_stock_data, self.toolkit.get_china_technical_indicators_online]),
                "social_media_analyst": ToolNode([self.toolkit.get_stock_news, self.toolkit.get_china_market_sentiment]),
                "news_analyst": ToolNode([self.toolkit.get_china_global_news_online, self.toolkit.get_stock_news]),
                "fundamentals_analyst": ToolNode([self.toolkit.get_fundamentals_analysis, self.toolkit.get_china_financial_statements]),
                "metaphysics_analyst": ToolNode([self.toolkit.get_stock_data, self.toolkit.get_stock_info, self.toolkit.get_traditional_calendar_info]),
            }
            # Only include nodes for selected analysts
            for analyst in selected_analysts:
                if analyst in all_tool_nodes:
                    tool_nodes[analyst] = all_tool_nodes[analyst]
        else:
            # Original US market tool nodes
            from tradingagents.agents.utils.agent_utils import Toolkit
            us_toolkit = Toolkit(config=self.config)
            all_tool_nodes = {
                "market_analyst": ToolNode([us_toolkit.get_YFin_data_online, us_toolkit.get_stockstats_indicators_report_online]),
                "social_media_analyst": ToolNode([us_toolkit.get_stock_news_openai, us_toolkit.get_reddit_stock_info]),
                "news_analyst": ToolNode([us_toolkit.get_global_news_openai, us_toolkit.get_google_news]),
                "fundamentals_analyst": ToolNode([us_toolkit.get_fundamentals_openai, us_toolkit.get_simfin_income_stmt]),
                "traditional_analyst": ToolNode([us_toolkit.get_YFin_data_online, us_toolkit.get_stock_news_openai]),
            }
            # Only include nodes for selected analysts
            for analyst in selected_analysts:
                if analyst in all_tool_nodes:
                    tool_nodes[analyst] = all_tool_nodes[analyst]
                    
        return tool_nodes
        
    async def propagate(
        self, 
        company_name: str, 
        trade_date: str,
        async_callback: Optional[Callable[[], Coroutine[Any, Any, None]]] = None
    ):
        """
        Run the trading agents graph for a company on a specific date with streaming.
        
        Args:
            company_name: The ticker or name of the company.
            trade_date: The date for the analysis.
            async_callback: An async function to call after each step for real-time updates.
        """
        self.ticker = company_name

        init_agent_state = self.propagator.create_initial_state(company_name, trade_date)
        args = self.propagator.get_graph_args()

        final_state = None
        async for chunk in self.graph.astream(init_agent_state, **args):
            final_state = chunk
            # The 'chunk' contains the state after each node's execution.
            # We can inspect it to see which node just ran.
            last_ran_node = list(chunk.keys())[-1]
            print(f"--- Just ran node: {last_ran_node} ---")
            if self.debug:
                if chunk[last_ran_node].get("messages"):
                    chunk[last_ran_node]["messages"][-1].pretty_print()
            
            # If a callback is provided, call it to stream updates
            if async_callback:
                await async_callback()

        self.curr_state = final_state

        if final_state:
            self._log_state(trade_date, final_state)
            return final_state, self.process_signal(final_state.get("final_trade_decision", "HOLD"))
        
        return None, "Error: No final state"

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "bull_research": final_state["bull_research"],
            "bear_research": final_state["bear_research"],
            "research_manager_report": final_state["research_manager_report"],
            "trader_decision": final_state["trader_decision"],
            "aggressive_debator": final_state["aggressive_debator"],
            "neutral_debator": final_state["neutral_debator"],
            "conservative_debator": final_state["conservative_debator"],
            "final_trade_decision": final_state["final_trade_decision"],
        }

        # Save to file
        log_dir = os.path.join(self.config["project_dir"], "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"trading_agents_log_{trade_date}.json")
        
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(self.log_states_dict[str(trade_date)], f, ensure_ascii=False, indent=2)

    def reflect_and_remember(self, returns_losses):
        """Reflect on the trading decision and update memories."""
        if self.curr_state is None:
            return
        
        reflection = self.reflector.reflect_on_decision(
            self.curr_state, returns_losses
        )
        
        # Update memories based on reflection
        self.bull_memory.add_memory(reflection["bull_memory"])
        self.bear_memory.add_memory(reflection["bear_memory"])
        self.trader_memory.add_memory(reflection["trader_memory"])
        self.invest_judge_memory.add_memory(reflection["invest_judge_memory"])
        self.risk_manager_memory.add_memory(reflection["risk_manager_memory"])
        self.research_manager_memory.add_memory(reflection["research_manager_memory"])

    def process_signal(self, full_signal):
        """Process the final trade decision signal."""
        return self.signal_processor.process_signal(full_signal)
