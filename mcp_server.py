# mcp_server.py
"""
AKShare MCP 服务器
使用 FastMCP 框架将 AKShare 接口暴露为 MCP tools
"""
from fastmcp import FastMCP
import logging
import sys

# 导入配置
from config import (
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCP_SERVER_PORT,
    LOG_LEVEL
)

# 导入工具函数
from mcp_utils import dataframe_to_mcp_result, format_error_response

# 导入 AKShare 接口
sys.path.append('.')
from akshare_api import *

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器
mcp = FastMCP(
    name=MCP_SERVER_NAME,
    instructions=f"""
AKShare 股票数据接口 MCP 服务器 v{MCP_SERVER_VERSION}

提供 133 个股票数据查询接口，包括：
- A股数据：市场总貌、实时行情、历史数据、分时数据等
- B股数据：实时行情、历史数据
- 港股数据：实时行情、历史数据
- 美股数据：实时行情、历史数据
- 高级功能：涨停板、龙虎榜、机构调研、研报资讯等

使用方法：直接调用对应的 tool，根据需要传入参数。
返回格式：JSON 格式，包含 success, rows, columns, data 字段。
"""
)

# =============================================================================
# 1. A股数据接口 - 股票市场总貌 (5个)
# =============================================================================

@mcp.tool()
def stock_sse_summary() -> dict:
    """
    获取上海证券交易所总貌数据

    Returns:
        dict: 包含上交所市场总貌信息的字典
    """
    try:
        from akshare_api import stock_sse_summary
        df = stock_sse_summary()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_sse_summary 执行失败: {e}")
        return format_error_response(e)


@mcp.tool()
def stock_szse_summary() -> dict:
    """
    获取深圳证券交易所总貌数据

    Returns:
        dict: 包含深交所市场总貌信息的字典
    """
    try:
        from akshare_api import stock_szse_summary
        df = stock_szse_summary()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_szse_summary 执行失败: {e}")
        return format_error_response(e)


@mcp.tool()
def stock_szse_area_summary() -> dict:
    """
    获取深圳证券交易所地区交易排序数据

    Returns:
        dict: 包含地区交易排序信息的字典
    """
    try:
        from akshare_api import stock_szse_area_summary
        df = stock_szse_area_summary()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_szse_area_summary 执行失败: {e}")
        return format_error_response(e)


@mcp.tool()
def stock_szse_sector_summary(symbol: str = "当年") -> dict:
    """
    获取深圳证券交易所股票行业成交数据

    Args:
        symbol: 统计周期，默认"当年"

    Returns:
        dict: 包含行业成交数据信息的字典
    """
    try:
        from akshare_api import stock_szse_sector_summary
        df = stock_szse_sector_summary(symbol=symbol)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_szse_sector_summary 执行失败: {e}")
        return format_error_response(e)


@mcp.tool()
def stock_sse_deal_daily() -> dict:
    """
    获取上海证券交易所每日概况数据

    Returns:
        dict: 包含上交所每日概况信息的字典
    """
    try:
        from akshare_api import stock_sse_deal_daily
        df = stock_sse_deal_daily()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_sse_deal_daily 执行失败: {e}")
        return format_error_response(e)


# 启动服务器
if __name__ == "__main__":
    logger.info(f"启动 {MCP_SERVER_NAME} v{MCP_SERVER_VERSION}")
    logger.info(f"监听端口: {MCP_SERVER_PORT}")
    mcp.run(transport="streamable-http", port=MCP_SERVER_PORT)
