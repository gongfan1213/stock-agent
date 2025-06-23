import os
from tradingagents.agents.utils.agent_states import AgentState

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "data_dir": "/Users/yluo/Documents/Code/ScAI/FR1-data",
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "gpt-4o",
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": "http://47.84.70.98:9000/v1",
    "openai_api_key": os.environ.get("OPENAI_API_KEY", "xxxxxxxxxxxxxx"),
    # Market settings
    "market_type": "china",  # "china" 或 "us"
    "default_ticker": "000001",  # 默认股票代码（平安银行）
    "default_index": "000001",  # 默认指数（上证指数）
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Tool settings
    "online_tools": True,
}
DEFAULT_CONFIG["state_schema"] = AgentState
