from typing import Optional
import datetime
import typer
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
from rich.columns import Columns
from rich.markdown import Markdown
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich.table import Table
from collections import deque
import time
from rich.tree import Tree
from rich import box
from rich.align import Align
from rich.rule import Rule

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from cli.models import AnalystType
from cli.utils import *

console = Console()

app = typer.Typer(
    name="ChinaStockAgents",
    help="ChinaStockAgents CLI: 多智能体大语言模型金融交易框架",
    add_completion=True,  # Enable shell completion
)


# Create a deque to store recent messages with a maximum length
class MessageBuffer:
    def __init__(self, max_length=100):
        self.messages = deque(maxlen=max_length)
        self.tool_calls = deque(maxlen=max_length)
        self.current_report = None
        self.final_report = None  # Store the complete final report
        self.agent_status = {
            # 分析师团队
            "市场分析师": "pending",
            "社交媒体分析师": "pending",
            "新闻分析师": "pending",
            "基本面分析师": "pending",
            # 研究团队
            "多头研究员": "pending",
            "空头研究员": "pending",
            "研究经理": "pending",
            # 交易团队
            "交易员": "pending",
            # 风险管理团队
            "激进分析师": "pending",
            "中性分析师": "pending",
            "保守分析师": "pending",
            # 投资组合管理团队
            "投资组合经理": "pending",
        }
        self.current_agent = None
        self.report_sections = {
            "market_report": None,
            "sentiment_report": None,
            "news_report": None,
            "fundamentals_report": None,
            "investment_plan": None,
            "trader_investment_plan": None,
            "final_trade_decision": None,
        }

    def add_message(self, message_type, content):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.messages.append((timestamp, message_type, content))

    def add_tool_call(self, tool_name, args):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.tool_calls.append((timestamp, tool_name, args))

    def update_agent_status(self, agent, status):
        if agent in self.agent_status:
            self.agent_status[agent] = status
            self.current_agent = agent

    def update_report_section(self, section_name, content):
        if section_name in self.report_sections:
            self.report_sections[section_name] = content
            self._update_current_report()

    def _update_current_report(self):
        # For the panel display, only show the most recently updated section
        latest_section = None
        latest_content = None

        # Find the most recently updated section
        for section, content in self.report_sections.items():
            if content is not None:
                latest_section = section
                latest_content = content

        if latest_section and latest_content:
            # Format the current section for display
            section_titles = {
                "market_report": "市场分析",
                "sentiment_report": "社交媒体情绪",
                "news_report": "新闻分析",
                "fundamentals_report": "基本面分析",
                "investment_plan": "研究团队决策",
                "trader_investment_plan": "交易团队计划",
                "final_trade_decision": "投资组合管理决策",
            }
            self.current_report = (
                f"### {section_titles[latest_section]}\n{latest_content}"
            )

        # Update the final complete report
        self._update_final_report()

    def _update_final_report(self):
        report_parts = []

        # Analyst Team Reports
        if any(
            self.report_sections[section]
            for section in [
                "market_report",
                "sentiment_report",
                "news_report",
                "fundamentals_report",
            ]
        ):
            report_parts.append("## 分析师团队报告")
            if self.report_sections["market_report"]:
                report_parts.append(
                    f"### 市场分析\n{self.report_sections['market_report']}"
                )
            if self.report_sections["sentiment_report"]:
                report_parts.append(
                    f"### 社交媒体情绪\n{self.report_sections['sentiment_report']}"
                )
            if self.report_sections["news_report"]:
                report_parts.append(
                    f"### 新闻分析\n{self.report_sections['news_report']}"
                )
            if self.report_sections["fundamentals_report"]:
                report_parts.append(
                    f"### 基本面分析\n{self.report_sections['fundamentals_report']}"
                )

        # Research Team Reports
        if self.report_sections["investment_plan"]:
            report_parts.append("## 研究团队决策")
            report_parts.append(f"{self.report_sections['investment_plan']}")

        # Trading Team Reports
        if self.report_sections["trader_investment_plan"]:
            report_parts.append("## 交易团队计划")
            report_parts.append(f"{self.report_sections['trader_investment_plan']}")

        # Portfolio Management Decision
        if self.report_sections["final_trade_decision"]:
            report_parts.append("## 投资组合管理决策")
            report_parts.append(f"{self.report_sections['final_trade_decision']}")

        self.final_report = "\n\n".join(report_parts) if report_parts else None


