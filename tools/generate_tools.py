# tools/generate_tools.py
"""
自动生成 MCP tools 装饰器的脚本
分析 akshare-api.py 中的函数，生成 @mcp.tool() 装饰器代码
"""
import re
from pathlib import Path

# 读取 akshare-api.py
api_file = Path("akshare-api.py")
content = api_file.read_text(encoding="utf-8")

# 提取所有函数定义
pattern = r'^def (stock_\w+)\((.*?)\):\s*"""(.*?)"""'
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
                # 推断类型
                if isinstance(default, str) and default.strip().startswith('"'):
                    param_type = 'str'
                elif isinstance(default, str) and default.strip().isdigit():
                    param_type = 'int'
                elif isinstance(default, str) and default.strip() in ['True', 'False']:
                    param_type = 'bool'
                else:
                    param_type = 'str'
                param_defs.append(f'{name.strip()}: {param_type} = {default.strip()}')
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
