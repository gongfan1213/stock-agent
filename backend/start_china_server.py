#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国股市智能体分析系统启动脚本
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ["MARKET_TYPE"] = "china"
os.environ["DEFAULT_TICKER"] = "000001"  # 平安银行
os.environ["DEFAULT_INDEX"] = "000001"   # 上证指数

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('china_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """启动中国股市智能体分析系统"""
    try:
        logger.info("正在启动中国股市智能体分析系统...")
        logger.info("市场类型: 中国股市")
        logger.info("默认股票代码: 000001 (平安银行)")
        logger.info("默认指数: 000001 (上证指数)")
        
        # 启动FastAPI服务器
        uvicorn.run(
            "backend.simple_main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
    except Exception as e:
        logger.error(f"启动服务器时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 