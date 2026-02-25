#!/usr/bin/env python3
"""
雪球 token 更新脚本（半自动修复入口）。

流程:
1) 从 --token / --cookie / 环境变量读取 token
2) 写入 aktools 容器内 akshare 的 xq_a_token 常量
3) 重启 aktools 容器
4) 自动执行回归验证
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def parse_token(cookie: str) -> str | None:
    match = re.search(r"(?:^|;\s*)xq_a_token=([^;]+)", cookie)
    if not match:
        return None
    return match.group(1).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="更新 aktools 容器内 xq_a_token")
    parser.add_argument("--token", default=os.getenv("XQ_A_TOKEN", ""), help="直接传 xq_a_token")
    parser.add_argument("--cookie", default=os.getenv("XQ_COOKIE", ""), help="完整 cookie 字符串")
    parser.add_argument("--container", default="aktools-service", help="aktools 容器名")
    parser.add_argument("--mcp-container", default="akshare-mcp-server", help="mcp 容器名，用于回归验证")
    parser.add_argument(
        "--cons-path",
        default="/usr/local/lib/python3.13/site-packages/akshare/stock/cons.py",
        help="容器内 akshare cons.py 路径",
    )
    parser.add_argument(
        "--symbols",
        default="SH600000,SZ000001",
        help="回归验证股票代码（逗号分隔）",
    )
    parser.add_argument("--verify-timeout", type=float, default=15.0, help="回归验证超时秒数")
    parser.add_argument("--skip-restart", action="store_true", help="仅更新，不重启容器")
    parser.add_argument("--skip-verify", action="store_true", help="跳过回归验证")
    return parser.parse_args()


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def update_token_in_container(container: str, cons_path: str, token: str) -> tuple[str, str]:
    inline = r"""
import re
import sys

path = sys.argv[1]
new_token = sys.argv[2]
text = open(path, "r", encoding="utf-8").read()
match = re.search(r'xq_a_token\s*=\s*"([^"]+)"', text)
if not match:
    print("ERROR: xq_a_token assignment not found")
    raise SystemExit(2)
old_token = match.group(1)
updated = re.sub(r'xq_a_token\s*=\s*"[^"]+"', f'xq_a_token = "{new_token}"', text, count=1)
open(path, "w", encoding="utf-8").write(updated)
print(old_token)
print(new_token)
"""
    cmd = ["docker", "exec", container, "python", "-c", inline, cons_path, token]
    result = run_cmd(cmd)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        raise RuntimeError(f"unexpected output: {result.stdout!r}")
    return lines[-2], lines[-1]


def restart_container(container: str) -> None:
    result = run_cmd(["docker", "restart", container])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def run_verify(mcp_container: str, symbols: str, timeout: float) -> int:
    script = Path(__file__).with_name("xq_post_repair_verify.py")
    cmd = [
        sys.executable,
        str(script),
        "--mcp-container",
        mcp_container,
        "--symbols",
        symbols,
        "--timeout",
        str(timeout),
    ]
    result = run_cmd(cmd)
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0 and result.stderr:
        print(result.stderr.strip())
    return result.returncode


def main() -> int:
    args = parse_args()
    token = args.token.strip()
    if not token and args.cookie.strip():
        parsed = parse_token(args.cookie.strip())
        if parsed:
            token = parsed
    if not token:
        print("错误: 未提供 token。请传 --token 或 --cookie（需包含 xq_a_token）")
        return 2

    print(f"[token-update] target container: {args.container}")
    print(f"[token-update] new token: {mask_secret(token)}")
    try:
        old_token, new_token = update_token_in_container(args.container, args.cons_path, token)
    except Exception as exc:
        print(f"[token-update][failed] 更新 token 失败: {exc}")
        return 2

    print(
        f"[token-update] token replaced: {mask_secret(old_token)} -> {mask_secret(new_token)}"
    )
    if not args.skip_restart:
        try:
            restart_container(args.container)
            print(f"[token-update] container restarted: {args.container}")
        except Exception as exc:
            print(f"[token-update][failed] 重启容器失败: {exc}")
            return 2

    if args.skip_verify:
        print("[token-update] skip verify by flag")
        return 0

    verify_rc = run_verify(args.mcp_container, args.symbols, args.verify_timeout)
    if verify_rc == 0:
        print("[token-update] verify passed")
        return 0
    print("[token-update] verify failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
