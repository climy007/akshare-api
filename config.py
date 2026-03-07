# config.py
"""
MCP 服务器配置文件
"""
import os
from pathlib import Path

# AKTools 服务配置
AKTOOLS_BASE_URL = os.getenv("AKTOOLS_BASE_URL", "http://127.0.0.1:8080")

# MCP 服务器配置
MCP_SERVER_NAME = "akshare-stock-data"
MCP_SERVER_VERSION = "1.0.0"
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 文件缓存配置（不占内存，用于减轻上游请求与防封 IP）
# 为空或未设置则禁用文件缓存
_CACHE_DIR_RAW = os.getenv("CACHE_DIR", "").strip()
CACHE_DIR = Path(_CACHE_DIR_RAW) if _CACHE_DIR_RAW else None

# 默认缓存 TTL（秒），仅影响未单独指定 TTL 的接口
CACHE_DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", "300"))

# 分层 TTL（秒）
# 实时数据建议较短缓存，静态资料建议较长缓存
# 默认采用方案 B（降请求优先）
CACHE_TTL_REALTIME = int(os.getenv("CACHE_TTL_REALTIME", "180"))
CACHE_TTL_DAILY = int(os.getenv("CACHE_TTL_DAILY", "1800"))
CACHE_TTL_STATIC = int(os.getenv("CACHE_TTL_STATIC", "3600"))

# 文件缓存后台清理周期（秒）
# <= 0 表示仅启动时清理一次
CACHE_CLEAN_INTERVAL_SECONDS = int(os.getenv("CACHE_CLEAN_INTERVAL_SECONDS", "3600"))
