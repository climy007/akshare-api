# config.py
"""
MCP 服务器配置文件
"""
import os

# AKTools 服务配置
AKTOOLS_BASE_URL = os.getenv("AKTOOLS_BASE_URL", "http://127.0.0.1:8080")

# MCP 服务器配置
MCP_SERVER_NAME = "akshare-stock-data"
MCP_SERVER_VERSION = "1.0.0"
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
