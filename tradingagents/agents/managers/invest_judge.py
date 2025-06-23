from langchain_core.messages import AIMessage
import time
import json


def create_invest_judge(llm, memory):
    """Creates an investment judge that makes final investment decisions."""
    
    def invest_judge_node(state) -> dict:
        # 获取各种分析报告
        market_report = state.get("market_report", "")
        sentiment_report = state.get("sentiment_report", "")
        news_report = state.get("news_report", "")
        fundamentals_report = state.get("fundamentals_report", "")
        metaphysics_report = state.get("metaphysics_report", "")
        
        # 获取交易员决策
        trader_decision = state.get("trader_investment_plan", "")
        
        # 获取风险辩论状态
        risk_debate_state = state.get("risk_debate_state", {})
        debate_history = risk_debate_state.get("history", "")
        
        prompt = f"""As the Investment Judge, your role is to make the final investment decision based on all available information. 
        You must carefully evaluate the trader's decision, all analyst reports, and the risk debate to make a well-informed final judgment.
        
        Trader's Investment Plan:
        {trader_decision}
        
        Market Research Report:
        {market_report}
        
        Social Media Sentiment Report:
        {sentiment_report}
        
        News Analysis Report:
        {news_report}
        
        Fundamentals Analysis Report:
        {fundamentals_report}
        
        Metaphysics Analysis Report:
        {metaphysics_report}
        
        Risk Debate History:
        {debate_history}
        
        Based on all this information, provide your final investment decision. 
        Consider the balance between risk and reward, market conditions, and all analyst perspectives.
        Your decision should be clear, actionable, and well-justified.
        
        Output your decision in a clear, professional format without special formatting."""
        
        response = llm.invoke(prompt)
        
        judge_decision = f"Investment Judge Decision: {response.content}"
        
        # 更新状态
        new_state = {
            "investment_debate_state": {
                "judge_decision": judge_decision,
                "final_decision": response.content,
                "decision_timestamp": time.time()
            }
        }
        
        # 添加到记忆
        if memory:
            memory.add_memory({
                "decision": response.content,
                "timestamp": time.time(),
                "context": {
                    "market_report": market_report[:200],
                    "sentiment_report": sentiment_report[:200],
                    "news_report": news_report[:200],
                    "fundamentals_report": fundamentals_report[:200],
                    "metaphysics_report": metaphysics_report[:200] if metaphysics_report else ""
                }
            })
        
        return new_state
    
    return invest_judge_node 