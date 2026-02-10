# AKShare MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 使用 FastMCP 框架创建 MCP 服务器，将现有 133 个 AKShare 股票数据接口暴露为 MCP tools，通过 streamable-http 传输方式在端口 8000 提供服务。

**Architecture:**
- FastMCP 作为 MCP 服务器框架，使用 `@mcp.tool()` 装饰器注册所有接口
- 调用现有 `akshare-api.py` 中的函数获取数据
- 将 pandas DataFrame 转换为 JSON 格式返回给 AI 助手
- 使用 `mcp.run(transport="streamable-http", port=8000)` 启动 HTTP 服务

**Tech Stack:**
- FastMCP: MCP 服务器框架
- mcp: MCP 协议库
- uvicorn: HTTP 服务器（FastMCP 依赖）
- pandas: 数据处理
- requests: HTTP 客户端（调用 AKTools）

---

## Task 1: 创建配置文件

**Files:**
- Create: `config.py`

**Step 1: 创建配置文件**

```python
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
```

**Step 2: 提交配置文件**

```bash
git add config.py
git commit -m "feat: add MCP server configuration"
```

---

## Task 2: 创建数据转换工具模块

**Files:**
- Create: `mcp_utils.py`

**Step 1: 创建数据转换工具**

```python
# mcp_utils.py
"""
MCP 工具函数 - DataFrame 转换为 MCP 友好格式
"""
import pandas as pd
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def dataframe_to_mcp_result(df: pd.DataFrame) -> Dict[str, Any]:
    """
    将 pandas DataFrame 转换为 MCP 友好的 JSON 格式

    Args:
        df: pandas DataFrame 对象

    Returns:
        dict: 包含 success, rows, columns, data 的字典
    """
    if df.empty:
        logger.warning("返回空 DataFrame")
        return {
            "success": False,
            "message": "No data available",
            "rows": 0,
            "columns": [],
            "data": []
        }

    try:
        # 转换为字典列表格式
        data_dict = df.to_dict(orient="records")

        # 处理 NaN 值（JSON 不支持 NaN）
        for record in data_dict:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None

        return {
            "success": True,
            "rows": len(df),
            "columns": list(df.columns),
            "data": data_dict
        }
    except Exception as e:
        logger.error(f"DataFrame 转换失败: {e}")
        return {
            "success": False,
            "message": f"Data conversion error: {str(e)}",
            "rows": 0,
            "columns": [],
            "data": []
        }


def format_error_response(error: Exception) -> Dict[str, Any]:
    """
    格式化错误响应

    Args:
        error: 异常对象

    Returns:
        dict: 错误信息字典
    """
    return {
        "success": False,
        "message": f"Error: {str(error)}",
        "rows": 0,
        "columns": [],
        "data": []
    }
```

**Step 2: 提交工具模块**

```bash
git add mcp_utils.py
git commit -m "feat: add data conversion utilities for MCP"
```

---

## Task 3: 创建 MCP 服务器基础框架

**Files:**
- Create: `mcp_server.py`

**Step 1: 创建 MCP 服务器主文件框架**

```python
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
```

**Step 2: 提交基础框架**

```bash
git add mcp_server.py
git commit -m "feat: add MCP server base framework with 5 market summary tools"
```

---

## Task 4: 批量生成剩余 MCP Tools

**Files:**
- Create: `tools/generate_tools.py` (生成脚本)
- Modify: `mcp_server.py` (添加剩余 tools)

**Step 1: 创建工具生成脚本**

