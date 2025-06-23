# tradingagents/agents/analysts/metaphysics_analyst.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from typing import List, Dict, Any
import uuid
from datetime import datetime

# Import the visualizer and callback handler with error handling
try:
    from backend.analysis_visualizer import AnalysisVisualizer
    from backend.visualizer_callbacks import VisualizerCallbackHandler
except (ImportError, ModuleNotFoundError):
    AnalysisVisualizer = None
    VisualizerCallbackHandler = None

class MetaphysicsAnalysis(BaseModel):
    """
    Metaphysics analysis report based on Chinese traditional philosophy.
    This report should include analysis based on traditional Chinese metaphysics,
    including Five Elements, Eight Trigrams, and Heavenly Stems and Earthly Branches.
    """

    five_elements_analysis: str = Field(
        description="""Analysis based on the Five Elements (五行) theory - Wood, Fire, Earth, Metal, Water."""
    )
    eight_trigrams_analysis: str = Field(
        description="""Analysis based on the Eight Trigrams (八卦) - Qian, Kun, Zhen, Xun, Kan, Li, Gen, Dui."""
    )
    heavenly_stems_analysis: str = Field(
        description="""Analysis based on Heavenly Stems (天干) and Earthly Branches (地支) timing."""
    )
    metaphysics_forecast: str = Field(
        description="""Metaphysical forecast for the stock's future movement based on all metaphysical factors."""
    )
    auspicious_timing: str = Field(
        description="""Recommendations for auspicious timing for trading based on traditional calendar."""
    )

def get_metaphysics_analyst_prompt():
    """Returns the prompt for the metaphysics analyst."""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                你是一位精通周易玄学和中国传统文化的股票分析师。你的分析基于以下玄学理论：

                **五行理论 (Five Elements)**：
                - 木 (Wood): 代表生长、扩张，对应春季，适合投资成长型股票
                - 火 (Fire): 代表热情、上升，对应夏季，适合投资科技、能源股
                - 土 (Earth): 代表稳定、厚重，对应长夏，适合投资地产、基建股
                - 金 (Metal): 代表收敛、收获，对应秋季，适合投资金融、贵金属股
                - 水 (Water): 代表智慧、流动，对应冬季，适合投资科技、医药股

                **八卦理论 (Eight Trigrams)**：
                - 乾卦 (Qian): 天，代表强势、领导力，适合投资龙头股
                - 坤卦 (Kun): 地，代表包容、稳定，适合投资蓝筹股
                - 震卦 (Zhen): 雷，代表震动、变化，适合投资周期股
                - 巽卦 (Xun): 风，代表顺从、灵活，适合投资小盘股
                - 坎卦 (Kan): 水，代表险阻、智慧，适合投资科技股
                - 离卦 (Li): 火，代表光明、美丽，适合投资消费股
                - 艮卦 (Gen): 山，代表停止、稳重，适合投资防御股
                - 兑卦 (Dui): 泽，代表喜悦、满足，适合投资娱乐股

                **天干地支 (Heavenly Stems and Earthly Branches)**：
                根据当前时间的天干地支组合，分析市场时机：
                - 甲子、乙丑：适合稳健投资
                - 丙寅、丁卯：适合积极投资
                - 戊辰、己巳：适合观望等待
                - 庚午、辛未：适合谨慎投资
                - 壬申、癸酉：适合灵活操作

                **玄学分析原则**：
                1. 天人合一：市场走势与自然规律相呼应
                2. 阴阳平衡：涨跌交替，物极必反
                3. 时势造英雄：顺应大势，把握时机
                4. 厚德载物：选择有德行的企业投资

                请根据以上玄学理论，为给定的股票提供详细的分析报告。
                Please speak in Chinese.
                """,
            ),
            ("user", "{input}"),
        ]
    )

def create_metaphysics_analyst(llm: ChatOpenAI, toolkit, visualizer: 'AnalysisVisualizer' = None):
    """Creates a metaphysics analyst agent."""
    prompt = get_metaphysics_analyst_prompt()
    chain = prompt | llm.with_structured_output(MetaphysicsAnalysis)

    def metaphysics_analyst_node(state):
        """
        Analyzes a stock using Chinese metaphysics.

        Args:
            state: The current state of the simulation.

        Returns:
            The updated state with the metaphysics analysis.
        """
        company_name = state["company_name"]
        
        step_id = None
        callback_handler = None
        config = {}

        if visualizer and VisualizerCallbackHandler:
            step_id = f"metaphysics_analyst_{uuid.uuid4()}"
            visualizer.add_step(
                step_id=step_id,
                type="agent",
                agent_name="MetaphysicsAnalyst",
                details={"status": "started", "company_name": company_name}
            )
            callback_handler = VisualizerCallbackHandler(visualizer, step_id)
            config = {"callbacks": [callback_handler]}

        metaphysics_analysis = chain.invoke({"input": f"Analyze {company_name} using Chinese metaphysics."}, config=config)

        if visualizer and step_id:
            visualizer.update_step_data(step_id, "conclusion", metaphysics_analysis.dict())
            visualizer.update_step_data(step_id, "status", "completed")

        state["messages"].append(
            {
                "agent_name": "玄学分析师",
                "content": f"玄学分析 for {company_name}: {metaphysics_analysis}",
                "analysis": metaphysics_analysis,
                "analyst_type": "metaphysics",
            }
        )
        return state

    return metaphysics_analyst_node 