import asyncio
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 创建自定义配置
config = DEFAULT_CONFIG.copy()
config["market_type"] = "china"  # 设置为中国市场
config["default_ticker"] = "000001"  # 默认股票：平安银行
config["default_index"] = "000001"  # 默认指数：上证指数
config["llm_provider"] = "openai"  # 使用 OpenAI 提供商
config["backend_url"] = "http://47.84.70.98:9000/v1"  # 阿里云服务器地址
config["deep_think_llm"] = "gpt-4o"  # 深度思考模型
config["quick_think_llm"] = "gpt-4o-mini"  # 快速思考模型
config["max_debate_rounds"] = 1  # 辩论轮次
config["online_tools"] = True  # 启用在线工具

# 使用自定义配置初始化
ta = TradingAgentsGraph(debug=True, config=config)

# 执行分析（中国股票示例）
print("开始分析中国股票...")
_, decision = asyncio.run(ta.propagate("000001", "2025-06-21"))  # 分析平安银行
print(f"最终决策：{decision}")

# 可以分析其他中国股票
# _, decision2 = ta.propagate("600036", "2025-06-21")  # 分析招商银行
# print("招商银行分析结果:")
# print(decision2)

# 记忆错误并反思（可选）
# ta.reflect_and_remember(1000)  # 参数是位置收益