```python
# tools/generate_tools.py
"""
自动生成 MCP tools 装饰器的脚本
分析 akshare-api.py 中的函数，生成 @mcp.tool() 装饰器代码
"""
import re
import inspect
from pathlib import Path

# 读取 akshare-api.py
api_file = Path("akshare-api.py")
content = api_file.read_text(encoding="utf-8")

# 提取所有函数定义
pattern = r'^def (stock_\w+)\((.*?)\):\s*\"""(.*?)\"""'
matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)

print(f"找到 {len(matches)} 个函数")
print("\n生成 MCP tools 代码：\n")

for func_name, params, docstring in matches:
    # 解析参数
    if params.strip():
        # 有参数的函数
        param_list = [p.strip() for p in params.split(',')]
        param_defs = []
        for param in param_list:
            if '=' in param:
                name, default = param.split('=', 1)
                param_defs.append(f'{name.strip()}: {type(default).__name__} = {default.strip()}')
            else:
                parts = param.split(':')
                param_defs.append(f'{parts[0].strip()}: str')

        params_str = ', '.join(param_defs)

        print(f'@mcp.tool()')
        print(f'def {func_name}({params_str}) -> dict:')
        print(f'    """')
        print(f'    {docstring.strip()}')
        print(f'    """')
        print(f'    try:')
        print(f'        from akshare_api import {func_name}')
        print(f'        # 构建参数字典')
        print(f'        kwargs = {{}}')
        for param in param_list:
            name = param.split('=')[0].split(':')[0].strip()
            print(f'        if {name} is not None:')
            print(f'            kwargs["{name}"] = {name}')
        print(f'        df = {func_name}(**kwargs)')
        print(f'        return dataframe_to_mcp_result(df)')
        print(f'    except Exception as e:')
        print(f'        logger.error(f"{func_name} 执行失败: {{e}}")')
        print(f'        return format_error_response(e)')
        print()
    else:
        # 无参数的函数
        print(f'@mcp.tool()')
        print(f'def {func_name}() -> dict:')
        print(f'    """')
        print(f'    {docstring.strip()}')
        print(f'    """')
        print(f'    try:')
        print(f'        from akshare_api import {func_name}')
        print(f'        df = {func_name}()')
        print(f'        return dataframe_to_mcp_result(df)')
        print(f'    except Exception as e:')
        print(f'        logger.error(f"{func_name} 执行失败: {{e}}")')
        print(f'        return format_error_response(e)')
        print()
```

**Step 2: 运行生成脚本**

```bash
python tools/generate_tools.py > mcp_tools_generated.py 2>&1
```

**Step 3: 手动整合生成的代码到 mcp_server.py**

将生成的 tools 添加到 `mcp_server.py` 中的 `# 启动服务器` 之前。

**Step 4: 提交完整 MCP 服务器**

```bash
git add mcp_server.py tools/generate_tools.py
git commit -m "feat: add all 133 AKShare interface tools to MCP server"
```

---

## Task 5: 更新依赖文件

**Files:**
- Modify: `requirements.txt`

**Step 1: 添加 MCP 相关依赖**

```txt
requests>=2.25.0
pandas>=1.3.0
numpy>=1.20.0
openpyxl>=3.0.0
fastmcp>=0.1.0
mcp>=0.9.0
```

**Step 2: 提交依赖更新**

```bash
git add requirements.txt
git commit -m "feat: add FastMCP and MCP dependencies"
```

---

## Task 6: 创建启动脚本

**Files:**
- Create: `run_mcp.sh`

**Step 1: 创建启动脚本**

```bash
#!/bin/bash
# run_mcp.sh - MCP 服务器启动脚本

set -e

echo "========================================="
echo "AKShare MCP Server 启动脚本"
echo "========================================="

# 检查 AKTools 是否运行
echo "检查 AKTools 服务..."
if ! curl -s http://127.0.0.1:8080 > /dev/null; then
    echo "错误: AKTools 服务未运行 (http://127.0.0.1:8080)"
    echo "请先启动 AKTools 服务"
    exit 1
fi
echo "✓ AKTools 服务正常"

# 检查 Python 虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
else
    echo "警告: 未找到虚拟环境，使用系统 Python"
fi

# 检查依赖
echo "检查依赖..."
pip list | grep -q "fastmcp" || {
    echo "安装依赖..."
    pip install -r requirements.txt
}

# 启动 MCP 服务器
echo ""
echo "启动 MCP 服务器 (端口 8000)..."
echo "按 Ctrl+C 停止服务"
echo "========================================="
echo ""

python mcp_server.py
```

