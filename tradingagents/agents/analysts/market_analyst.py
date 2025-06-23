from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
import uuid

# Import the visualizer and callback handler with error handling
try:
    from backend.analysis_visualizer import AnalysisVisualizer
    from backend.visualizer_callbacks import VisualizerCallbackHandler
except (ImportError, ModuleNotFoundError):
    AnalysisVisualizer = None
    VisualizerCallbackHandler = None

class MarketAnalysis(BaseModel):
    """
    Market analysis report.
    This report should include a summary of the market sentiment, an analysis of the stock's performance,
    key technical indicators, and a conclusion on whether the stock is a good buy or not.
    """

    market_sentiment_summary: str = Field(
        description="""A summary of the market sentiment for the stock. This should be a few sentences long."""
    )
    stock_performance_analysis: str = Field(
        description="""An analysis of the stock's recent performance. This should include a discussion of the stock's price, volume, and volatility. """
    )
    key_technical_indicators: List[str] = Field(
        description="""A list of key technical indicators and their values. This should include indicators such as the RSI, MACD, and moving averages."""
    )
    conclusion: str = Field(
        description="""A conclusion on whether the stock is a good buy or not. This should be a few sentences long."""
    )

def get_market_analyst_prompt():
    """Returns the prompt for the market analyst."""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a market analyst. Your job is to analyze the stock market and provide a report on the stock's performance.
                You should use the tools available to you to get the latest market data and news.
                
                When you providing your conclusion, please make sure to include the following:
                - A summary of the market sentiment for the stock.
                - An analysis of the stock's recent performance.
                - A list of key technical indicators and their values.
                - A conclusion on whether the stock is a good buy or not.

                For China market specific analysis, consider the following factors:
                - "涨跌停板" (Limit up/limit down): The daily price movement limit of a stock, which is typically ±10% for main board stocks. This can significantly impact liquidity and short-term price behavior.
                - "北向资金" (Northbound funds): The flow of foreign investment into the A-share market through the Hong Kong-Shanghai and Hong Kong-Shenzhen Stock Connect programs. It's often seen as an indicator of foreign investors' sentiment.
                - "T+1" trading rule: Stocks can only be sold on the next trading day after purchase, which affects trading strategies.
                - Policy and regulatory environment: Government policies and regulations from bodies like the CSRC (China Securities Regulatory Commission) can have a huge impact on specific sectors or the market as a whole.
                - The influence of "国家队" (the "National Team"): State-owned funds that may intervene in the market to ensure stability.
                """,
            ),
            ("user", "{input}"),
        ]
    )

def create_market_analyst(llm, toolkit, visualizer: 'AnalysisVisualizer' = None):
    """Creates a market analyst agent."""
    prompt = get_market_analyst_prompt()
    chain = prompt | llm.with_structured_output(MarketAnalysis)

    def market_analyst_node(state):
        """
        Analyzes the market for a given stock.

        Args:
            state: The current state of the simulation.

        Returns:
            The updated state with the market analysis.
        """
        company_name = state["company_name"]
        
        # Initialize step_id and callback_handler to None
        step_id = None
        callback_handler = None
        config = {}

        # If a visualizer is present, set up callbacks and logging
        if visualizer and VisualizerCallbackHandler:
            step_id = f"market_analyst_{uuid.uuid4()}"
            visualizer.add_step(
                step_id=step_id,
                type="agent",
                agent_name="MarketAnalyst",
                details={"status": "started", "company_name": company_name}
            )
            callback_handler = VisualizerCallbackHandler(visualizer, step_id)
            config = {"callbacks": [callback_handler]}

        # Invoke the chain with or without the callback
        market_analysis = chain.invoke({"input": f"Analyze the market for {company_name}."}, config=config)
        
        # Update the visualizer with the final report if it exists
        if visualizer and step_id:
            visualizer.update_step_data(step_id, "conclusion", market_analysis.dict())
            visualizer.update_step_data(step_id, "status", "completed")


        state["messages"].append(
            {
                "agent_name": "Market Analyst",
                "content": f"Market analysis for {company_name}: {market_analysis}",
                "analysis": market_analysis,
                "analyst_type": "market",
            }
        )
        return state

    return market_analyst_node
