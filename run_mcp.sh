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
