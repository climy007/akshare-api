#!/usr/bin/env python3
"""
雪球 token 健康探测脚本。

用途:
1) 周期性探测 stock_individual_spot_xq 是否可用
2) 识别 token 过期特征
3) 连续失败达到阈值后发送告警
4) 记录状态文件，避免重复告警
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


TOKEN_ERROR_MARKERS = (
    "400016",
    "KeyError('data')",
    "参数错误 'data'",
    "重新登录帐号后再试",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="雪球 token 健康探测")
    parser.add_argument(
        "--base-url",
        default=os.getenv("AKTOOLS_BASE_URL", "http://aktools:8080"),
        help="AKTools 基础地址",
    )
    parser.add_argument(
        "--symbol",
        default=os.getenv("XQ_HEALTH_SYMBOL", "SH600000"),
        help="探测用股票代码",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("XQ_HEALTH_TIMEOUT_SECONDS", "12")),
        help="HTTP 超时秒数",
    )
    parser.add_argument(
        "--failure-threshold",
        type=int,
        default=int(os.getenv("XQ_HEALTH_FAILURE_THRESHOLD", "3")),
        help="连续失败阈值，达到后触发告警",
    )
    parser.add_argument(
        "--state-file",
        default=os.getenv("XQ_HEALTH_STATE_FILE", "/tmp/xq_health_state.json"),
        help="状态文件路径",
    )
    parser.add_argument(
        "--alert-webhook-url",
        default=os.getenv("XQ_ALERT_WEBHOOK_URL", ""),
        help="告警 webhook 地址（为空仅打印日志）",
    )
    parser.add_argument(
        "--alert-format",
        default=os.getenv("XQ_ALERT_FORMAT", "feishu"),
        choices=["feishu", "wecom", "raw"],
        help="告警 webhook 协议格式",
    )
    parser.add_argument(
        "--alert-recovery",
        action="store_true",
        default=os.getenv("XQ_ALERT_RECOVERY", "1") == "1",
        help="恢复后发送恢复通知",
    )
    parser.add_argument(
        "--update-command",
        default=os.getenv(
            "XQ_UPDATE_COMMAND_TEMPLATE",
            "python ops/xq_token_update.py --cookie '<latest_cookie>' --container aktools-service --mcp-container akshare-mcp-server",
        ),
        help="告警消息中附带的修复命令模板",
    )
    return parser.parse_args()


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "consecutive_failures": 0,
            "alert_sent": False,
            "last_error": "",
            "last_checked_at": "",
            "last_ok_at": "",
            "last_alert_at": "",
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "consecutive_failures": 0,
            "alert_sent": False,
            "last_error": "state_file_parse_error",
            "last_checked_at": "",
            "last_ok_at": "",
            "last_alert_at": "",
        }


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def send_alert(webhook_url: str, fmt: str, message: str, timeout: float) -> None:
    if not webhook_url:
        print(f"[alert][no_webhook] {message}")
        return

    if fmt == "wecom":
        payload = {"msgtype": "text", "text": {"content": message}}
    elif fmt == "feishu":
        payload = {"msg_type": "text", "content": {"text": message}}
    else:
        payload = {"text": message}

    resp = requests.post(webhook_url, json=payload, timeout=timeout)
    resp.raise_for_status()


@dataclass
class ProbeResult:
    ok: bool
    reason: str
    detail: str
    rows: int


def detect_token_error(detail: str) -> bool:
    lower = detail.lower()
    return any(marker.lower() in lower for marker in TOKEN_ERROR_MARKERS)


def probe(base_url: str, symbol: str, timeout: float) -> ProbeResult:
    url = f"{base_url.rstrip('/')}/api/public/stock_individual_spot_xq"
    try:
        response = requests.get(url, params={"symbol": symbol}, timeout=timeout)
    except requests.RequestException as exc:
        return ProbeResult(False, "request_error", str(exc), 0)

    body_preview = response.text[:500]
    if response.status_code != 200:
        reason = "token_expired" if detect_token_error(body_preview) else f"http_{response.status_code}"
        return ProbeResult(False, reason, body_preview, 0)

    try:
        payload = response.json()
    except ValueError:
        return ProbeResult(False, "invalid_json", body_preview, 0)

    # aktools 接口正常返回 list；异常时可能返回 dict(error)
    if isinstance(payload, list):
        rows = len(payload)
        if rows > 0:
            return ProbeResult(True, "ok", "healthy", rows)
        return ProbeResult(False, "empty_payload", "list_empty", 0)

    if isinstance(payload, dict):
        detail = json.dumps(payload, ensure_ascii=False)
        reason = "token_expired" if detect_token_error(detail) else "error_payload"
        return ProbeResult(False, reason, detail, 0)

    return ProbeResult(False, "unexpected_payload_type", type(payload).__name__, 0)


def main() -> int:
    args = parse_args()
    state_path = Path(args.state_file)
    state = load_state(state_path)

    result = probe(args.base_url, args.symbol, args.timeout)
    now = utc_now_iso()
    state["last_checked_at"] = now

    if result.ok:
        recovered = state.get("consecutive_failures", 0) > 0 or state.get("alert_sent", False)
        state["consecutive_failures"] = 0
        state["last_error"] = ""
        state["last_ok_at"] = now
        if recovered and args.alert_recovery and state.get("alert_sent", False):
            message = (
                "[XQ Watcher] 雪球接口已恢复\n"
                f"- symbol: {args.symbol}\n"
                f"- rows: {result.rows}\n"
                f"- time: {now}"
            )
            try:
                send_alert(args.alert_webhook_url, args.alert_format, message, args.timeout)
            except Exception as exc:
                print(f"[alert][recovery][failed] {exc}")
        state["alert_sent"] = False
        save_state(state_path, state)
        print(f"[health][ok] symbol={args.symbol} rows={result.rows}")
        return 0

    state["consecutive_failures"] = int(state.get("consecutive_failures", 0)) + 1
    state["last_error"] = f"{result.reason}: {result.detail}"
    should_alert = (
        state["consecutive_failures"] >= args.failure_threshold
        and not bool(state.get("alert_sent", False))
    )

    if should_alert:
        message = (
            "[XQ Watcher] 检测到雪球 token 可能失效\n"
            f"- symbol: {args.symbol}\n"
            f"- reason: {result.reason}\n"
            f"- failures: {state['consecutive_failures']}\n"
            f"- time: {now}\n"
            f"- fix: {args.update_command}"
        )
        try:
            send_alert(args.alert_webhook_url, args.alert_format, message, args.timeout)
            state["alert_sent"] = True
            state["last_alert_at"] = now
            print("[health][alert_sent] threshold reached")
        except Exception as exc:
            print(f"[health][alert_failed] {exc}")
    else:
        print(
            f"[health][fail] reason={result.reason} failures={state['consecutive_failures']} "
            f"threshold={args.failure_threshold}"
        )

    save_state(state_path, state)
    return 2 if should_alert else 1


if __name__ == "__main__":
    raise SystemExit(main())
