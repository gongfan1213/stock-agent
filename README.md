# stock-agent基于13个智能体的Langgraph中国A股系统


![image](https://github.com/user-attachments/assets/c2149470-e6ed-42f9-b430-2f51eb02b707)


![image](https://github.com/user-attachments/assets/74dd76dc-b732-4976-b7fd-9bf92aa0ee52)


![image](https://github.com/user-attachments/assets/985f700f-09b3-485e-9585-e77cc4437753)


![image](https://github.com/user-attachments/assets/25912c94-f7a4-4d36-9cbf-0994b6136f58)


![image](https://github.com/user-attachments/assets/05a8b6aa-ca8b-4387-9453-0f50560b996f)


![image](https://github.com/user-attachments/assets/70165fed-b6bd-4eba-a04d-724b96bff69b)


![image](https://github.com/user-attachments/assets/1652ee65-4639-47d7-ad03-1aea196af4c1)


![image](https://github.com/user-attachments/assets/5fafb52a-8181-40f8-a455-49a5c3f496be)

![image](https://github.com/user-attachments/assets/b9838531-004b-48be-a14e-e53df42a4985)




## 概述

本系统是基于TradingAgents框架的中国股市智能体分析系统，专门为中国股市设计，支持实时数据获取、多智能体协作分析和投资决策生成。

## 主要特性

### 🎯 中国股市专用功能
- **实时数据获取**: 基于AKShare的中国股市数据接口
- **技术指标分析**: 支持MACD、KDJ、RSI、BOLL等中国股市常用指标
- **基本面分析**: 财务报表、财务比率、估值模型
- **新闻情绪分析**: 政策影响、市场热点、投资者情绪
- **风险控制**: 涨跌停板、交易时间、政策风险考虑

### 🤖 多智能体协作
- **市场分析师**: 技术面分析和趋势预测
- **基本面分析师**: 财务指标和估值分析
- **新闻分析师**: 政策影响和市场热点
- **社交媒体分析师**: 投资者情绪分析
- **多头研究员**: 看涨理由和机会分析
- **空头研究员**: 风险提示和谨慎观点
- **研究经理**: 综合分析和最终建议
- **交易员**: 具体交易策略和时机
- **风险管理团队**: 激进、中性、保守策略分析
- **投资组合经理**: 最终投资决策

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 安装AKShare（中国股市数据接口）
pip install akshare

# 设置环境变量
export MARKET_TYPE=china
export DEFAULT_TICKER=000001
export DEFAULT_INDEX=000001
```

### 2. 启动服务器

```bash
# 方式1: 使用中国股市专用启动脚本
cd backend
python start_china_server.py

# 方式2: 直接启动
cd backend
python main.py
```

### 3. 测试系统

```bash
# 运行测试脚本
python test_china_market.py
```

## API接口

### 基础接口

#### 健康检查
```http
GET /api/health
```

#### 系统信息
```http
GET /api/system-info
```

### 数据接口

#### 获取股票信息
```http
GET /api/stock-info/{ticker}
```

#### 获取股票历史数据
```http
GET /api/stock-data/{ticker}?date=2025-01-21&look_back_days=30
```

#### 获取市场概况
```http
GET /api/market-overview
```

#### 获取股票新闻
```http
GET /api/stock-news/{ticker}?date=2025-01-21&look_back_days=7
```

#### 获取基本面分析
```http
GET /api/fundamentals/{ticker}?date=2025-01-21
```

### 分析接口

#### 开始智能体分析
```http
POST /api/analyze
Content-Type: application/json

{
    "ticker": "000001",
    "date": "2025-01-21",
    "market_type": "china",
    "selected_analysts": ["market", "news", "fundamentals", "social"],
    "research_depth": 1,
    "look_back_days": 30
}
```

### WebSocket接口

#### 实时进度监控
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};
```

## 配置说明

### 默认配置

系统默认配置位于 `tradingagents/default_config.py`:

```python
DEFAULT_CONFIG = {
    "market_type": "china",  # 市场类型
    "default_ticker": "000001",  # 默认股票代码（平安银行）
    "default_index": "000001",  # 默认指数（上证指数）
    "llm_provider": "openai",  # LLM提供商
    "deep_think_llm": "gpt-4o",  # 深度思考模型
    "quick_think_llm": "gpt-4o-mini",  # 快速思考模型
    "online_tools": True,  # 使用在线工具
}
```

### 中国股市配置

中国股市专用配置位于 `tradingagents/dataflows/config.py`:

```python
def get_china_market_config() -> Dict:
    """获取专门为中国股市优化的配置"""
    config = get_config()
    return validate_china_market_config(config)
```

## 数据源

### AKShare数据接口

系统使用AKShare作为主要数据源，支持：

- **股票数据**: 实时价格、成交量、技术指标
- **财务数据**: 资产负债表、利润表、现金流量表
- **市场数据**: 指数数据、板块数据
- **新闻数据**: 股票相关新闻、公告

### 数据缓存

系统支持数据缓存，提高查询效率：

```python
# 缓存目录配置
"data_cache_dir": "tradingagents/dataflows/data_cache"
```

## 智能体工具

### 市场分析师工具
- `get_china_stock_data_online`: 获取股票历史数据
- `get_china_technical_indicators_online`: 获取技术指标

### 新闻分析师工具
- `get_china_global_news_online`: 获取宏观新闻
- `get_china_stock_news_online`: 获取股票新闻

### 基本面分析师工具
- `get_china_fundamentals_online`: 获取基本面分析
- `get_china_financial_statements`: 获取财务报表
- `get_china_industry_analysis`: 获取行业分析

### 社交媒体分析师工具
- `get_china_market_sentiment`: 获取市场情绪分析

## 使用示例

### Python客户端示例

```python
import requests
import json

# 基础配置
base_url = "http://localhost:8000"
headers = {"Content-Type": "application/json"}

# 获取系统信息
response = requests.get(f"{base_url}/api/system-info")
system_info = response.json()
print(f"系统名称: {system_info['system_name']}")
print(f"市场类型: {system_info['market_type']}")

# 开始分析
analysis_request = {
    "ticker": "000001",
    "date": "2025-01-21",
    "selected_analysts": ["market", "news", "fundamentals"],
    "look_back_days": 30
}

response = requests.post(
    f"{base_url}/api/analyze",
    headers=headers,
    data=json.dumps(analysis_request)
)

if response.status_code == 200:
    print("分析已开始，请通过WebSocket连接获取实时进度")
else:
    print(f"启动分析失败: {response.text}")
```

### JavaScript客户端示例

```javascript
// WebSocket连接
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
    console.log('WebSocket连接已建立');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'agent_status':
            console.log(`智能体 ${data.agent} 状态: ${data.status}`);
            break;
        case 'message':
            console.log(`${data.sender}: ${data.content}`);
            break;
        case 'report_update':
            console.log(`报告更新: ${data.report_type}`);
            break;
        case 'final_decision':
            console.log(`最终决策: ${data.decision}`);
            break;
    }
};

// 开始分析
fetch('http://localhost:8000/api/analyze', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        ticker: '000001',
        date: '2025-01-21',
        selected_analysts: ['market', 'news', 'fundamentals'],
        look_back_days: 30
    })
})
.then(response => response.json())
.then(data => {
    console.log('分析结果:', data);
});
```

## 故障排除

### 常见问题

1. **数据获取失败**
   - 检查网络连接
   - 确认AKShare版本兼容性
   - 验证股票代码格式

2. **服务器启动失败**
   - 检查端口占用情况
   - 确认依赖包安装完整
   - 查看日志文件

3. **WebSocket连接失败**
   - 确认服务器正在运行
   - 检查防火墙设置
   - 验证WebSocket URL

### 日志文件

系统日志文件位置：
- 服务器日志: `backend/china_server.log`
- 分析日志: `tradingagents/logs/`

### 调试模式

启用调试模式：

```python
# 在配置中设置
config["debug"] = True

# 或在启动时设置
python main.py --debug
```

## 扩展开发

### 添加新的数据源

1. 在 `tradingagents/dataflows/` 目录下创建新的数据接口
2. 在 `tradingagents/agents/utils/china_toolkit.py` 中添加工具方法
3. 在 `tradingagents/graph/trading_graph.py` 中注册工具节点

### 添加新的智能体

1. 在 `tradingagents/agents/` 目录下创建新的智能体
2. 定义智能体的提示词和工具
3. 在分析图中集成新的智能体

### 自定义配置

1. 修改 `tradingagents/default_config.py` 中的默认配置
2. 或通过环境变量覆盖配置
3. 或在运行时动态设置配置

## 许可证

本项目基于原有TradingAgents框架开发，遵循相应的开源许可证。

## 贡献

欢迎提交Issue和Pull Request来改进中国股市适配功能。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**注意**: 本系统仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。 
