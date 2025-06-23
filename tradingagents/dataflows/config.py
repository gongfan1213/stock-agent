import tradingagents.default_config as default_config
from typing import Dict, Optional

# Use default config but allow it to be overridden
_config: Optional[Dict] = None
DATA_DIR: Optional[str] = None


def initialize_config():
    """Initialize the configuration with default values."""
    global _config, DATA_DIR
    if _config is None:
        _config = default_config.DEFAULT_CONFIG.copy()
        DATA_DIR = _config["data_dir"]


def set_config(config: Dict):
    """Update the configuration with custom values."""
    global _config, DATA_DIR
    if _config is None:
        _config = default_config.DEFAULT_CONFIG.copy()
    _config.update(config)
    DATA_DIR = _config["data_dir"]


def get_config() -> Dict:
    """Get the current configuration."""
    if _config is None:
        initialize_config()
    return _config.copy()


def validate_china_market_config(config: Dict) -> Dict:
    """
    验证和优化中国股市配置
    
    Args:
        config: 配置字典
        
    Returns:
        Dict: 验证后的配置
    """
    validated_config = config.copy()
    
    # 确保市场类型设置正确
    if validated_config.get("market_type") == "china":
        # 设置中国股市默认值
        if not validated_config.get("default_ticker"):
            validated_config["default_ticker"] = "000001"
        if not validated_config.get("default_index"):
            validated_config["default_index"] = "000001"
        
        # 确保使用正确的数据源
        validated_config["online_tools"] = True
        
        # 设置合适的模型
        if not validated_config.get("deep_think_llm"):
            validated_config["deep_think_llm"] = "gpt-4o"
        if not validated_config.get("quick_think_llm"):
            validated_config["quick_think_llm"] = "gpt-4o-mini"
    
    return validated_config


def get_china_market_config() -> Dict:
    """
    获取专门为中国股市优化的配置
    
    Returns:
        Dict: 中国股市配置
    """
    config = get_config()
    return validate_china_market_config(config)


# Initialize with default config
initialize_config()
