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
import threading
import time
import requests

# 导入配置
from config import (
    AKTOOLS_BASE_URL,
    CACHE_CLEAN_INTERVAL_SECONDS,
    CACHE_DIR,
    CACHE_TTL_DAILY,
    CACHE_TTL_REALTIME,
    CACHE_TTL_STATIC,
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCP_SERVER_PORT,
    MCP_SERVER_HOST,
    LOG_LEVEL
)

# 导入工具函数
from mcp_utils import dataframe_to_mcp_result, format_error_response
from file_cache import file_cached, clean_expired

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
_cache_cleaner_stop_event: threading.Event | None = None


def _run_cache_cleanup_once() -> None:
    if CACHE_DIR is None:
        return
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.warning("file_cache init failed (%s): %s", CACHE_DIR, e)
        return
    if not CACHE_DIR.is_dir():
        logger.warning("file_cache disabled: CACHE_DIR is not a directory (%s)", CACHE_DIR)
        return
    n = clean_expired(CACHE_DIR)
    logger.info("file_cache clean_expired: %s files removed", n)


def _start_cache_cleaner(interval_seconds: int) -> None:
    global _cache_cleaner_stop_event
    if CACHE_DIR is None or interval_seconds <= 0:
        return

    stop_event = threading.Event()
    _cache_cleaner_stop_event = stop_event

    def _worker() -> None:
        while not stop_event.wait(interval_seconds):
            _run_cache_cleanup_once()

    t = threading.Thread(target=_worker, name="file-cache-cleaner", daemon=True)
    t.start()
    logger.info("file_cache periodic cleaner started: every %ss", interval_seconds)


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

提供 55 个股票数据查询接口，包括：
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
# MCP Tools - 55 个 AKShare 股票数据接口
# =============================================================================


