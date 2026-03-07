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

启动 AKTools:
```bash
pip install aktools
python -m aktools
```

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

### 常用环境变量（含缓存）

```bash
# 服务基础配置
export AKTOOLS_BASE_URL="http://127.0.0.1:8080"
export MCP_SERVER_HOST="0.0.0.0"
export MCP_SERVER_PORT="8000"
export LOG_LEVEL="INFO"

# 文件缓存配置（不设置 CACHE_DIR 则禁用文件缓存）
export CACHE_DIR="./.cache/akshare-mcp"
export CACHE_TTL_REALTIME="60"
export CACHE_TTL_DAILY="900"
export CACHE_TTL_STATIC="1800"
export CACHE_DEFAULT_TTL="300"
export CACHE_CLEAN_INTERVAL_SECONDS="1800"
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

### 缓存未生效或命中率低

1. 确认已设置 `CACHE_DIR`（未设置时缓存关闭）
2. 确认目录可写：`mkdir -p "$CACHE_DIR" && touch "$CACHE_DIR/.probe"`
3. 根据场景调大 `CACHE_TTL_REALTIME` / `CACHE_TTL_DAILY` / `CACHE_TTL_STATIC`
4. 检查日志中是否有 `file_cache` 相关告警

## 缓存参数建议

### 方案 A：低延迟优先（默认推荐）

```bash
export CACHE_TTL_REALTIME="60"
export CACHE_TTL_DAILY="900"
export CACHE_TTL_STATIC="1800"
export CACHE_CLEAN_INTERVAL_SECONDS="1800"
```

适合对实时性要求较高的场景，整体缓存命中率中等，请求压力可明显下降。

### 方案 B：降请求优先（防封/省流量）

```bash
export CACHE_TTL_REALTIME="180"
export CACHE_TTL_DAILY="1800"
export CACHE_TTL_STATIC="3600"
export CACHE_CLEAN_INTERVAL_SECONDS="3600"
```

适合上游限流严格或网络波动较大的场景，命中率更高，但数据新鲜度会下降。

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

或使用构建脚本：

```bash
python tools/build_server.py
```

## 许可证

MIT
