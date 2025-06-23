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

class SocialMediaAnalysis(BaseModel):
    """
    Social media analysis report.
    This report should include a summary of the social media sentiment,
    key discussion points, and a conclusion on its potential market impact.
    """

    sentiment_summary: str = Field(
        description="""A summary of the overall social media sentiment (e.g., Bullish, Bearish, Neutral)."""
    )
    key_discussion_points: List[str] = Field(
        description="""Key themes or topics being discussed on social media regarding the stock."""
    )
    conclusion: str = Field(
        description="""A conclusion on the potential impact of social media sentiment on the stock's short-term price movement."""
    )


def get_social_media_analyst_prompt():
    """Returns the prompt for the social media analyst."""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a social media analyst specializing in financial markets. Your task is to analyze
                social media conversations about a specific stock and provide a report on market sentiment.

                Please provide the following in your report:
                - A summary of the social media sentiment.
                - Key discussion points or themes.
                - A conclusion on the potential impact on the stock's price.
                
                For the China market, sources like Weibo (微博), Xueqiu (雪球), and East Money's Guba (东方财富股吧)
                are key platforms for gauging retail investor sentiment.
                Please speak in Chinese.
                """,
            ),
            ("user", "{input}"),
        ]
    )


def create_social_media_analyst(llm, toolkit, visualizer: 'AnalysisVisualizer' = None):
    """Creates a social media analyst agent."""
    prompt = get_social_media_analyst_prompt()
    chain = prompt | llm.with_structured_output(SocialMediaAnalysis)

    def social_media_analyst_node(state):
        """
        Analyzes social media for a given stock.

        Args:
            state: The current state of the simulation.

        Returns:
            The updated state with the social media analysis.
        """
        company_name = state["company_name"]
        
        step_id = None
        callback_handler = None
        config = {}

        if visualizer and VisualizerCallbackHandler:
            step_id = f"social_media_analyst_{uuid.uuid4()}"
            visualizer.add_step(
                step_id=step_id,
                type="agent",
                agent_name="SocialMediaAnalyst",
                details={"status": "started", "company_name": company_name}
            )
            callback_handler = VisualizerCallbackHandler(visualizer, step_id)
            config = {"callbacks": [callback_handler]}

        social_media_analysis = chain.invoke({"input": f"Analyze social media for {company_name}."}, config=config)

        if visualizer and step_id:
            visualizer.update_step_data(step_id, "conclusion", social_media_analysis.dict())
            visualizer.update_step_data(step_id, "status", "completed")

        state["messages"].append(
            {
                "agent_name": "Social Media Analyst",
                "content": f"Social media analysis for {company_name}: {social_media_analysis}",
                "analysis": social_media_analysis,
                "analyst_type": "social",
            }
        )
        return state

    return social_media_analyst_node
