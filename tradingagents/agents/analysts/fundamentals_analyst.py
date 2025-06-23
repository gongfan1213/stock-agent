from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Dict, Any
import uuid

# Import the visualizer and callback handler with error handling
try:
    from backend.analysis_visualizer import AnalysisVisualizer
    from backend.visualizer_callbacks import VisualizerCallbackHandler
except (ImportError, ModuleNotFoundError):
    AnalysisVisualizer = None
    VisualizerCallbackHandler = None

class FundamentalsAnalysis(BaseModel):
    """
    Fundamentals analysis report.
    This report should include an analysis of the company's financial health,
    key financial ratios, and a conclusion on its investment potential based on fundamentals.
    """

    financial_health_summary: str = Field(
        description="""A summary of the company's financial health, covering revenue, profit, and debt."""
    )
    key_financial_ratios: Dict[str, Any] = Field(
        description="""A dictionary of key financial ratios (e.g., P/E, P/B, ROE)."""
    )
    conclusion: str = Field(
        description="""A conclusion on the company's investment potential based on its fundamentals."""
    )


def get_fundamentals_analyst_prompt():
    """Returns the prompt for the fundamentals analyst."""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a fundamentals analyst. Your job is to analyze the financial health of a company
                and provide a report on its investment potential.

                Please provide the following in your report:
                - An analysis of the company's financial health (revenue, profit, debt).
                - Key financial ratios (P/E, P/B, ROE).
                - A conclusion on the company's investment potential.
                
                For the China market, be aware that financial reporting standards (e.g., CAS) might differ
                from IFRS or GAAP. Pay attention to accounts receivable and goodwill, which can sometimes be red flags.
                Please speak in Chinese.
                """,
            ),
            ("user", "{input}"),
        ]
    )


def create_fundamentals_analyst(llm, toolkit, visualizer: 'AnalysisVisualizer' = None):
    """Creates a fundamentals analyst agent."""
    prompt = get_fundamentals_analyst_prompt()
    chain = prompt | llm.with_structured_output(FundamentalsAnalysis)

    def fundamentals_analyst_node(state):
        """
        Analyzes the fundamentals of a given stock.

        Args:
            state: The current state of the simulation.

        Returns:
            The updated state with the fundamentals analysis.
        """
        company_name = state["company_name"]
        
        step_id = None
        callback_handler = None
        config = {}

        if visualizer and VisualizerCallbackHandler:
            step_id = f"fundamentals_analyst_{uuid.uuid4()}"
            visualizer.add_step(
                step_id=step_id,
                type="agent",
                agent_name="FundamentalsAnalyst",
                details={"status": "started", "company_name": company_name}
            )
            callback_handler = VisualizerCallbackHandler(visualizer, step_id)
            config = {"callbacks": [callback_handler]}

        fundamentals_analysis = chain.invoke({"input": f"Analyze fundamentals for {company_name}."}, config=config)
        
        if visualizer and step_id:
            visualizer.update_step_data(step_id, "conclusion", fundamentals_analysis.dict())
            visualizer.update_step_data(step_id, "status", "completed")

        state["messages"].append(
            {
                "agent_name": "Fundamentals Analyst",
                "content": f"Fundamentals analysis for {company_name}: {fundamentals_analysis}",
                "analysis": fundamentals_analysis,
                "analyst_type": "fundamentals",
            }
        )
        return state

    return fundamentals_analyst_node
