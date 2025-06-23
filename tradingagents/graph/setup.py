# ChinaStockAgents/graph/setup.py

from langgraph.graph import StateGraph, END

from tradingagents.agents import (
    create_market_analyst,
    create_social_media_analyst,
    create_news_analyst,
    create_fundamentals_analyst,
    create_metaphysics_analyst,
    create_bull_researcher,
    create_bear_researcher,
    create_research_manager,
    create_trader,
    create_conservative_debator,
    create_aggresive_debator,
    create_neutral_debator,
    create_invest_judge,
    create_risk_manager,
)


class GraphSetup:
    """Sets up the trading agents graph."""

    def __init__(
        self,
        quick_thinking_llm,
        deep_thinking_llm,
        toolkit,
        tool_nodes,
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        risk_manager_memory,
        research_manager_memory,
        conditional_logic,
        visualizer=None,
    ):
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.toolkit = toolkit
        self.tool_nodes = tool_nodes
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.risk_manager_memory = risk_manager_memory
        self.research_manager_memory = research_manager_memory
        self.conditional_logic = conditional_logic
        self.visualizer = visualizer

        # Unified agent creation functions, using lambdas for deferred execution
        self.agent_creation_funcs = {
            "market_analyst": lambda: create_market_analyst(self.quick_thinking_llm, self.toolkit, self.visualizer),
            "social_media_analyst": lambda: create_social_media_analyst(self.quick_thinking_llm, self.toolkit, self.visualizer),
            "news_analyst": lambda: create_news_analyst(self.quick_thinking_llm, self.toolkit, self.visualizer),
            "fundamentals_analyst": lambda: create_fundamentals_analyst(self.quick_thinking_llm, self.toolkit, self.visualizer),
            "metaphysics_analyst": lambda: create_metaphysics_analyst(self.quick_thinking_llm, self.toolkit, self.visualizer),
            "bull_researcher": lambda: create_bull_researcher(self.deep_thinking_llm, self.bull_memory),
            "bear_researcher": lambda: create_bear_researcher(self.deep_thinking_llm, self.bear_memory),
            "research_manager": lambda: create_research_manager(self.deep_thinking_llm, self.research_manager_memory),
            "trader": lambda: create_trader(self.deep_thinking_llm, self.trader_memory),
            "conservative_debator": lambda: create_conservative_debator(self.deep_thinking_llm),
            "aggresive_debator": lambda: create_aggresive_debator(self.deep_thinking_llm),
            "neutral_debator": lambda: create_neutral_debator(self.deep_thinking_llm),
            "invest_judge": lambda: create_invest_judge(self.deep_thinking_llm, self.invest_judge_memory),
            "risk_manager": lambda: create_risk_manager(self.deep_thinking_llm, self.risk_manager_memory),
        }

    def setup_graph(self, selected_analysts):
        """Sets up and returns a fully dynamic trading agents graph."""
        workflow = StateGraph(self.toolkit.config["state_schema"])

        # Define roles: which analysts can run in parallel at the start
        PARALLEL_ANALYST_ROLES = [
            "market_analyst", "social_media_analyst", "news_analyst", 
            "fundamentals_analyst", "metaphysics_analyst"
        ]
        
        # Core sequential workflow roles
        CORE_WORKFLOW_ROLES = [
            "research_manager", "bull_researcher", "bear_researcher", "trader",
            "conservative_debator", "aggresive_debator", "neutral_debator",
            "invest_judge", "risk_manager"
        ]

        # Determine which of the selected analysts are valid parallel roles
        entry_analysts = [name for name in selected_analysts if name in PARALLEL_ANALYST_ROLES]
        
        # Determine all nodes that need to be added to the graph
        agents_to_add = set(entry_analysts).union(CORE_WORKFLOW_ROLES)
        
        for agent_name in agents_to_add:
            if agent_name in self.agent_creation_funcs:
                node = self.agent_creation_funcs[agent_name]()
                workflow.add_node(agent_name, node)
                # Add associated tool node if it exists for this analyst
                if agent_name in self.tool_nodes:
                    tool_node_name = f"{agent_name}_tool_node"
                    workflow.add_node(tool_node_name, self.tool_nodes[agent_name])
            else:
                 raise ValueError(f"GraphSetup: Unknown agent type '{agent_name}' not in agent_creation_funcs.")

        # --- Define Graph Edges ---

        # If no valid parallel analysts are selected, start directly with the research manager
        if not entry_analysts:
            workflow.set_entry_point("research_manager")
        else:
            # If there are analysts, they run in parallel from a dummy entry point
            workflow.set_entry_point("analyst_team")
            # This dummy node allows branching to multiple parallel analysts
            workflow.add_node("analyst_team", lambda state: state)

            for analyst_name in entry_analysts:
                # Branch out from the entry node to each selected parallel analyst
                workflow.add_edge("analyst_team", analyst_name)
                
                tool_node_name = f"{analyst_name}_tool_node"
                # Connect analyst to its tool node (if it exists)
                if tool_node_name in workflow.nodes:
                    workflow.add_edge(analyst_name, tool_node_name)
                    # After the tool, all analysts funnel into the research manager
                    workflow.add_edge(tool_node_name, "research_manager")
                else:
                    # If an analyst has no tool, connect directly to the research manager
                    workflow.add_edge(analyst_name, "research_manager")

        # Connect the core sequential workflow, which is static
        workflow.add_edge("research_manager", "bull_researcher")
        workflow.add_edge("bull_researcher", "bear_researcher")
        workflow.add_edge("bear_researcher", "trader")
        workflow.add_edge("trader", "conservative_debator")
        workflow.add_conditional_edges(
            "conservative_debator",
            self.conditional_logic.decide_to_continue_or_end_debate,
            {
                "continue": "aggresive_debator",
                "end": "invest_judge",
            },
        )
        workflow.add_edge("aggresive_debator", "neutral_debator")
        workflow.add_edge("neutral_debator", "conservative_debator")
        workflow.add_edge("invest_judge", "risk_manager")
        workflow.add_edge("risk_manager", END)

        return workflow.compile()