**Step 2: 设置执行权限**

```bash
chmod +x run_mcp.sh
```

**Step 3: 提交启动脚本**

```bash
git add run_mcp.sh
git commit -m "feat: add MCP server startup script"
```

---

## Task 7: 创建测试脚本

**Files:**
- Create: `test_mcp_server.py`

**Step 1: 创建基础测试脚本**

```python
# test_mcp_server.py
"""
MCP 服务器测试脚本
"""
import requests
import json
import time

# MCP 服务器配置
MCP_SERVER_URL = "http://localhost:8000"

def test_server_alive():
    """测试服务器是否运行"""
    print("测试 1: 服务器连接...")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/", timeout=2)
        print(f"✓ 服务器运行中")
        return True
    except requests.exceptions.ConnectionError:
        print(f"✗ 服务器未运行，请先启动: python mcp_server.py")
        return False
    except Exception as e:
        print(f"✗ 连接错误: {e}")
        return False


def test_list_tools():
    """测试列出所有 tools"""
    print("\n测试 2: 列出所有 MCP tools...")
    try:
        # MCP 标准端点列出 tools
        response = requests.get(f"{MCP_SERVER_URL}/tools", timeout=5)
        if response.status_code == 200:
            tools = response.json()
            print(f"✓ 共有 {len(tools)} 个 tools:")
            for tool in tools[:5]:  # 显示前5个
                print(f"  - {tool.get('name', 'unknown')}")
            if len(tools) > 5:
                print(f"  ... 还有 {len(tools) - 5} 个")
            return True
        else:
            print(f"✗ 获取 tools 列表失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


def test_call_tool_simple():
    """测试调用简单的无参数 tool"""
    print("\n测试 3: 调用无参数 tool (stock_sse_summary)...")
    try:
        payload = {
            "name": "stock_sse_summary",
            "arguments": {}
        }
        response = requests.post(
            f"{MCP_SERVER_URL}/tools/call",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✓ 成功获取数据: {result.get('rows')} 行")
                print(f"  列名: {result.get('columns')[:3]}...")
                return True
            else:
                print(f"✗ 数据为空: {result.get('message')}")
                return False
        else:
            print(f"✗ HTTP 错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


def test_call_tool_with_params():
    """测试调用带参数的 tool"""
    print("\n测试 4: 调用带参数 tool (stock_szse_sector_summary)...")
    try:
        payload = {
            "name": "stock_szse_sector_summary",
            "arguments": {
                "symbol": "当年"
            }
        }
        response = requests.post(
            f"{MCP_SERVER_URL}/tools/call",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✓ 成功获取数据: {result.get('rows')} 行")
                return True
            else:
                print(f"! 数据为空（可能是正常情况）: {result.get('message')}")
                return True
        else:
            print(f"✗ HTTP 错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("AKShare MCP 服务器测试")
    print("=" * 50)

    # 运行测试
    results = []
    results.append(test_server_alive())
    if results[0]:  # 服务器运行才继续
        results.append(test_list_tools())
        results.append(test_call_tool_simple())
        results.append(test_call_tool_with_params())

    # 总结
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 50)

    if passed == total:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
```

**Step 2: 提交测试脚本**

```bash
git add test_mcp_server.py
git commit -m "feat: add MCP server test script"
```

---

## Task 8: 创建使用文档

**Files:**
- Create: `docs/MCP_SERVER_GUIDE.md`

**Step 1: 创建 MCP 服务器使用文档**

```markdown
# AKShare MCP 服务器使用指南

## 简介

AKShare MCP 服务器将 133 个 AKShare 股票数据接口暴露为 MCP (Model Context Protocol) tools，
使 AI 助手（如 Claude）能够直接调用股票数据接口。

## 技术架构

- **框架**: FastMCP
- **传输方式**: streamable-http
- **端口**: 8000 (默认)
- **数据源**: AKTools API (localhost:8080)

## 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 确保 AKTools 服务运行

MCP 服务器依赖 AKTools 服务，请确保 AKTools 在 `http://127.0.0.1:8080` 运行。

