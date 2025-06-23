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

class NewsAnalysis(BaseModel):
    """
    News analysis report.
    This report should include a summary of the news sentiment, key news highlights,
    and a conclusion on the potential impact on the stock.
    """

    news_sentiment_summary: str = Field(
        description="""A summary of the overall sentiment from the news articles."""
    )
    key_news_highlights: List[str] = Field(
        description="""A list of key news headlines or talking points that are most impactful."""
    )
    conclusion: str = Field(
        description="""A conclusion on the potential impact of the news on the stock's price and future performance."""
    )


def get_news_analyst_prompt():
    """Returns the prompt for the news analyst."""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a financial news analyst. Your role is to analyze news articles related to a specific stock
                and provide a concise report on the sentiment and potential impact.

                Please provide the following in your report:
                - A summary of the news sentiment (Positive, Negative, Neutral).
                - Key news highlights that support your analysis.
                - A conclusion on the potential impact on the stock.
                
                For the China market, pay special attention to news from official sources like Xinhua or People's Daily,
                and announcements from regulatory bodies like the CSRC, as they can have a significant market impact.
                Please speak in Chinese.
                """,
            ),
            ("user", "{input}"),
        ]
    )


def create_news_analyst(llm, toolkit, visualizer: 'AnalysisVisualizer' = None):
    """Creates a news analyst agent."""
    prompt = get_news_analyst_prompt()
    chain = prompt | llm.with_structured_output(NewsAnalysis)

    def news_analyst_node(state):
        """
        Analyzes news for a given stock.

        Args:
            state: The current state of the simulation.

        Returns:
            The updated state with the news analysis.
        """
        company_name = state["company_name"]
        
        step_id = None
        callback_handler = None
        config = {}

        if visualizer and VisualizerCallbackHandler:
            step_id = f"news_analyst_{uuid.uuid4()}"
            visualizer.add_step(
                step_id=step_id,
                type="agent",
                agent_name="NewsAnalyst",
                details={"status": "started", "company_name": company_name}
            )
            callback_handler = VisualizerCallbackHandler(visualizer, step_id)
            config = {"callbacks": [callback_handler]}

        news_analysis = chain.invoke({"input": f"Analyze news for {company_name}."}, config=config)

        if visualizer and step_id:
            visualizer.update_step_data(step_id, "conclusion", news_analysis.dict())
            visualizer.update_step_data(step_id, "status", "completed")

        state["messages"].append(
            {
                "agent_name": "News Analyst",
                "content": f"News analysis for {company_name}: {news_analysis}",
                "analysis": news_analysis,
                "analyst_type": "news",
            }
        )
        return state

    return news_analyst_node
