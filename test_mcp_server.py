# test_mcp_server.py
"""
MCP 服务器测试脚本
"""
import requests
import json

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
