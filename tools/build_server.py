# tools/build_server.py
"""
构建完整的 mcp_server.py 文件
"""
import re

# 读取生成的工具代码
with open('/tmp/all_tools.py', 'r', encoding='utf-8') as f:
    generated_tools = f.read()

# 移除前3行（找到信息）
lines = generated_tools.split('\n')
tools_code = '\n'.join(lines[3:])

# 构建完整的 mcp_server.py
server_code = '''# mcp_server.py
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
# MCP Tools - 133 个 AKShare 股票数据接口
# =============================================================================

'''

# 添加生成的工具代码
server_code += tools_code

# 添加启动代码
server_code += '''

# 启动服务器
if __name__ == "__main__":
    logger.info(f"启动 {MCP_SERVER_NAME} v{MCP_SERVER_VERSION}")
    logger.info(f"监听端口: {MCP_SERVER_PORT}")
    mcp.run(transport="streamable-http", port=MCP_SERVER_PORT)
'''

# 写入完整的 mcp_server.py
with open('mcp_server.py', 'w', encoding='utf-8') as f:
    f.write(server_code)

print("✓ mcp_server.py 已生成，包含 133 个 tools")
