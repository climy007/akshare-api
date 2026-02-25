#!/usr/bin/env python3
"""
token 修复后回归验证脚本。

通过 mcp 容器访问 aktools 内网地址，验证雪球接口是否恢复。
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="雪球 token 修复后回归验证")
    parser.add_argument(
        "--mcp-container",
        default="akshare-mcp-server",
        help="mcp 容器名，用于发起内网请求",
    )
    parser.add_argument(
        "--base-url",
        default="http://aktools:8080",
        help="aktools 在 docker 网络中的地址",
    )
    parser.add_argument(
        "--symbols",
        default="SH600000,SZ000001",
        help="逗号分隔的验证股票代码",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="单次请求超时时间（秒）",
    )
    return parser.parse_args()


def run_verify(mcp_container: str, base_url: str, symbols: list[str], timeout: float) -> list[dict[str, Any]]:
    inline = r"""
import json
import sys
import requests

base_url = sys.argv[1].rstrip("/")
symbols = [item for item in sys.argv[2].split(",") if item]
timeout = float(sys.argv[3])
rows = []
for symbol in symbols:
    url = f"{base_url}/api/public/stock_individual_spot_xq"
    try:
        resp = requests.get(url, params={"symbol": symbol}, timeout=timeout)
        status_code = resp.status_code
        try:
            payload = resp.json()
        except ValueError:
            payload = None
        row_count = len(payload) if isinstance(payload, list) else 0
        rows.append(
            {
                "symbol": symbol,
                "status_code": status_code,
                "row_count": row_count,
                "ok": status_code == 200 and row_count > 0,
                "preview": resp.text[:180],
            }
        )
    except Exception as exc:
        rows.append(
            {
                "symbol": symbol,
                "status_code": 0,
                "row_count": 0,
                "ok": False,
                "preview": repr(exc),
            }
        )
print(json.dumps(rows, ensure_ascii=False))
"""
    cmd = [
        "docker",
        "exec",
        mcp_container,
        "python",
        "-c",
        inline,
        base_url,
        ",".join(symbols),
        str(timeout),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"docker exec failed({result.returncode}): {result.stderr.strip() or result.stdout.strip()}"
        )
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"verify output parse failed: {exc}; raw={result.stdout!r}") from exc


def main() -> int:
    args = parse_args()
    symbols = [item.strip() for item in args.symbols.split(",") if item.strip()]
    if not symbols:
        print("错误: --symbols 不能为空")
        return 2

    try:
        rows = run_verify(args.mcp_container, args.base_url, symbols, args.timeout)
    except Exception as exc:
        print(f"[verify][failed] {exc}")
        print("建议检查 docker 容器状态与网络连通性。")
        return 2

    all_ok = all(item.get("ok") for item in rows)
    print("[verify] result:")
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    print(f"[verify] summary: {'PASS' if all_ok else 'FAIL'}")
    if not all_ok:
        fix_hint = (
            "python ops/xq_token_update.py --cookie '<latest_cookie>' "
            "--container aktools-service --mcp-container akshare-mcp-server"
        )
        print(f"[verify] hint: {shlex.quote(fix_hint)}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