message_buffer = MessageBuffer()


def create_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    layout["main"].split_column(
        Layout(name="upper", ratio=3), Layout(name="analysis", ratio=5)
    )
    layout["upper"].split_row(
        Layout(name="progress", ratio=2), Layout(name="messages", ratio=3)
    )
    return layout


def update_display(layout, spinner_text=None):
    # Header with welcome message
    layout["header"].update(
        Panel(
            "[bold green]欢迎使用 ChinaStockAgents CLI[/bold green]\n"
            "[dim]© [Tauric Research](https://github.com/TauricResearch)[/dim]",
            title="欢迎使用 ChinaStockAgents",
            border_style="green",
            padding=(1, 2),
            expand=True,
        )
    )

    # Progress panel showing agent status
    progress_table = Table(title="智能体状态", show_header=True, header_style="bold magenta")
    progress_table.add_column("智能体", style="cyan", no_wrap=True)
    progress_table.add_column("状态", style="green")

    status_colors = {
        "pending": "dim",
        "in_progress": "yellow",
        "completed": "green",
        "error": "red"
    }

    for agent, status in message_buffer.agent_status.items():
        color = status_colors.get(status, "white")
        status_text = {
            "pending": "等待中",
            "in_progress": "进行中",
            "completed": "已完成",
            "error": "错误"
        }.get(status, status)
        
        progress_table.add_row(agent, f"[{color}]{status_text}[/{color}]")

    layout["progress"].update(Panel(progress_table, title="进度", border_style="blue"))

    # Messages panel
    messages_table = Table(title="消息和工具调用", show_header=True, header_style="bold magenta")
    messages_table.add_column("时间", style="cyan", no_wrap=True)
    messages_table.add_column("类型", style="green")
    messages_table.add_column("内容", style="white")

    # Add recent messages
    for timestamp, msg_type, content in list(message_buffer.messages)[-10:]:
        # Truncate content if too long
        if len(content) > 100:
            content = content[:97] + "..."
        messages_table.add_row(timestamp, msg_type, content)

    layout["messages"].update(Panel(messages_table, title="消息", border_style="blue"))

    # Current report panel
    if message_buffer.current_report:
        layout["analysis"].update(
            Panel(
                Markdown(message_buffer.current_report),
                title="当前报告",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        layout["analysis"].update(
            Panel(
                "等待分析开始...",
                title="当前报告",
                border_style="green",
                padding=(1, 2),
            )
        )

    # Footer with statistics
    tool_calls_count = len(message_buffer.tool_calls)
    llm_calls_count = len([msg for msg in message_buffer.messages if msg[1] == "LLM"])
    reports_count = len([content for content in message_buffer.report_sections.values() if content is not None])

    footer_content = f"工具调用: {tool_calls_count} | LLM 调用: {llm_calls_count} | 生成报告: {reports_count}"
    layout["footer"].update(
        Panel(
            footer_content,
            title="统计信息",
            border_style="blue",
            padding=(1, 2),
        )
    )


def get_user_selections():
    """获取分析所需的所有用户选择"""
    
    def create_question_box(title, prompt, default=None):
        """创建带有给定标题和提示的问题框"""
        question_text = f"{prompt}\n默认值: {default}" if default else prompt
        return Panel(
            question_text,
            title=title,
            border_style="blue",
            padding=(1, 2),
            expand=True,
        )

    # 步骤 1: 市场类型选择
    console.print(
        create_question_box(
            "步骤 1: 市场类型",
            "选择分析的市场类型",
            "中国 (中国股市)"
        )
    )
    
    market_type = console.input("[bold blue]选择市场类型 (china/us): [/bold blue]").strip().lower()
    if not market_type:
        market_type = "china"
    
    # 根据市场类型更新配置
    config = DEFAULT_CONFIG.copy()
    config["market_type"] = market_type
    
    if market_type == "china":
        config["default_ticker"] = "000001"  # 平安银行
        config["default_index"] = "000001"   # 上证指数
    else:
        config["default_ticker"] = "SPY"     # 标普500ETF
        config["default_index"] = "SPY"      # 标普500ETF

    # 步骤 2: 股票代码
    default_ticker = config["default_ticker"]
    ticker_prompt = "输入要分析的股票代码"
    if market_type == "china":
        ticker_prompt += "\n示例: 000001 (平安银行), 600000 (浦发银行), 000002 (万科A)"
    else:
        ticker_prompt += "\n示例: SPY, AAPL, TSLA, NVDA"
    
    console.print(
        create_question_box(
            "步骤 2: 股票代码",
            ticker_prompt,
            default_ticker
        )
    )
    
    ticker = console.input(f"[bold blue]输入股票代码: [/bold blue]").strip()
    if not ticker:
        ticker = default_ticker

    # 步骤 3: 分析日期
    console.print(
        create_question_box(
            "步骤 3: 分析日期",
            "输入分析日期 (YYYY-MM-DD)",
            "2025-06-21"
        )
    )
    
    analysis_date = console.input("[bold blue]输入分析日期: [/bold blue]").strip()
    if not analysis_date:
        analysis_date = "2025-06-21"

    # 步骤 4: 分析师团队
    console.print(
        create_question_box(
            "步骤 4: 分析师团队",
            "选择用于分析的 LLM 分析师智能体",
            "社交媒体分析师"
        )
    )
    
    analyst_options = [
        "社交媒体分析师",
        "新闻分析师", 
        "基本面分析师",
        "市场分析师"
    ]
    
    console.print("[dim]可用分析师:[/dim]")
    for i, analyst in enumerate(analyst_options, 1):
        console.print(f"  {i}. {analyst}")
    
    analyst_choice = console.input("[bold blue]选择分析师 (1-4): [/bold blue]").strip()
    if analyst_choice == "1" or not analyst_choice:
        selected_analysts = ["social"]
    elif analyst_choice == "2":
        selected_analysts = ["news"]
    elif analyst_choice == "3":
        selected_analysts = ["fundamentals"]
    elif analyst_choice == "4":
        selected_analysts = ["market"]
    else:
        selected_analysts = ["social"]

    # 步骤 5: 研究深度
    console.print(
        create_question_box(
            "步骤 5: 研究深度",
            "选择研究深度级别",
            "浅度"
        )
    )
    
    depth_options = [
        "浅度 - 快速研究，较少的辩论和策略讨论轮次",
        "中度 - 平衡研究，适度的辩论轮次",
        "深度 - 全面研究，广泛的辩论轮次"
    ]
    
    console.print("[dim]可用深度:[/dim]")
    for i, depth in enumerate(depth_options, 1):
        console.print(f"  {i}. {depth}")
    
    depth_choice = console.input("[bold blue]选择深度 (1-3): [/bold blue]").strip()
    if depth_choice == "1" or not depth_choice:
        config["max_debate_rounds"] = 1
        config["max_risk_discuss_rounds"] = 1
    elif depth_choice == "2":
        config["max_debate_rounds"] = 2
        config["max_risk_discuss_rounds"] = 2
    elif depth_choice == "3":
        config["max_debate_rounds"] = 3
        config["max_risk_discuss_rounds"] = 3
    else:
        config["max_debate_rounds"] = 1
        config["max_risk_discuss_rounds"] = 1

    # 步骤 6: OpenAI 后端
    console.print(
        create_question_box(
            "步骤 6: OpenAI 后端",
            "选择要使用的服务",
            "OpenAI"
        )
    )
    
    backend_choice = console.input("[bold blue]选择 LLM 提供商: [/bold blue]").strip()
    if not backend_choice:
        backend_choice = "OpenAI"
    
    console.print(f"[green]您选择了: {backend_choice}[/green]")
    console.print(f"[green]URL: {config['backend_url']}[/green]")

    # 步骤 7: 思考智能体
    console.print(
        create_question_box(
            "步骤 7: 思考智能体",
            "选择用于分析的思考智能体",
            "GPT-4o-mini"
        )
    )
    
    quick_llm = console.input("[bold blue]选择您的 [快速思考 LLM 引擎]: [/bold blue]").strip()
    if not quick_llm:
        quick_llm = "gpt-4o-mini"
    
    deep_llm = console.input("[bold blue]选择您的 [深度思考 LLM 引擎]: [/bold blue]").strip()
    if not deep_llm:
        deep_llm = "gpt-4o"
    
    config["quick_think_llm"] = quick_llm
    config["deep_think_llm"] = deep_llm

    return {
        "ticker": ticker,
        "analysis_date": analysis_date,
        "selected_analysts": selected_analysts,
        "config": config,
        "market_type": market_type
    }


def get_ticker():
    """Get ticker symbol from user input."""
    return typer.prompt("", default="SPY")


def get_analysis_date():
    """Get the analysis date from user input."""
    while True:
        date_str = typer.prompt(
            "", default=datetime.datetime.now().strftime("%Y-%m-%d")
        )
        try:
            # Validate date format and ensure it's not in the future
            analysis_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            if analysis_date.date() > datetime.datetime.now().date():
                console.print("[red]Error: Analysis date cannot be in the future[/red]")
                continue
            return date_str
        except ValueError:
            console.print(
                "[red]Error: Invalid date format. Please use YYYY-MM-DD[/red]"
            )


def display_complete_report(final_state):
    """显示完整的分析报告"""
    
    # 创建完整报告布局
    report_layout = Layout()
    report_layout.split_column(
        Layout(name="header", size=3),
        Layout(name="report", ratio=1),
        Layout(name="footer", size=3),
    )

    # 标题
    report_layout["header"].update(
        Panel(
            "[bold green]分析完成！[/bold green]\n"
            "[dim]以下是完整的分析报告[/dim]",
            title="ChinaStockAgents 分析报告",
            border_style="green",
            padding=(1, 2),
        )
    )

    # 报告内容
    if message_buffer.final_report:
        report_layout["report"].update(
            Panel(
                Markdown(message_buffer.final_report),
                title="完整分析报告",
                border_style="blue",
                padding=(1, 2),
            )
        )
    else:
        report_layout["report"].update(
            Panel(
                "报告生成中...",
                title="完整分析报告",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # 底部统计
    tool_calls_count = len(message_buffer.tool_calls)
    llm_calls_count = len([msg for msg in message_buffer.messages if msg[1] == "LLM"])
    reports_count = len([content for content in message_buffer.report_sections.values() if content is not None])

    footer_content = f"工具调用: {tool_calls_count} | LLM 调用: {llm_calls_count} | 生成报告: {reports_count}"
    report_layout["footer"].update(
        Panel(
            footer_content,
            title="最终统计",
            border_style="blue",
            padding=(1, 2),
        )
    )

    # 显示完整报告
    console.print(report_layout)

    # 显示最终决策
    if hasattr(message_buffer, 'final_decision') and message_buffer.final_decision:
        console.print("\n[bold green]最终投资决策:[/bold green]")
        console.print(Panel(
            message_buffer.final_decision,
            title="投资建议",
            border_style="green",
            padding=(1, 2),
        ))

    console.print("\n[green]分析完成！感谢使用 ChinaStockAgents！[/green]")


def update_research_team_status(status):
    """更新研究团队所有成员的状态"""
    research_team = ["多头研究员", "空头研究员", "研究经理"]
    for agent in research_team:
        message_buffer.update_agent_status(agent, status)

def extract_content_string(content):
    """从消息内容中提取字符串"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # 处理内容块列表
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_use':
                    text_parts.append(f"[工具调用: {item.get('name', '未知')}]")
            else:
                text_parts.append(str(item))
        return ' '.join(text_parts)
    else:
        return str(content)

def run_analysis():
    # 首先获取所有用户选择
    selections = get_user_selections()
    
    # 创建配置
    config = selections["config"]
    config["max_debate_rounds"] = selections["config"]["max_debate_rounds"]
    config["max_risk_discuss_rounds"] = selections["config"]["max_risk_discuss_rounds"]
    config["quick_think_llm"] = selections["config"]["quick_think_llm"]
    config["deep_think_llm"] = selections["config"]["deep_think_llm"]
    config["backend_url"] = selections["config"]["backend_url"]
    config["llm_provider"] = selections["config"]["llm_provider"].lower()

    # 初始化图形
    graph = TradingAgentsGraph(
        [analyst.value for analyst in selections["selected_analysts"]], config=config, debug=True
    )

    # 创建布局
    layout = create_layout()

    # 开始实时显示
    with Live(layout, refresh_per_second=4, screen=True):
        # 添加初始消息
        message_buffer.add_message(
            "系统",
            f"开始分析 {selections['ticker']} 在 {selections['analysis_date']} 的数据",
        )
        message_buffer.add_message(
            "系统",
            f"市场类型: {selections['market_type']}",
        )
        message_buffer.add_message(
            "系统",
            f"选择的分析师: {', '.join(get_analyst_chinese_name(analyst.value) for analyst in selections['selected_analysts'])}",
        )
        update_display(layout)

        # 将智能体状态更新为进行中
        first_analyst = get_analyst_chinese_name(selections['selected_analysts'][0].value)
        message_buffer.update_agent_status(first_analyst, "in_progress")
        update_display(layout)

        try:
            # 执行传播
            final_state, decision = graph.propagate(
                selections["ticker"], selections["analysis_date"]
            )

            # 更新所有智能体状态为已完成
            for agent in message_buffer.agent_status:
                message_buffer.update_agent_status(agent, "completed")

            # 添加完成消息
            message_buffer.add_message("系统", "分析完成！")
            update_display(layout)

            # 显示完整报告
            display_complete_report(final_state)

        except Exception as e:
            # 处理错误
            message_buffer.add_message("错误", f"分析过程中出现错误: {str(e)}")
            message_buffer.update_agent_status("错误", "error")
            update_display(layout)
            console.print(f"[red]错误: {str(e)}[/red]")
            raise e


@app.command()
def main():
    """ChinaStockAgents CLI - 多智能体大语言模型金融交易框架"""
    console.print(
        Panel(
            "[bold blue]ChinaStockAgents CLI[/bold blue]\n"
            "[dim]多智能体大语言模型金融交易框架[/dim]\n\n"
            "这个工具将帮助您分析股票并生成投资建议。\n"
            "请按照提示输入相关信息。",
            title="欢迎使用 ChinaStockAgents",
            border_style="green",
            padding=(1, 2),
        )
    )
    
    # 运行分析
    run_analysis()

@app.command()
def version():
    """显示版本信息"""
    console.print("[bold blue]ChinaStockAgents CLI v1.0.0[/bold blue]")
    console.print("[dim]多智能体大语言模型金融交易框架[/dim]")

def get_agent_chinese_name(english_name):
    """将英文智能体名称转换为中文显示名称"""
    name_mapping = {
        "Market Analyst": "市场分析师",
        "Social Analyst": "社交媒体分析师", 
        "News Analyst": "新闻分析师",
        "Fundamentals Analyst": "基本面分析师",
        "Bull Researcher": "多头研究员",
        "Bear Researcher": "空头研究员",
        "Research Manager": "研究经理",
        "Trader": "交易员",
        "Risky Analyst": "激进分析师",
        "Neutral Analyst": "中性分析师",
        "Safe Analyst": "保守分析师",
        "Portfolio Manager": "投资组合经理"
    }
    return name_mapping.get(english_name, english_name)

def get_analyst_chinese_name(analyst_type):
    """根据分析师类型获取中文名称"""
    analyst_mapping = {
        "market": "市场分析师",
        "social": "社交媒体分析师",
        "news": "新闻分析师", 
        "fundamentals": "基本面分析师"
    }
    return analyst_mapping.get(analyst_type, analyst_type)

if __name__ == "__main__":
    app()