@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_sse_summary() -> dict:
    """
    上海证券交易所-股票数据总貌
    """
    try:
        from akshare_api import stock_sse_summary
        df = stock_sse_summary()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_sse_summary 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_szse_summary() -> dict:
    """
    深圳证券交易所-市场总貌-证券类别统计
    """
    try:
        from akshare_api import stock_szse_summary
        df = stock_szse_summary()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_szse_summary 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_szse_area_summary() -> dict:
    """
    深圳证券交易所-市场总貌-地区交易排序
    """
    try:
        from akshare_api import stock_szse_area_summary
        df = stock_szse_area_summary()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_szse_area_summary 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_szse_sector_summary(symbol: str = "当年") -> dict:
    """
    深圳证券交易所-统计资料-股票行业成交数据

    参数说明:
    - symbol: str
      symbol="当月"; choice of {"当月", "当年"}
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_sse_deal_daily() -> dict:
    """
    上海证券交易所-数据-股票数据-成交概况-股票成交概况-每日股票情况
    """
    try:
        from akshare_api import stock_sse_deal_daily
        df = stock_sse_deal_daily()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_sse_deal_daily 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_STATIC)
def stock_individual_info_em(symbol: str) -> dict:
    """
    东方财富-个股-股票信息

    参数说明:
    - symbol: str
      symbol="603777"; 股票代码
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
@file_cached(ttl_seconds=CACHE_TTL_STATIC)
def stock_individual_basic_info_xq(symbol: str) -> dict:
    """
    雪球财经-个股-公司概况-公司简介

    参数说明:
    - symbol: str
      symbol="SH601127"; 股票代码
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_zh_a_spot() -> dict:
    """
    新浪财经-沪深京 A 股数据, 重复运行本函数会被新浪暂时封 IP, 建议增加时间间隔
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
    雪球-行情中心-个股

    参数说明:
    - symbol: str
      symbol="SH600000"; 证券代码，可以是 A 股个股代码，A 股场内基金代码，A 股指数，美股代码, 美股指数
    - token: str, 可选
      token=None; 默认不设置 token（可传雪球 xq_a_token 以访问需登录的数据）
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_zh_a_hist(symbol: str, period: str = "daily", start_date: str = "20210301", end_date: str = "20210616", adjust: str = "", timeout: str = None) -> dict:
    """
    东方财富-沪深京 A 股日频率数据; 历史数据按日频率更新, 当日收盘价请在收盘后获取

    参数说明:
    - symbol: str
      symbol='603777'; 股票代码可以在 ak.stock_zh_a_spot_em() 中获取
    - period: str
      period='daily'; choice of {'daily', 'weekly', 'monthly'}
    - start_date: str
      start_date='20210301'; 开始查询的日期
    - end_date: str
      end_date='20210616'; 结束查询的日期
    - adjust: str
      默认返回不复权的数据; qfq: 返回前复权后的数据; hfq: 返回后复权后的数据
    - timeout: float
      timeout=None; 默认不设置超时参数
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_zh_a_daily(symbol: str, start_date: str = "20201103", end_date: str = "20201116", adjust: str = "") -> dict:
    """
    新浪财经-沪深京 A 股的数据, 历史数据按日频率更新; 注意其中的 sh689009 为 CDR, 请 通过 ak.stock_zh_a_cdr_daily 接口获取

    参数说明:
    - symbol: str
      symbol='sh600000'; 股票代码可以在 ak.stock_zh_a_spot() 中获取
    - start_date: str
      start_date='20201103'; 开始查询的日期
    - end_date: str
      end_date='20201116'; 结束查询的日期
    - adjust: str
      默认返回不复权的数据; qfq: 返回前复权后的数据; hfq: 返回后复权后的数据; hfq-factor: 返回后复权因子; qfq-factor: 返回前复权因子
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_zh_a_hist_tx(symbol: str, start_date: str = "20201103", end_date: str = "20201116", adjust: str = "") -> dict:
    """
    腾讯证券-日频-股票历史数据; 历史数据按日频率更新, 当日收盘价请在收盘后获取

    参数说明:
    - symbol: str
      symbol='sz000001'; 带市场标识
    - start_date: str
      start_date='19000101'; 开始查询的日期
    - end_date: str
      end_date='20500101'; 结束查询的日期
    - adjust: str
      默认返回不复权的数据; qfq: 返回前复权后的数据; hfq: 返回后复权后的数据
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
    新浪财经-沪深京 A 股股票或者指数的分时数据，目前可以获取 1, 5, 15, 30, 60 分钟的数据频率, 可以指定是否复权

    参数说明:
    - symbol: str
      symbol='sh000300'; 同日频率数据接口
    - period: str
      period='1'; 获取 1, 5, 15, 30, 60 分钟的数据频率
    - adjust: str
      adjust=""; 默认为空: 返回不复权的数据; qfq: 返回前复权后的数据; hfq: 返回后复权后的数据;
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
def stock_intraday_em(symbol: str) -> dict:
    """
    东方财富-分时数据

    参数说明:
    - symbol: str
      symbol="000001"; 股票代码
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
def stock_zh_a_hist_pre_min_em(symbol: str) -> dict:
    """
    东方财富-股票行情-盘前数据

    参数说明:
    - symbol: str
      symbol="000001"; 股票代码
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
@file_cached(ttl_seconds=CACHE_TTL_STATIC)
def stock_zh_growth_comparison_em(symbol: str) -> dict:
    """
    东方财富-行情中心-同行比较-成长性比较

    参数说明:
    - symbol: str
      symbol="SZ000895"
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
@file_cached(ttl_seconds=CACHE_TTL_STATIC)
def stock_zh_valuation_comparison_em(symbol: str) -> dict:
    """
    东方财富-行情中心-同行比较-估值比较

    参数说明:
    - symbol: str
      symbol="SZ000895"
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
@file_cached(ttl_seconds=CACHE_TTL_STATIC)
def stock_zh_dupont_comparison_em(symbol: str) -> dict:
    """
    东方财富-行情中心-同行比较-杜邦分析比较

    参数说明:
    - symbol: str
      symbol="SZ000895"
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
@file_cached(ttl_seconds=CACHE_TTL_STATIC)
def stock_zh_scale_comparison_em(symbol: str) -> dict:
    """
    东方财富-行情中心-同行比较-公司规模

    参数说明:
    - symbol: str
      symbol="SZ000895"
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
@file_cached(ttl_seconds=CACHE_TTL_STATIC)
def stock_financial_abstract(symbol: str) -> dict:
    """
    新浪财经-财务报表-关键指标

    参数说明:
    - symbol: str
      symbol="600004"; 股票代码
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_yjbb_em(date: str = "20220331") -> dict:
    """
    东方财富-数据中心-年报季报-业绩报表

    参数说明:
    - date: str
      date="20200331"; choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}; 从 20100331 开始
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_hsgt_fund_flow_summary_em() -> dict:
    """
    东方财富网-数据中心-资金流向-沪深港通资金流向
    """
    try:
        from akshare_api import stock_hsgt_fund_flow_summary_em
        df = stock_hsgt_fund_flow_summary_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hsgt_fund_flow_summary_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_profit_forecast_em() -> dict:
    """
    东方财富网-数据中心-研究报告-盈利预测; 该数据源网页端返回数据有异常, 本接口已修复该异常
    """
    try:
        from akshare_api import stock_profit_forecast_em
        df = stock_profit_forecast_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_profit_forecast_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_profit_forecast_ths() -> dict:
    """
    同花顺-盈利预测
    """
    try:
        from akshare_api import stock_profit_forecast_ths
        df = stock_profit_forecast_ths()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_profit_forecast_ths 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_STATIC)
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_hot_rank_em() -> dict:
    """
    东方财富网站-股票热度
    """
    try:
        from akshare_api import stock_hot_rank_em
        df = stock_hot_rank_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_rank_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_lhb_detail_em(start_date: str = "20230403", end_date: str = "20230417") -> dict:
    """
    东方财富网-数据中心-龙虎榜单-龙虎榜详情

    参数说明:
    - start_date: str
      start_date="20220314"
    - end_date: str
      end_date="20220315"
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_lhb_stock_statistic_em() -> dict:
    """
    东方财富网-数据中心-龙虎榜单-个股上榜统计
    """
    try:
        from akshare_api import stock_lhb_stock_statistic_em
        df = stock_lhb_stock_statistic_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_lhb_stock_statistic_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_institute_hold_detail(stock: str, quarter: str) -> dict:
    """
    新浪财经-机构持股-机构持股详情

    参数说明:
    - stock: str
      stock="300003"; 股票代码
    - quarter: str
      quarter="20201"; 从 2005 年开始, {"一季报":1, "中报":2 "三季报":3 "年报":4}, e.g., "20191", 其中的 1 表示一季报; "20193", 其中的 3 表示三季报;
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_research_report_em(symbol: str) -> dict:
    """
    东方财富网-数据中心-研究报告-个股研报

    参数说明:
    - symbol: str
      symbol="000001"
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_irm_cninfo(symbol: str) -> dict:
    """
    互动易-提问

    参数说明:
    - symbol: str
      symbol="002594";
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_irm_ans_cninfo(symbol: str) -> dict:
    """
    互动易-回答

    参数说明:
    - symbol: str
      symbol="1495108801386602496"; 通过 ak.stock_irm_cninfo 来获取具体的提问者编号
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_zh_b_spot() -> dict:
    """
    B 股数据是从新浪财经获取的数据, 重复运行本函数会被新浪暂时封 IP, 建议增加时间间隔
    """
    try:
        from akshare_api import stock_zh_b_spot
        df = stock_zh_b_spot()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_zh_b_spot 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_zh_b_daily(symbol: str, start_date: str = "20201103", end_date: str = "20201116", adjust: str = "") -> dict:
    """
    B 股数据是从新浪财经获取的数据, 历史数据按日频率更新

    参数说明:
    - symbol: str
      symbol='sh900901'; 股票代码可以在 ak.stock_zh_b_spot() 中获取
    - start_date: str
      start_date='20201103'; 开始查询的日期
    - end_date: str
      end_date='20201116'; 结束查询的日期
    - adjust: str
      默认返回不复权的数据; qfq: 返回前复权后的数据; hfq: 返回后复权后的数据; hfq-factor: 返回后复权因子; qfq-factor: 返回前复权因子
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_zh_b_minute(symbol: str, period: str = "1", adjust: str = "") -> dict:
    """
    新浪财经 B 股股票或者指数的分时数据，目前可以获取 1, 5, 15, 30, 60 分钟的数据频率, 可以指定是否复权

    参数说明:
    - symbol: str
      symbol='sh900901'; 同日频率数据接口
    - period: str
      period='1'; 获取 1, 5, 15, 30, 60 分钟的数据频率
    - adjust: str
      adjust=""; 默认为空: 返回不复权的数据; qfq: 返回前复权后的数据; hfq: 返回后复权后的数据;
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_hk_spot() -> dict:
    """
    获取所有港股的实时行情数据 15 分钟延时
    """
    try:
        from akshare_api import stock_hk_spot
        df = stock_hk_spot()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hk_spot 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_us_spot() -> dict:
    """
    新浪财经-美股; 获取的数据有 15 分钟延迟; 建议使用 ak.stock_us_spot_em() 来获取数据
    """
    try:
        from akshare_api import stock_us_spot
        df = stock_us_spot()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_us_spot 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_STATIC)