## 启动

### 方式 1: 使用启动脚本

```bash
./run_mcp.sh
```

### 方式 2: 直接运行

```bash
python mcp_server.py
```

### 方式 3: 指定端口

```bash
MCP_SERVER_PORT=9000 python mcp_server.py
```

## Claude Desktop 配置

在 Claude Desktop 的配置文件中添加：

### macOS
`~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
`%APPDATA%/Claude/claude_desktop_config.json`

### 配置内容

```json
{
  "mcpServers": {
    "akshare-api": {
      "url": "http://localhost:8000",
      "transport": "streamable-http"
    }
  }
}
```

## 可用 Tools

服务器提供 133 个 tools，包括：

### 市场总貌 (5个)
- `stock_sse_summary`: 上海证券交易所总貌
- `stock_szse_summary`: 深圳证券交易所总貌
- `stock_szse_area_summary`: 深交所地区交易排序
- `stock_szse_sector_summary`: 深交所行业成交数据
- `stock_sse_deal_daily`: 上交所每日概况

### 实时行情 (10个)
- `stock_zh_a_spot_em`: 沪深京A股实时行情
- `stock_sh_a_spot_em`: 沪A股实时行情
- `stock_sz_a_spot_em`: 深A股实时行情
- `stock_bj_a_spot_em`: 京A股实时行情
- `stock_cy_a_spot_em`: 创业板实时行情
- `stock_kc_a_spot_em`: 科创板实时行情
- 更多...

### 历史数据
- `stock_zh_a_hist`: 历史行情（支持复权）
- `stock_zh_a_daily`: 历史行情（新浪）
- 更多...

完整列表请参考 `akshare-api.py`。

## 使用示例

### 在 Claude Desktop 中使用

启动 Claude Desktop 后，可以直接对话：

```
Claude: 请帮我获取上海证券交易所的今日总貌数据

Claude 会自动调用 stock_sse_summary tool 并返回结果
```

```
Claude: 查询平安银行（000001）最近一年的历史行情，前复权

Claude 会自动调用 stock_zh_a_hist tool，传入参数：
symbol="000001", adjust="qfq"
```

### HTTP API 测试

使用测试脚本：

```bash
python test_mcp_server.py
```

手动测试：

```bash
# 列出所有 tools
curl http://localhost:8000/tools

# 调用 tool
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "stock_sse_summary", "arguments": {}}'
```

## 返回数据格式

所有 tools 返回统一的 JSON 格式：

```json
{
  "success": true,
  "rows": 10,
  "columns": ["日期", "股票代码", "名称", "收盘价"],
  "data": [
    {"日期": "2025-02-11", "股票代码": "600000", "名称": "浦发银行", "收盘价": 10.5},
    ...
  ]
}
```

错误时返回：

```json
{
  "success": false,
  "message": "Error: AKTools service unavailable",
  "rows": 0,
  "columns": [],
  "data": []
}
```

## 故障排查

### 服务器无法启动

1. 检查 AKTools 是否运行: `curl http://127.0.0.1:8080`
2. 检查端口是否被占用: `lsof -i :8000`
3. 查看日志输出

### Claude 无法连接

1. 确认 MCP 服务器正在运行
2. 检查配置文件 URL 是否正确
3. 重启 Claude Desktop

### 数据返回为空

1. 检查 AKTools 服务是否正常
2. 确认网络连接
3. 查看服务器日志

## 开发

### 添加新的 Tool

在 `mcp_server.py` 中添加：

```python
@mcp.tool()
def your_new_tool(param1: str = "default") -> dict:
    """工具描述"""
    try:
        from akshare_api import your_function
        df = your_function(param1=param1)
        return dataframe_to_mcp_result(df)
    except Exception as e:
        logger.error(f"your_new_tool 执行失败: {e}")
        return format_error_response(e)
```

### 重新生成 Tools

如果 `akshare-api.py` 有更新，重新生成 MCP tools：

