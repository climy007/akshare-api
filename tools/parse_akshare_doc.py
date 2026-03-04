#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析 AKShare 股票文档，提取每个接口的 描述 和 输入参数，用于更新 mcp_server.py 的 docstring。
用法: python tools/parse_akshare_doc.py <doc_file.txt>
输出: JSON 到 stdout，格式为 { "接口名": { "desc": "描述", "params": [{"name","type","desc"}] } }
"""
import re
import json
import sys


def parse_doc(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    result = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        # 匹配 "接口: stock_xxx" 或 "接口: xq_xxx"
        m = re.match(r"^接口:\s*(\w+)\s*$", line.strip())
        if m:
            name = m.group(1)
            desc = ""
            params = []
            i += 1
            while i < len(lines):
                l = lines[i]
                stripped = l.strip()
                if re.match(r"^描述:\s*", stripped):
                    desc = re.sub(r"^描述:\s*", "", stripped)
                    i += 1
                    continue
                if stripped == "输入参数":
                    i += 1
                    # 跳到表头行 "| 名称 | 类型 | 描述 |"
                    while i < len(lines) and "名称" not in lines[i] and "类型" not in lines[i]:
                        i += 1
                    if i < len(lines):
                        i += 1  # 跳过表头
                    # 跳过 "| --- | --- | --- |"
                    while i < len(lines) and "---" in lines[i]:
                        i += 1
                    # 读参数行
                    while i < len(lines):
                        row = lines[i]
                        s = row.strip()
                        if not s.startswith("|") or "---" in s:
                            break
                        parts = [p.strip() for p in row.split("|") if p.strip()]
                        if len(parts) >= 3 and parts[0] != "-" and parts[0] != "名称":
                            params.append({
                                "name": parts[0],
                                "type": parts[1],
                                "desc": parts[2],
                            })
                        i += 1
                    continue
                # 下一个接口或下一节
                if stripped.startswith("接口:") or (stripped.startswith("目标地址:") and desc):
                    break
                if re.match(r"^接口:\s*\w+", stripped):
                    break
                i += 1
            result[name] = {"desc": desc, "params": params}
            continue
        i += 1
    return result


def build_docstring(name: str, info: dict, param_names: list) -> str:
    """根据解析结果和实际函数参数名列表生成 docstring。param_names 为函数签名中的参数名（如 ['symbol','period']）。"""
    desc = info.get("desc", "").strip()
    params = info.get("params", [])
    lines = [f'    """', f"    {desc}"]
    if not param_names:
        lines.append('    """')
        return "\n".join(lines)
    # 只包含实际存在的参数（按 param_names 顺序）
    param_map = {p["name"]: p for p in params}
    included = []
    for pname in param_names:
        if pname in param_map:
            included.append((pname, param_map[pname]))
    if not included:
        lines.append('    """')
        return "\n".join(lines)
    lines.append("")
    lines.append("    参数说明:")
    for pname, p in included:
        typ = p.get("type", "str")
        d = p.get("desc", "")
        lines.append(f"    - {pname}: {typ}")
        lines.append(f"      {d}")
    lines.append('    """')
    return "\n".join(lines)


def extract_param_names(signature: str) -> list:
    """从 def xxx(...) 的括号内字符串提取参数名列表。"""
    names = []
    for part in re.split(r"\s*,\s*", signature):
        # 取第一个 : 或 = 前的名字
        name = part.strip().split(":")[0].split("=")[0].strip()
        if name and name not in ("self", "cls"):
            names.append(name)
    return names


def apply_docstrings(server_path: str, doc_data: dict) -> None:
    """读取 mcp_server.py，根据 doc_data 替换每个 @mcp.tool() 函数的 docstring，写回文件。"""
    with open(server_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配: @mcp.tool()\ndef name(params) -> dict:\n    """ ... """
    pattern = re.compile(
        r"(@mcp\.tool\(\)\s*\n)(def\s+(\w+)\s*\(([^)]*)\)\s*->\s*dict:\s*\n)(\s*\"\"\"(?:.*?)\"\"\")",
        re.DOTALL,
    )

    def repl(m):
        prefix = m.group(1)
        def_line = m.group(2)
        func_name = m.group(3)
        params_part = m.group(4)
        old_doc = m.group(5)
        if func_name.startswith("_"):
            return m.group(0)
        # 自定义 MCP 工具（非 AKShare 文档接口）保留原 docstring
        if func_name.startswith("xq_token_") and func_name not in doc_data:
            return m.group(0)
        param_names = extract_param_names(params_part)
        info = doc_data.get(func_name, {})
        if not info and not param_names:
            return m.group(0)
        new_doc = build_docstring(func_name, info, param_names)
        return prefix + def_line + new_doc

    new_content = pattern.sub(repl, content)
    with open(server_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("已更新 mcp_server.py 中的 docstring", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_akshare_doc.py <doc_file.txt> [mcp_server.py]", file=sys.stderr)
        print("  若提供 mcp_server.py 路径则直接应用 docstring 更新", file=sys.stderr)
        sys.exit(1)
    doc_path = sys.argv[1]
    data = parse_doc(doc_path)
    if len(sys.argv) >= 3:
        apply_docstrings(sys.argv[2], data)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