def stock_zyjs_ths(symbol: str) -> dict:
    """
    同花顺-主营介绍

    参数说明:
    - symbol: str
      symbol="000066"
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
@file_cached(ttl_seconds=CACHE_TTL_STATIC)
def stock_zygc_em(symbol: str) -> dict:
    """
    东方财富网-个股-主营构成

    参数说明:
    - symbol: str
      symbol="SH688041"
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_gsrl_gsdt_em(date: str) -> dict:
    """
    东方财富网-数据中心-股市日历-公司动态

    参数说明:
    - date: str
      date="20230808"; 交易日
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
@file_cached(ttl_seconds=CACHE_TTL_STATIC)
def stock_dividend_cninfo(symbol: str) -> dict:
    """
    巨潮资讯-个股-历史分红

    参数说明:
    - symbol: str
      symbol="600009"
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_news_em(symbol: str) -> dict:
    """
    东方财富指定个股的新闻资讯数据

    参数说明:
    - symbol: str
      symbol="603777"; 股票代码或其他关键词
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_news_main_cx() -> dict:
    """
    财新网-财新数据通-最新
    """
    try:
        from akshare_api import stock_news_main_cx
        df = stock_news_main_cx()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_news_main_cx 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_yjkb_em(date: str) -> dict:
    """
    东方财富-数据中心-年报季报-业绩快报

    参数说明:
    - date: str
      date="20200331"; choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}; 从 20100331 开始
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_yjyg_em(date: str) -> dict:
    """
    东方财富-数据中心-年报季报-业绩预告

    参数说明:
    - date: str
      date="20200331"; choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}; 从 20081231 开始
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
@file_cached(ttl_seconds=CACHE_TTL_DAILY)
def stock_yysj_em(symbol: str, date: str) -> dict:
    """
    东方财富-数据中心-年报季报-预约披露时间

    参数说明:
    - symbol: str
      symbol="沪深A股"; choice of {'沪深A股', '沪市A股', '科创板', '深市A股', '创业板', '京市A股', 'ST板'}
    - date: str
      date="20200331"; choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}; 从 20081231 开始
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_hot_follow_xq(symbol: str) -> dict:
    """
    雪球-沪深股市-热度排行榜-关注排行榜

    参数说明:
    - symbol: str
      symbol="最热门"; choice of {"本周新增", "最热门"}
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_hot_rank_detail_em(symbol: str) -> dict:
    """
    东方财富网-股票热度-历史趋势及粉丝特征

    参数说明:
    - symbol: str
      symbol="SZ000665"
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
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_hot_rank_latest_em() -> dict:
    """
    东方财富-个股人气榜-最新排名
    """
    try:
        from akshare_api import stock_hot_rank_latest_em
        df = stock_hot_rank_latest_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_rank_latest_em 执行失败: {e}")
        return format_error_response(e)

@mcp.tool()
@file_cached(ttl_seconds=CACHE_TTL_REALTIME)
def stock_hot_keyword_em() -> dict:
    """
    东方财富-个股人气榜-热门关键词
    """
    try:
        from akshare_api import stock_hot_keyword_em
        df = stock_hot_keyword_em()
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"stock_hot_keyword_em 执行失败: {e}")
        return format_error_response(e)

# 启动服务器
if __name__ == "__main__":
    _run_cache_cleanup_once()
    _start_cache_cleaner(CACHE_CLEAN_INTERVAL_SECONDS)
    logger.info(f"启动 {MCP_SERVER_NAME} v{MCP_SERVER_VERSION}")
    logger.info(f"监听端口: {MCP_SERVER_PORT}")
    logger.info(f"监听地址: {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
    mcp.run(transport="streamable-http", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
