# mcp_server.py
"""
AKShare MCP 服务器
使用 FastMCP 框架将 AKShare 接口暴露为 MCP tools
"""
from fastmcp import FastMCP
import logging
import os
import re
import sys
import requests

# 导入配置
from config import (
    AKTOOLS_BASE_URL,
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCP_SERVER_PORT,
    MCP_SERVER_HOST,
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
RUNTIME_XQ_TOKEN = os.getenv("XQ_A_TOKEN", "").strip()


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "*" * len(token)
    return f"{token[:4]}...{token[-4:]}"


def _extract_xq_token_from_cookie(cookie: str) -> str | None:
    if not cookie:
        return None
    match = re.search(r"(?:^|;\s*)xq_a_token=([^;]+)", cookie)
    if not match:
        return None
    return match.group(1).strip()


def _xq_probe(symbol: str, timeout: float = 12.0, token: str | None = None) -> dict:
    params = {"symbol": symbol}
    if token:
        params["token"] = token
    url = f"{AKTOOLS_BASE_URL.rstrip('/')}/api/public/stock_individual_spot_xq"
    try:
        resp = requests.get(url, params=params, timeout=timeout)
    except Exception as e:
        return {
            "ok": False,
            "status_code": 0,
            "rows": 0,
            "message": repr(e),
            "token_used": bool(token),
        }

    body_preview = resp.text[:300]
    rows = 0
    if resp.status_code == 200:
        try:
            payload = resp.json()
            if isinstance(payload, list):
                rows = len(payload)
        except ValueError:
            pass
    return {
        "ok": resp.status_code == 200 and rows > 0,
        "status_code": resp.status_code,
        "rows": rows,
        "message": body_preview,
        "token_used": bool(token),
    }

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
# MCP Tools - 133 个 AKShare 股票数据接口
# =============================================================================


@mcp.tool()
def stock_sse_summary() -> dict:
    """
    获取上海证券交易所总貌数据
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

    参数说明:
    - symbol: str, 可选, 默认"当年"
      参数格式: 字符串类型，可选值如"当年"、"近一年"、"近三年"等时间范围描述
    """
    try:
        from akshare_api import stock_szse_sector_summary
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_szse_sector_summary(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_szse_sector_summary 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_sse_deal_daily() -> dict:
    """
    获取上海证券交易所每日概况数据
    """
    try:
        from akshare_api import stock_sse_deal_daily
        df = stock_sse_deal_daily()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_sse_deal_daily 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_individual_info_em(symbol: str) -> dict:
    """
    获取个股信息查询-东方财富

    参数说明:
    - symbol: str, 必需
      参数格式: 6位股票代码，如"000001"、"603777"
      说明: 股票代码可以在stock_zh_a_spot_em()中获取
    """
    try:
        from akshare_api import stock_individual_info_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_individual_info_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_individual_info_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_individual_basic_info_xq(symbol: str) -> dict:
    """
    获取个股信息查询-雪球

    参数说明:
    - symbol: str, 必需
      参数格式: 带市场前缀的股票代码，如"SH601127"、"SZ000001"
      说明: 市场前缀包括SH(上海)、SZ(深圳)、BJ(北京)
    """
    try:
        from akshare_api import stock_individual_basic_info_xq
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_individual_basic_info_xq(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_individual_basic_info_xq 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_bid_ask_em(symbol: str) -> dict:
    """
    获取行情报价-东方财富

    参数说明:
    - symbol: str, 必需
      参数格式: 6位股票代码，如"000001"、"603777"
    """
    try:
        from akshare_api import stock_bid_ask_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_bid_ask_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_bid_ask_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_a_spot_em() -> dict:
    """
    获取沪深京A股实时行情-东方财富
    """
    try:
        from akshare_api import stock_zh_a_spot_em
        df = stock_zh_a_spot_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_a_spot_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_sh_a_spot_em() -> dict:
    """
    获取沪A股实时行情-东方财富
    """
    try:
        from akshare_api import stock_sh_a_spot_em
        df = stock_sh_a_spot_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_sh_a_spot_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_sz_a_spot_em() -> dict:
    """
    获取深A股实时行情-东方财富
    """
    try:
        from akshare_api import stock_sz_a_spot_em
        df = stock_sz_a_spot_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_sz_a_spot_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_bj_a_spot_em() -> dict:
    """
    获取京A股实时行情-东方财富
    """
    try:
        from akshare_api import stock_bj_a_spot_em
        df = stock_bj_a_spot_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_bj_a_spot_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_new_a_spot_em() -> dict:
    """
    获取新股实时行情-东方财富
    """
    try:
        from akshare_api import stock_new_a_spot_em
        df = stock_new_a_spot_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_new_a_spot_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_cy_a_spot_em() -> dict:
    """
    获取创业板实时行情-东方财富
    """
    try:
        from akshare_api import stock_cy_a_spot_em
        df = stock_cy_a_spot_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_cy_a_spot_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_kc_a_spot_em() -> dict:
    """
    获取科创板实时行情-东方财富
    """
    try:
        from akshare_api import stock_kc_a_spot_em
        df = stock_kc_a_spot_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_kc_a_spot_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_ab_comparison_em() -> dict:
    """
    获取AB股比价-东方财富
    """
    try:
        from akshare_api import stock_zh_ab_comparison_em
        df = stock_zh_ab_comparison_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_ab_comparison_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_a_spot() -> dict:
    """
    获取沪深京A股实时行情-新浪
    """
    try:
        from akshare_api import stock_zh_a_spot
        df = stock_zh_a_spot()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_a_spot 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_individual_spot_xq(symbol: str, token: str = None) -> dict:
    """
    获取个股实时行情-雪球

    参数说明:
    - symbol: str, 必需
      参数格式: 带市场前缀的股票代码，如"SH600000"、"SZ000001"
      说明: 市场前缀包括SH(上海)、SZ(深圳)、BJ(北京)
    """
    try:
        from akshare_api import stock_individual_spot_xq
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        effective_token = token if token else RUNTIME_XQ_TOKEN
        if effective_token:
            kwargs["token"] = effective_token
        df = stock_individual_spot_xq(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_individual_spot_xq 执行失败: {e}")
        return format_error_response(e)


@mcp.tool()
def xq_token_health_check(symbol: str = "SH600000", timeout: float = 12.0) -> dict:
    """
    手动检测雪球 token 是否可用

    参数说明:
    - symbol: str, 可选, 默认"SH600000"
      参数格式: 带市场前缀的股票代码，如"SH600000"
    - timeout: float, 可选, 默认12.0
      参数格式: 请求超时秒数
    """
    try:
        no_token_result = _xq_probe(symbol=symbol, timeout=timeout, token=None)
        runtime_result = None
        if RUNTIME_XQ_TOKEN:
            runtime_result = _xq_probe(symbol=symbol, timeout=timeout, token=RUNTIME_XQ_TOKEN)

        current_ok = runtime_result["ok"] if runtime_result is not None else no_token_result["ok"]
        message = "runtime token healthy" if current_ok else "token may be expired or invalid"
        return {
            "success": current_ok,
            "message": message,
            "rows": 1 if current_ok else 0,
            "columns": ["probe", "status_code", "rows", "ok", "token_used"],
            "data": [
                {"probe": "without_runtime_token", **no_token_result},
                *([{"probe": "with_runtime_token", **runtime_result}] if runtime_result else []),
            ],
            "runtime_token_set": bool(RUNTIME_XQ_TOKEN),
            "runtime_token_masked": _mask_token(RUNTIME_XQ_TOKEN) if RUNTIME_XQ_TOKEN else "",
        }
    except Exception as e:
        logger.error(f"xq_token_health_check 执行失败: {e}")
        return format_error_response(e)


@mcp.tool()
def xq_token_update(token: str = "", cookie: str = "", verify_symbol: str = "SH600000", timeout: float = 12.0) -> dict:
    """
    手动更新运行时雪球 token（仅作用于当前 mcp 进程）

    参数说明:
    - token: str, 可选
      参数格式: xq_a_token 字符串
    - cookie: str, 可选
      参数格式: 完整 Cookie 字符串，工具会自动提取 xq_a_token
    - verify_symbol: str, 可选, 默认"SH600000"
      参数格式: 验证用股票代码
    - timeout: float, 可选, 默认12.0
      参数格式: 请求超时秒数
    """
    global RUNTIME_XQ_TOKEN
    try:
        new_token = token.strip() if token else ""
        if not new_token and cookie:
            extracted = _extract_xq_token_from_cookie(cookie)
            if extracted:
                new_token = extracted
        if not new_token:
            return {
                "success": False,
                "message": "未提供有效 token，请传 token 或包含 xq_a_token 的 cookie",
                "rows": 0,
                "columns": [],
                "data": [],
            }

        RUNTIME_XQ_TOKEN = new_token
        verify_result = _xq_probe(symbol=verify_symbol, timeout=timeout, token=RUNTIME_XQ_TOKEN)
        return {
            "success": verify_result["ok"],
            "message": "runtime token updated",
            "rows": 1 if verify_result["ok"] else 0,
            "columns": ["symbol", "status_code", "rows", "ok"],
            "data": [
                {
                    "symbol": verify_symbol,
                    "status_code": verify_result["status_code"],
                    "rows": verify_result["rows"],
                    "ok": verify_result["ok"],
                }
            ],
            "runtime_token_masked": _mask_token(RUNTIME_XQ_TOKEN),
            "verify_preview": verify_result["message"],
        }
    except Exception as e:
        logger.error(f"xq_token_update 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_a_hist(symbol: str, period: str = "daily", start_date: str = "20210301", end_date: str = "20210616", adjust: str = "", timeout: str = None) -> dict:
    """
    获取历史行情数据-东方财富

    参数说明:
    - symbol: str, 必需
      参数格式: 6位股票代码，如"000001"、"603777"

    - period: str, 可选, 默认"daily"
      参数格式: 字符串类型，可选值: "daily"(日线)、"weekly"(周线)、"monthly"(月线)

    - start_date: str, 可选, 默认"20210301"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20210301"

    - end_date: str, 可选, 默认"20210616"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20210616"

    - adjust: str, 可选, 默认""(不复权)
      参数格式: 字符串类型
      可选值:
      - "": 不复权(默认)
      - "qfq": 前复权
      - "hfq": 后复权

    - timeout: str, 可选, 默认None
      参数格式: 浮点数，单位为秒
      说明: 默认不设置超时参数
    """
    try:
        from akshare_api import stock_zh_a_hist
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if period is not None:
            kwargs["period"] = period
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        if timeout is not None:
            kwargs["timeout"] = timeout
        df = stock_zh_a_hist(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_a_hist 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_a_daily(symbol: str, start_date: str = "20201103", end_date: str = "20201116", adjust: str = "") -> dict:
    """
    获取历史行情数据-新浪

    参数说明:
    - symbol: str, 必需
      参数格式: 带市场前缀的股票代码，如"sh600000"、"sz000001"

    - start_date: str, 可选, 默认"20201103"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20201103"

    - end_date: str, 可选, 默认"20201116"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20201116"

    - adjust: str, 可选, 默认""(不复权)
      参数格式: 字符串类型
      可选值:
      - "": 不复权(默认)
      - "qfq": 前复权
      - "hfq": 后复权
      - "qfq-factor": 前复权因子
      - "hfq-factor": 后复权因子
    """
    try:
        from akshare_api import stock_zh_a_daily
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_zh_a_daily(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_a_daily 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_a_hist_tx(symbol: str, start_date: str = "20201103", end_date: str = "20201116", adjust: str = "") -> dict:
    """
    获取历史行情数据-腾讯
    """
    try:
        from akshare_api import stock_zh_a_hist_tx
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_zh_a_hist_tx(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_a_hist_tx 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_a_minute(symbol: str, period: str = "1", adjust: str = "") -> dict:
    """
    获取分时数据-新浪

    参数说明:
    - symbol: str, 必需
      参数格式: 带市场前缀的股票代码，如"sh600519"、"sz000001"

    - period: str, 可选, 默认"1"
      参数格式: 数字字符串，表示分钟间隔
      可选值: "1"(1分钟)、"5"(5分钟)、"15"(15分钟)、"30"(30分钟)、"60"(60分钟)

    - adjust: str, 可选, 默认""(不复权)
      参数格式: 字符串类型
      可选值: ""(不复权)、"qfq"(前复权)
    """
    try:
        from akshare_api import stock_zh_a_minute
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if period is not None:
            kwargs["period"] = period
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_zh_a_minute(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_a_minute 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_a_hist_min_em(symbol: str, period: str = "1", start_date: str = "2021-09-01 09:30:00", end_date: str = "2021-09-01 15:00:00", adjust: str = "") -> dict:
    """
    获取分时数据-东方财富

    参数说明:
    - symbol: str, 必需
      参数格式: 6位股票代码，如"000001"、"603777"

    - period: str, 可选, 默认"1"
      参数格式: 数字字符串，表示分钟间隔
      可选值: "1"(1分钟)、"5"(5分钟)、"15"(15分钟)、"30"(30分钟)、"60"(60分钟)

    - start_date: str, 可选, 默认"2021-09-01 09:30:00"
      参数格式: 日期时间字符串，格式"YYYY-MM-DD HH:MM:SS"，如"2021-09-01 09:30:00"

    - end_date: str, 可选, 默认"2021-09-01 15:00:00"
      参数格式: 日期时间字符串，格式"YYYY-MM-DD HH:MM:SS"，如"2021-09-01 15:00:00"

    - adjust: str, 可选, 默认""(不复权)
      参数格式: 字符串类型
      可选值: ""(不复权)、"qfq"(前复权)
    """
    try:
        from akshare_api import stock_zh_a_hist_min_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if period is not None:
            kwargs["period"] = period
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_zh_a_hist_min_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_a_hist_min_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_intraday_em(symbol: str) -> dict:
    """
    获取日内分时数据-东方财富
    """
    try:
        from akshare_api import stock_intraday_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_intraday_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_intraday_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_intraday_sina(symbol: str) -> dict:
    """
    获取日内分时数据-新浪
    """
    try:
        from akshare_api import stock_intraday_sina
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_intraday_sina(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_intraday_sina 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_a_hist_pre_min_em(symbol: str) -> dict:
    """
    获取盘前数据-东方财富
    """
    try:
        from akshare_api import stock_zh_a_hist_pre_min_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_zh_a_hist_pre_min_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_a_hist_pre_min_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_a_tick_tx(symbol: str, trade_date: str = "20210316") -> dict:
    """
    获取历史分笔数据-腾讯

    参数说明:
    - symbol: str, 必需
      参数格式: 带市场前缀的股票代码，如"sh600519"、"sz000001"

    - trade_date: str, 可选, 默认"20210316"
      参数格式: 8位数字字符串，格式YYYYMMDD，表示交易日期，如"20210316"
    """
    try:
        from akshare_api import stock_zh_a_tick_tx
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if trade_date is not None:
            kwargs["trade_date"] = trade_date
        df = stock_zh_a_tick_tx(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_a_tick_tx 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_growth_comparison_em(symbol: str) -> dict:
    """
    获取股票成长性比较-东方财富
    """
    try:
        from akshare_api import stock_zh_growth_comparison_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_zh_growth_comparison_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_growth_comparison_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_valuation_comparison_em(symbol: str) -> dict:
    """
    获取股票估值比较-东方财富
    """
    try:
        from akshare_api import stock_zh_valuation_comparison_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_zh_valuation_comparison_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_valuation_comparison_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_dupont_comparison_em(symbol: str) -> dict:
    """
    获取股票杜邦分析比较-东方财富
    """
    try:
        from akshare_api import stock_zh_dupont_comparison_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_zh_dupont_comparison_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_dupont_comparison_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_scale_comparison_em(symbol: str) -> dict:
    """
    获取股票规模比较-东方财富
    """
    try:
        from akshare_api import stock_zh_scale_comparison_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_zh_scale_comparison_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_scale_comparison_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_a_cdr_daily(symbol: str, start_date: str = "20201103", end_date: str = "20201116", adjust: str = "") -> dict:
    """
    获取CDR历史数据-新浪
    """
    try:
        from akshare_api import stock_zh_a_cdr_daily
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_zh_a_cdr_daily(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_a_cdr_daily 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_financial_abstract(symbol: str) -> dict:
    """
    获取财务报表数据
    """
    try:
        from akshare_api import stock_financial_abstract
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_financial_abstract(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_financial_abstract 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_financial_analysis_indicator(symbol: str) -> dict:
    """
    获取财务指标数据
    """
    try:
        from akshare_api import stock_financial_analysis_indicator
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_financial_analysis_indicator(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_financial_analysis_indicator 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_yjbb_em(date: str = "20220331") -> dict:
    """
    获取业绩报表数据

    参数说明:
    - date: str, 可选, 默认"20220331"
      参数格式: 8位数字字符串，格式YYYYMMDD，通常为季度末日期
      常用值: "20220331"(一季度)、"20220630"(二季度)、"20220930"(三季度)、"20221231"(四季度)
    """
    try:
        from akshare_api import stock_yjbb_em
        # 构建参数字典
        kwargs = {}
        if date is not None:
            kwargs["date"] = date
        df = stock_yjbb_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_yjbb_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hsgt_fund_flow_summary_em() -> dict:
    """
    获取沪深港通资金流向
    """
    try:
        from akshare_api import stock_hsgt_fund_flow_summary_em
        df = stock_hsgt_fund_flow_summary_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hsgt_fund_flow_summary_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_individual_fund_flow_rank() -> dict:
    """
    获取个股资金流向
    """
    try:
        from akshare_api import stock_individual_fund_flow_rank
        df = stock_individual_fund_flow_rank()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_individual_fund_flow_rank 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_profit_forecast_em() -> dict:
    """
    获取东方财富盈利预测
    """
    try:
        from akshare_api import stock_profit_forecast_em
        df = stock_profit_forecast_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_profit_forecast_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_profit_forecast_ths() -> dict:
    """
    获取同花顺盈利预测
    """
    try:
        from akshare_api import stock_profit_forecast_ths
        df = stock_profit_forecast_ths()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_profit_forecast_ths 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_concept_cons_ths() -> dict:
    """
    获取同花顺概念板块指数
    """
    try:
        from akshare_api import stock_board_concept_cons_ths
        df = stock_board_concept_cons_ths()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_concept_cons_ths 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_concept_name_em() -> dict:
    """
    获取东方财富概念板块
    """
    try:
        from akshare_api import stock_board_concept_name_em
        df = stock_board_concept_name_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_concept_name_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_concept_hist_em(symbol: str, period: str = "daily", start_date: str = "20220101", end_date: str = "20250227", adjust: str = "") -> dict:
    """
    获取概念板块历史行情

    参数说明:
    - symbol: str, 必需
      参数格式: 概念板块名称或代码，如"新能源汽车"、"人工智能"
      说明: 可以从stock_board_concept_name_em()获取板块列表

    - period: str, 可选, 默认"daily"
      参数格式: 字符串类型
      可选值: "daily"(日线)、"weekly"(周线)、"monthly"(月线)

    - start_date: str, 可选, 默认"20220101"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20220101"

    - end_date: str, 可选, 默认"20250227"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20250227"

    - adjust: str, 可选, 默认""(不复权)
      参数格式: 字符串类型
      可选值: ""(不复权)、"qfq"(前复权)
    """
    try:
        from akshare_api import stock_board_concept_hist_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if period is not None:
            kwargs["period"] = period
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_board_concept_hist_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_concept_hist_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_industry_name_ths() -> dict:
    """
    获取同花顺行业一览表
    """
    try:
        from akshare_api import stock_board_industry_name_ths
        df = stock_board_industry_name_ths()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_industry_name_ths 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_industry_name_em() -> dict:
    """
    获取东方财富行业板块
    """
    try:
        from akshare_api import stock_board_industry_name_em
        df = stock_board_industry_name_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_industry_name_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hot_rank_em() -> dict:
    """
    获取股票热度排行
    """
    try:
        from akshare_api import stock_hot_rank_em
        df = stock_hot_rank_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_rank_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_market_activity_em() -> dict:
    """
    获取盘口异动数据
    """
    try:
        from akshare_api import stock_market_activity_em
        df = stock_market_activity_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_market_activity_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_change_em() -> dict:
    """
    获取板块异动详情
    """
    try:
        from akshare_api import stock_board_change_em
        df = stock_board_change_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_change_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zt_pool_em() -> dict:
    """
    获取涨停股池
    """
    try:
        from akshare_api import stock_zt_pool_em
        df = stock_zt_pool_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zt_pool_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zt_pool_previous_em() -> dict:
    """
    获取昨日涨停股池
    """
    try:
        from akshare_api import stock_zt_pool_previous_em
        df = stock_zt_pool_previous_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zt_pool_previous_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_dt_pool_em() -> dict:
    """
    获取跌停股池
    """
    try:
        from akshare_api import stock_dt_pool_em
        df = stock_dt_pool_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_dt_pool_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_lhb_detail_em(start_date: str = "20230403", end_date: str = "20230417") -> dict:
    """
    获取龙虎榜详情

    参数说明:
    - start_date: str, 可选, 默认"20230403"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20230403"

    - end_date: str, 可选, 默认"20230417"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20230417"
    """
    try:
        from akshare_api import stock_lhb_detail_em
        # 构建参数字典
        kwargs = {}
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        df = stock_lhb_detail_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_lhb_detail_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_lhb_stock_statistic_em() -> dict:
    """
    获取个股上榜统计
    """
    try:
        from akshare_api import stock_lhb_stock_statistic_em
        df = stock_lhb_stock_statistic_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_lhb_stock_statistic_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_institute_visit_em() -> dict:
    """
    获取机构调研统计
    """
    try:
        from akshare_api import stock_institute_visit_em
        df = stock_institute_visit_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_institute_visit_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_institute_visit_detail_em() -> dict:
    """
    获取机构调研详细
    """
    try:
        from akshare_api import stock_institute_visit_detail_em
        df = stock_institute_visit_detail_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_institute_visit_detail_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_institute_hold_detail(stock: str, quarter: str) -> dict:
    """
    获取机构持股详情

    参数说明:
    - stock: str, 必需
      参数格式: 6位股票代码，如"000001"、"603777"

    - quarter: str, 必需
      参数格式: 季度字符串，格式"YYYYQ季度"
      常用值: "2024Q1"(2024年一季度)、"2024Q2"(2024年二季度)、"2024Q3"(2024年三季度)、"2024Q4"(2024年四季度)
    """
    try:
        from akshare_api import stock_institute_hold_detail
        # 构建参数字典
        kwargs = {}
        if stock is not None:
            kwargs["stock"] = stock
        if quarter is not None:
            kwargs["quarter"] = quarter
        df = stock_institute_hold_detail(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_institute_hold_detail 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_institute_recommend(symbol: str) -> dict:
    """
    获取机构推荐池
    """
    try:
        from akshare_api import stock_institute_recommend
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_institute_recommend(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_institute_recommend 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_institute_recommend_detail(symbol: str) -> dict:
    """
    获取股票评级记录
    """
    try:
        from akshare_api import stock_institute_recommend_detail
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_institute_recommend_detail(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_institute_recommend_detail 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_research_report_em(symbol: str) -> dict:
    """
    获取个股研报
    """
    try:
        from akshare_api import stock_research_report_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_research_report_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_research_report_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_info_cjzc_em() -> dict:
    """
    获取财经早餐
    """
    try:
        from akshare_api import stock_info_cjzc_em
        df = stock_info_cjzc_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_info_cjzc_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_info_global_em() -> dict:
    """
    获取全球财经快讯-东方财富
    """
    try:
        from akshare_api import stock_info_global_em
        df = stock_info_global_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_info_global_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_info_global_sina() -> dict:
    """
    获取全球财经快讯-新浪财经
    """
    try:
        from akshare_api import stock_info_global_sina
        df = stock_info_global_sina()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_info_global_sina 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_irm_cninfo(symbol: str) -> dict:
    """
    获取互动易-提问
    """
    try:
        from akshare_api import stock_irm_cninfo
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_irm_cninfo(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_irm_cninfo 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_irm_ans_cninfo(symbol: str) -> dict:
    """
    获取互动易-回答
    """
    try:
        from akshare_api import stock_irm_ans_cninfo
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_irm_ans_cninfo(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_irm_ans_cninfo 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_sns_sseinfo(symbol: str) -> dict:
    """
    获取上证e互动
    """
    try:
        from akshare_api import stock_sns_sseinfo
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_sns_sseinfo(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_sns_sseinfo 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_b_spot_em() -> dict:
    """
    获取B股实时行情-东方财富
    """
    try:
        from akshare_api import stock_zh_b_spot_em
        df = stock_zh_b_spot_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_b_spot_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_b_spot() -> dict:
    """
    获取B股实时行情-新浪
    """
    try:
        from akshare_api import stock_zh_b_spot
        df = stock_zh_b_spot()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_b_spot 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_b_daily(symbol: str, start_date: str = "20201103", end_date: str = "20201116", adjust: str = "") -> dict:
    """
    获取B股历史行情数据-新浪
    """
    try:
        from akshare_api import stock_zh_b_daily
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_zh_b_daily(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_b_daily 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_b_minute(symbol: str, period: str = "1", adjust: str = "") -> dict:
    """
    获取B股分时数据-新浪
    """
    try:
        from akshare_api import stock_zh_b_minute
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if period is not None:
            kwargs["period"] = period
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_zh_b_minute(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_b_minute 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hk_spot_em() -> dict:
    """
    获取港股实时行情-东方财富
    """
    try:
        from akshare_api import stock_hk_spot_em
        df = stock_hk_spot_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hk_spot_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hk_spot() -> dict:
    """
    获取港股实时行情-新浪
    """
    try:
        from akshare_api import stock_hk_spot
        df = stock_hk_spot()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hk_spot 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hk_daily(symbol: str, start_date: str = "20201103", end_date: str = "20201116", adjust: str = "") -> dict:
    """
    获取港股历史行情数据-新浪
    """
    try:
        from akshare_api import stock_hk_daily
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_hk_daily(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hk_daily 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_us_spot() -> dict:
    """
    获取美股实时行情-新浪
    """
    try:
        from akshare_api import stock_us_spot
        df = stock_us_spot()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_us_spot 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_us_spot_em() -> dict:
    """
    获取美股实时行情-东方财富
    """
    try:
        from akshare_api import stock_us_spot_em
        df = stock_us_spot_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_us_spot_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_us_daily(symbol: str, start_date: str = "20201103", end_date: str = "20201116", adjust: str = "") -> dict:
    """
    获取美股历史行情数据-新浪
    """
    try:
        from akshare_api import stock_us_daily
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_us_daily(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_us_daily 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_growth_comparison_em(symbol: str) -> dict:
    """
    获取股票成长性比较-东方财富
    """
    try:
        from akshare_api import stock_zh_growth_comparison_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_zh_growth_comparison_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_growth_comparison_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_valuation_comparison_em(symbol: str) -> dict:
    """
    获取股票估值比较-东方财富
    """
    try:
        from akshare_api import stock_zh_valuation_comparison_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_zh_valuation_comparison_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_valuation_comparison_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_dupont_comparison_em(symbol: str) -> dict:
    """
    获取股票杜邦分析比较-东方财富
    """
    try:
        from akshare_api import stock_zh_dupont_comparison_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_zh_dupont_comparison_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_dupont_comparison_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_scale_comparison_em(symbol: str) -> dict:
    """
    获取股票规模比较-东方财富
    """
    try:
        from akshare_api import stock_zh_scale_comparison_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_zh_scale_comparison_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_scale_comparison_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zh_a_cdr_daily(symbol: str, start_date: str = "20201103", end_date: str = "20201116", adjust: str = "") -> dict:
    """
    获取CDR历史数据-新浪
    """
    try:
        from akshare_api import stock_zh_a_cdr_daily
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_zh_a_cdr_daily(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_a_cdr_daily 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_financial_abstract(symbol: str) -> dict:
    """
    获取财务报表数据
    """
    try:
        from akshare_api import stock_financial_abstract
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_financial_abstract(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_financial_abstract 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_financial_analysis_indicator(symbol: str) -> dict:
    """
    获取财务指标数据
    """
    try:
        from akshare_api import stock_financial_analysis_indicator
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_financial_analysis_indicator(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_financial_analysis_indicator 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_yjbb_em(date: str = "20220331") -> dict:
    """
    获取业绩报表数据

    参数说明:
    - date: str, 可选, 默认"20220331"
      参数格式: 8位数字字符串，格式YYYYMMDD，通常为季度末日期
      常用值: "20220331"(一季度)、"20220630"(二季度)、"20220930"(三季度)、"20221231"(四季度)
    """
    try:
        from akshare_api import stock_yjbb_em
        # 构建参数字典
        kwargs = {}
        if date is not None:
            kwargs["date"] = date
        df = stock_yjbb_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_yjbb_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hsgt_fund_flow_summary_em() -> dict:
    """
    获取沪深港通资金流向
    """
    try:
        from akshare_api import stock_hsgt_fund_flow_summary_em
        df = stock_hsgt_fund_flow_summary_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hsgt_fund_flow_summary_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_individual_fund_flow_rank() -> dict:
    """
    获取个股资金流向
    """
    try:
        from akshare_api import stock_individual_fund_flow_rank
        df = stock_individual_fund_flow_rank()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_individual_fund_flow_rank 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_profit_forecast_em() -> dict:
    """
    获取东方财富盈利预测
    """
    try:
        from akshare_api import stock_profit_forecast_em
        df = stock_profit_forecast_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_profit_forecast_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_profit_forecast_ths() -> dict:
    """
    获取同花顺盈利预测
    """
    try:
        from akshare_api import stock_profit_forecast_ths
        df = stock_profit_forecast_ths()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_profit_forecast_ths 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_concept_cons_ths() -> dict:
    """
    获取同花顺概念板块指数
    """
    try:
        from akshare_api import stock_board_concept_cons_ths
        df = stock_board_concept_cons_ths()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_concept_cons_ths 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_concept_name_em() -> dict:
    """
    获取东方财富概念板块
    """
    try:
        from akshare_api import stock_board_concept_name_em
        df = stock_board_concept_name_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_concept_name_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_concept_hist_em(symbol: str, period: str = "daily", start_date: str = "20220101", end_date: str = "20250227", adjust: str = "") -> dict:
    """
    获取概念板块历史行情

    参数说明:
    - symbol: str, 必需
      参数格式: 概念板块名称或代码，如"新能源汽车"、"人工智能"
      说明: 可以从stock_board_concept_name_em()获取板块列表

    - period: str, 可选, 默认"daily"
      参数格式: 字符串类型
      可选值: "daily"(日线)、"weekly"(周线)、"monthly"(月线)

    - start_date: str, 可选, 默认"20220101"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20220101"

    - end_date: str, 可选, 默认"20250227"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20250227"

    - adjust: str, 可选, 默认""(不复权)
      参数格式: 字符串类型
      可选值: ""(不复权)、"qfq"(前复权)
    """
    try:
        from akshare_api import stock_board_concept_hist_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if period is not None:
            kwargs["period"] = period
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_board_concept_hist_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_concept_hist_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_industry_name_ths() -> dict:
    """
    获取同花顺行业一览表
    """
    try:
        from akshare_api import stock_board_industry_name_ths
        df = stock_board_industry_name_ths()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_industry_name_ths 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_industry_name_em() -> dict:
    """
    获取东方财富行业板块
    """
    try:
        from akshare_api import stock_board_industry_name_em
        df = stock_board_industry_name_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_industry_name_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hot_rank_em() -> dict:
    """
    获取股票热度排行
    """
    try:
        from akshare_api import stock_hot_rank_em
        df = stock_hot_rank_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_rank_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_market_activity_em() -> dict:
    """
    获取盘口异动数据
    """
    try:
        from akshare_api import stock_market_activity_em
        df = stock_market_activity_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_market_activity_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_change_em() -> dict:
    """
    获取板块异动详情
    """
    try:
        from akshare_api import stock_board_change_em
        df = stock_board_change_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_change_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zt_pool_em() -> dict:
    """
    获取涨停股池
    """
    try:
        from akshare_api import stock_zt_pool_em
        df = stock_zt_pool_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zt_pool_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zt_pool_previous_em() -> dict:
    """
    获取昨日涨停股池
    """
    try:
        from akshare_api import stock_zt_pool_previous_em
        df = stock_zt_pool_previous_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zt_pool_previous_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_dt_pool_em() -> dict:
    """
    获取跌停股池
    """
    try:
        from akshare_api import stock_dt_pool_em
        df = stock_dt_pool_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_dt_pool_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_lhb_detail_em(start_date: str = "20230403", end_date: str = "20230417") -> dict:
    """
    获取龙虎榜详情

    参数说明:
    - start_date: str, 可选, 默认"20230403"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20230403"

    - end_date: str, 可选, 默认"20230417"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20230417"
    """
    try:
        from akshare_api import stock_lhb_detail_em
        # 构建参数字典
        kwargs = {}
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        df = stock_lhb_detail_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_lhb_detail_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_lhb_stock_statistic_em() -> dict:
    """
    获取个股上榜统计
    """
    try:
        from akshare_api import stock_lhb_stock_statistic_em
        df = stock_lhb_stock_statistic_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_lhb_stock_statistic_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_institute_visit_em() -> dict:
    """
    获取机构调研统计
    """
    try:
        from akshare_api import stock_institute_visit_em
        df = stock_institute_visit_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_institute_visit_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_institute_visit_detail_em() -> dict:
    """
    获取机构调研详细
    """
    try:
        from akshare_api import stock_institute_visit_detail_em
        df = stock_institute_visit_detail_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_institute_visit_detail_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_institute_hold_detail(stock: str, quarter: str) -> dict:
    """
    获取机构持股详情

    参数说明:
    - stock: str, 必需
      参数格式: 6位股票代码，如"000001"、"603777"

    - quarter: str, 必需
      参数格式: 季度字符串，格式"YYYYQ季度"
      常用值: "2024Q1"(2024年一季度)、"2024Q2"(2024年二季度)、"2024Q3"(2024年三季度)、"2024Q4"(2024年四季度)
    """
    try:
        from akshare_api import stock_institute_hold_detail
        # 构建参数字典
        kwargs = {}
        if stock is not None:
            kwargs["stock"] = stock
        if quarter is not None:
            kwargs["quarter"] = quarter
        df = stock_institute_hold_detail(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_institute_hold_detail 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_institute_recommend(symbol: str) -> dict:
    """
    获取机构推荐池
    """
    try:
        from akshare_api import stock_institute_recommend
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_institute_recommend(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_institute_recommend 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_institute_recommend_detail(symbol: str) -> dict:
    """
    获取股票评级记录
    """
    try:
        from akshare_api import stock_institute_recommend_detail
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_institute_recommend_detail(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_institute_recommend_detail 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_research_report_em(symbol: str) -> dict:
    """
    获取个股研报
    """
    try:
        from akshare_api import stock_research_report_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_research_report_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_research_report_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_info_cjzc_em() -> dict:
    """
    获取财经早餐
    """
    try:
        from akshare_api import stock_info_cjzc_em
        df = stock_info_cjzc_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_info_cjzc_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_info_global_em() -> dict:
    """
    获取全球财经快讯-东方财富
    """
    try:
        from akshare_api import stock_info_global_em
        df = stock_info_global_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_info_global_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_info_global_sina() -> dict:
    """
    获取全球财经快讯-新浪财经
    """
    try:
        from akshare_api import stock_info_global_sina
        df = stock_info_global_sina()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_info_global_sina 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_irm_cninfo(symbol: str) -> dict:
    """
    获取互动易-提问
    """
    try:
        from akshare_api import stock_irm_cninfo
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_irm_cninfo(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_irm_cninfo 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_irm_ans_cninfo(symbol: str) -> dict:
    """
    获取互动易-回答
    """
    try:
        from akshare_api import stock_irm_ans_cninfo
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_irm_ans_cninfo(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_irm_ans_cninfo 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_sns_sseinfo(symbol: str) -> dict:
    """
    获取上证e互动
    """
    try:
        from akshare_api import stock_sns_sseinfo
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_sns_sseinfo(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_sns_sseinfo 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_market_activity_em() -> dict:
    """
    获取赚钱效应分析
    """
    try:
        from akshare_api import stock_market_activity_em
        df = stock_market_activity_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_market_activity_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zyjs_ths(symbol: str) -> dict:
    """
    获取主营介绍-同花顺
    """
    try:
        from akshare_api import stock_zyjs_ths
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_zyjs_ths(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zyjs_ths 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_zygc_em(symbol: str) -> dict:
    """
    获取主营构成-东方财富
    """
    try:
        from akshare_api import stock_zygc_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_zygc_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zygc_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_gsrl_gsdt_em(date: str) -> dict:
    """
    获取公司动态-东方财富

    参数说明:
    - date: str, 必需
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20240315"
    """
    try:
        from akshare_api import stock_gsrl_gsdt_em
        # 构建参数字典
        kwargs = {}
        if date is not None:
            kwargs["date"] = date
        df = stock_gsrl_gsdt_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_gsrl_gsdt_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_dividend_cninfo(symbol: str) -> dict:
    """
    获取历史分红-巨潮资讯
    """
    try:
        from akshare_api import stock_dividend_cninfo
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_dividend_cninfo(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_dividend_cninfo 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_news_em(symbol: str) -> dict:
    """
    获取个股新闻-东方财富
    """
    try:
        from akshare_api import stock_news_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_news_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_news_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_news_main_cx() -> dict:
    """
    获取财经内容精选-财新网
    """
    try:
        from akshare_api import stock_news_main_cx
        df = stock_news_main_cx()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_news_main_cx 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_financial_report_sina(stock: str, indicator: str) -> dict:
    """
    获取财务报表-新浪

    参数说明:
    - stock: str, 必需
      参数格式: 带市场前缀的股票代码，如"sh600519"、"sz000001"

    - indicator: str, 必需
      参数格式: 财务指标类型
      可选值: "利润表"、"资产负债表"、"现金流量表"
    """
    try:
        from akshare_api import stock_financial_report_sina
        # 构建参数字典
        kwargs = {}
        if stock is not None:
            kwargs["stock"] = stock
        if indicator is not None:
            kwargs["indicator"] = indicator
        df = stock_financial_report_sina(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_financial_report_sina 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_yjkb_em(date: str) -> dict:
    """
    获取业绩快报-东方财富

    参数说明:
    - date: str, 必需
      参数格式: 8位数字字符串，格式YYYYMMDD，通常为季度末日期
      常用值: "20240331"(一季度)、"20240630"(二季度)、"20240930"(三季度)、"20241231"(四季度)
    """
    try:
        from akshare_api import stock_yjkb_em
        # 构建参数字典
        kwargs = {}
        if date is not None:
            kwargs["date"] = date
        df = stock_yjkb_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_yjkb_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_yjyg_em(date: str) -> dict:
    """
    获取业绩预告-东方财富

    参数说明:
    - date: str, 必需
      参数格式: 8位数字字符串，格式YYYYMMDD，通常为季度末日期
      常用值: "20240331"(一季度)、"20240630"(二季度)、"20240930"(三季度)、"20241231"(四季度)
    """
    try:
        from akshare_api import stock_yjyg_em
        # 构建参数字典
        kwargs = {}
        if date is not None:
            kwargs["date"] = date
        df = stock_yjyg_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_yjyg_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_yysj_em(symbol: str, date: str) -> dict:
    """
    获取预约披露时间-东方财富

    参数说明:
    - symbol: str, 必需
      参数格式: 6位股票代码，如"000001"、"603777"

    - date: str, 必需
      参数格式: 8位数字字符串，格式YYYYMMDD，通常为季度末日期
      常用值: "20240331"(一季度)、"20240630"(二季度)、"20240930"(三季度)、"20241231"(四季度)
    """
    try:
        from akshare_api import stock_yysj_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if date is not None:
            kwargs["date"] = date
        df = stock_yysj_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_yysj_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_concept_cons_em(symbol: str) -> dict:
    """
    获取概念板块成分股-东方财富

    参数说明:
    - symbol: str, 必需
      参数格式: 概念板块名称或代码，如"新能源汽车"、"人工智能"
      说明: 可以从stock_board_concept_name_em()获取板块列表
    """
    try:
        from akshare_api import stock_board_concept_cons_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_board_concept_cons_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_concept_cons_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_concept_hist_em(symbol: str, period: str = "daily", start_date: str = "20220101", end_date: str = "20250227", adjust: str = "") -> dict:
    """
    获取概念板块指数-东方财富
    """
    try:
        from akshare_api import stock_board_concept_hist_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if period is not None:
            kwargs["period"] = period
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_board_concept_hist_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_concept_hist_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_industry_cons_em(symbol: str) -> dict:
    """
    获取行业板块成分股-东方财富

    参数说明:
    - symbol: str, 必需
      参数格式: 行业板块名称或代码，如"银行"、"医药生物"
      说明: 可以从stock_board_industry_name_em()获取板块列表
    """
    try:
        from akshare_api import stock_board_industry_cons_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_board_industry_cons_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_industry_cons_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_board_industry_hist_em(symbol: str, period: str = "daily", start_date: str = "20220101", end_date: str = "20250227", adjust: str = "") -> dict:
    """
    获取行业板块指数-东方财富

    参数说明:
    - symbol: str, 必需
      参数格式: 行业板块名称或代码，如"银行"、"医药生物"
      说明: 可以从stock_board_industry_name_em()获取板块列表

    - period: str, 可选, 默认"daily"
      参数格式: 字符串类型
      可选值: "daily"(日线)、"weekly"(周线)、"monthly"(月线)

    - start_date: str, 可选, 默认"20220101"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20220101"

    - end_date: str, 可选, 默认"20250227"
      参数格式: 8位数字字符串，格式YYYYMMDD，如"20250227"

    - adjust: str, 可选, 默认""(不复权)
      参数格式: 字符串类型
      可选值: ""(不复权)、"qfq"(前复权)
    """
    try:
        from akshare_api import stock_board_industry_hist_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if period is not None:
            kwargs["period"] = period
        if start_date is not None:
            kwargs["start_date"] = start_date
        if end_date is not None:
            kwargs["end_date"] = end_date
        if adjust is not None:
            kwargs["adjust"] = adjust
        df = stock_board_industry_hist_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_board_industry_hist_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hot_follow_xq(symbol: str) -> dict:
    """
    获取股票热度-雪球关注排行榜

    参数说明:
    - symbol: str, 必需
      参数格式: 带市场前缀的股票代码，如"SH600000"、"SZ000001"
      说明: 市场前缀包括SH(上海)、SZ(深圳)、BJ(北京)
    """
    try:
        from akshare_api import stock_hot_follow_xq
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_hot_follow_xq(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_follow_xq 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hot_rank_detail_em(symbol: str) -> dict:
    """
    获取历史趋势及粉丝特征-东方财富
    """
    try:
        from akshare_api import stock_hot_rank_detail_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_hot_rank_detail_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_rank_detail_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hot_rank_detail_xq(symbol: str) -> dict:
    """
    获取个股人气榜-实时变动
    """
    try:
        from akshare_api import stock_hot_rank_detail_xq
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_hot_rank_detail_xq(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_rank_detail_xq 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hot_rank_latest_em() -> dict:
    """
    获取个股人气榜-最新排名
    """
    try:
        from akshare_api import stock_hot_rank_latest_em
        df = stock_hot_rank_latest_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_rank_latest_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hot_keyword_em() -> dict:
    """
    获取热门关键词-东方财富
    """
    try:
        from akshare_api import stock_hot_keyword_em
        df = stock_hot_keyword_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_keyword_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hot_search_em() -> dict:
    """
    获取热搜股票-东方财富
    """
    try:
        from akshare_api import stock_hot_search_em
        df = stock_hot_search_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_search_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
def stock_hot_related_em(symbol: str) -> dict:
    """
    获取相关股票-东方财富
    """
    try:
        from akshare_api import stock_hot_related_em
        # 构建参数字典
        kwargs = {}
        if symbol is not None:
            kwargs["symbol"] = symbol
        df = stock_hot_related_em(**kwargs)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_related_em 执行失败: {e}")
        return format_error_response(e)



# 启动服务器
if __name__ == "__main__":
    logger.info(f"启动 {MCP_SERVER_NAME} v{MCP_SERVER_VERSION}")
    logger.info(f"监听端口: {MCP_SERVER_PORT}")
    logger.info(f"监听地址: {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
    mcp.run(transport="streamable-http", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