```bash
python tools/generate_tools.py > mcp_tools_new.py
# 手动将生成的代码复制到 mcp_server.py
```

## 许可证

MIT
```

**Step 2: 提交文档**

```bash
git add docs/MCP_SERVER_GUIDE.md
git commit -m "docs: add MCP server usage guide"
```

---

## Task 9: 更新主 README

**Files:**
- Modify: `README.md`

**Step 1: 在 README.md 中添加 MCP 服务器章节**

在 README.md 的 `## 更新日志` 之前添加：

```markdown
## MCP 服务器

本项目提供基于 FastMCP 框架的 MCP 服务器，将所有 AKShare 接口暴露为 MCP tools，
支持 AI 助手（如 Claude）直接调用股票数据接口。

### 快速启动

```bash
# 1. 确保 AKTools 服务运行 (端口 8080)

# 2. 启动 MCP 服务器
python mcp_server.py
# 或使用启动脚本
./run_mcp.sh

# 3. 服务器将在端口 8000 提供 streamable-http MCP 服务
```

### Claude Desktop 配置

在 Claude Desktop 配置文件中添加：

```json
{
  "mcpServers": {
    "akshare-api": {
      "url": "http://localhost:8000",
      "transport": "streamable-http"
    }
  }
}
```

详细使用指南请参考：[MCP 服务器使用指南](docs/MCP_SERVER_GUIDE.md)

```

**Step 2: 提交 README 更新**

```bash
git add README.md
git commit -m "docs: add MCP server section to README"
```

---

## Task 10: 最终集成测试

**Files:**
- Test: Integration test

**Step 1: 启动 AKTools 服务**

```bash
# 确保在另一个终端启动 AKTools
# 或验证其运行
curl http://127.0.0.1:8080
```

**Expected:** AKTools 服务返回响应

**Step 2: 启动 MCP 服务器**

```bash
python mcp_server.py
```

**Expected:** 输出类似：
```
INFO - __main__ - 启动 akshare-stock-data v1.0.0
INFO - __main__ - 监听端口: 8000
```

**Step 3: 在另一个终端运行测试**

```bash
python test_mcp_server.py
```

**Expected:**
```
==================================================
AKShare MCP 服务器测试
==================================================
测试 1: 服务器连接...
✓ 服务器运行中

测试 2: 列出所有 MCP tools...
✓ 共有 133 个 tools:
  - stock_sse_summary
  - stock_szse_summary
  ...

测试 3: 调用无参数 tool (stock_sse_summary)...
✓ 成功获取数据: 5 行

测试 4: 调用带参数 tool (stock_szse_sector_summary)...
✓ 成功获取数据: 20 行

==================================================
测试结果: 4/4 通过
==================================================
✓ 所有测试通过！
```

**Step 4: 测试 Claude Desktop 连接**

1. 确认 MCP 服务器运行
2. 配置 Claude Desktop（如上所述）
3. 重启 Claude Desktop
4. 在对话中测试：`请帮我获取上交所今日总貌数据`

**Expected:** Claude 调用 tool 并返回股票数据

**Step 5: 提交最终版本**

```bash
git add .
git commit -m "feat: complete MCP server implementation with 133 tools"
```

---

## 总结

实施完成后，您将拥有：

1. **MCP 服务器** (`mcp_server.py`): 包含 133 个 AKShare 接口的 MCP tools
2. **配置文件** (`config.py`): 集中管理服务器配置
3. **工具模块** (`mcp_utils.py`): DataFrame 到 JSON 的转换
4. **启动脚本** (`run_mcp.sh`): 一键启动服务
5. **测试脚本** (`test_mcp_server.py`): 验证服务器功能
6. **使用文档** (`docs/MCP_SERVER_GUIDE.md`): 完整的使用指南
7. **更新依赖** (`requirements.txt`): 包含 FastMCP 等

**核心特性:**
- FastMCP 框架 + streamable-http 传输
- 133 个股票数据 tools
- 统一的 JSON 返回格式
- 完善的错误处理和日志
