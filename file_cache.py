# file_cache.py
"""
文件缓存：按 TTL 缓存 MCP 工具返回的 JSON 结果，不占用内存，适合低内存服务器。
"""
import hashlib
import inspect
import json
import logging
import os
import tempfile
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def _cache_key(name: str, args: tuple, kwargs: dict) -> str:
    """根据工具名与参数生成稳定缓存 key（哈希）。"""
    payload = {
        "n": name,
        "a": list(args),
        "k": sorted((k, v) for k, v in kwargs.items()),
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _cache_path(cache_dir: Path, name: str, key: str) -> Path:
    """缓存文件路径：cache_dir/工具名/key.json"""
    return cache_dir / name / f"{key}.json"


def get(cache_dir: Path, name: str, args: tuple, kwargs: dict, ttl_seconds: float) -> Optional[dict]:
    """
    从文件缓存读取结果。若不存在或已过期则返回 None。

    Args:
        cache_dir: 缓存根目录
        name: 工具名（如函数名）
        args: 位置参数元组
        kwargs: 关键字参数字典
        ttl_seconds: 有效秒数，过期则视为未命中

    Returns:
        缓存的 result 字典，或 None
    """
    if ttl_seconds <= 0:
        return None
    try:
        key = _cache_key(name, args, kwargs)
        path = _cache_path(cache_dir, name, key)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            entry = json.load(f)
        expires_at = entry.get("expires_at")
        if expires_at is not None:
            try:
                expires_at = float(expires_at)
            except (TypeError, ValueError):
                raise ValueError("invalid expires_at")
        if expires_at is not None and time.time() > expires_at:
            try:
                path.unlink()
            except OSError:
                pass
            return None
        result = entry.get("result")
        if not isinstance(result, dict):
            raise ValueError("invalid result")
        return result
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as e:
        logger.debug("file_cache get %s: %s", path, e)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        return None


def set(
    cache_dir: Path,
    name: str,
    args: tuple,
    kwargs: dict,
    ttl_seconds: float,
    result: dict,
) -> None:
    """
    将结果写入文件缓存。

    Args:
        cache_dir: 缓存根目录
        name: 工具名
        args: 位置参数元组
        kwargs: 关键字参数字典
        ttl_seconds: 有效秒数
        result: 要缓存的 result 字典（可 JSON 序列化）
    """
    if ttl_seconds <= 0:
        return
    key = _cache_key(name, args, kwargs)
    path = _cache_path(cache_dir, name, key)
    entry = {
        "expires_at": time.time() + ttl_seconds,
        "result": result,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(entry, ensure_ascii=False, default=str)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f"{path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as f:
            f.write(raw)
            tmp_name = f.name
        os.replace(tmp_name, path)
    except (OSError, TypeError) as e:
        logger.warning("file_cache set %s: %s", path, e)
        try:
            if "tmp_name" in locals():
                Path(tmp_name).unlink(missing_ok=True)
        except OSError:
            pass


def clean_expired(cache_dir: Path) -> int:
    """
    扫描缓存目录，删除已过期或损坏的缓存文件（不删除 .tmp 写入中文件）。

    Args:
        cache_dir: 缓存根目录，与 set/get 使用的一致。

    Returns:
        删除的文件数量。若 cache_dir 不存在或非目录，返回 0。
    """
    if not cache_dir.exists() or not cache_dir.is_dir():
        logger.debug("file_cache clean_expired: %s not a directory or missing", cache_dir)
        return 0
    removed = 0
    now = time.time()
    try:
        for tool_dir in cache_dir.iterdir():
            if not tool_dir.is_dir():
                continue
            for path in tool_dir.iterdir():
                if path.is_file() and path.suffix == ".json":
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            entry = json.load(f)
                        expires_at = entry.get("expires_at")
                        if expires_at is None:
                            path.unlink()
                            removed += 1
                            continue
                        try:
                            expires_at = float(expires_at)
                        except (TypeError, ValueError):
                            path.unlink()
                            removed += 1
                            continue
                        if now > expires_at:
                            path.unlink()
                            removed += 1
                    except (json.JSONDecodeError, OSError, TypeError, ValueError):
                        try:
                            path.unlink()
                            removed += 1
                        except OSError:
                            pass
    except OSError as e:
        logger.warning("file_cache clean_expired: %s", e)
    return removed


def file_cached(ttl_seconds: float, cache_dir: Optional[Path] = None):
    """
    装饰器：对工具函数的返回值做文件缓存（按 TTL）。

    Args:
        ttl_seconds: 缓存有效秒数
        cache_dir: 缓存根目录，为 None 时从 config 读取
    """

    def decorator(f: Callable[..., dict]) -> Callable[..., dict]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> dict:
            from config import CACHE_DIR

            root = cache_dir if cache_dir is not None else CACHE_DIR
            if root is None or ttl_seconds <= 0:
                return f(*args, **kwargs)
            name = f.__name__
            cached = get(root, name, args, kwargs, ttl_seconds)
            if cached is not None:
                logger.debug("file_cache hit: %s", name)
                return cached
            result = f(*args, **kwargs)
            if result is not None and result.get("success") is True:
                set(root, name, args, kwargs, ttl_seconds, result)
            return result

        # 保留原函数签名，供 FastMCP 解析工具参数
        wrapper.__signature__ = inspect.signature(f)
        return wrapper

    return decorator


if __name__ == "__main__":
    import sys

    cache_dir_raw = os.getenv("CACHE_DIR", "").strip()
    if not cache_dir_raw:
        print("Usage: CACHE_DIR=/path/to/cache python -m file_cache", file=sys.stderr)
        sys.exit(1)
    root = Path(cache_dir_raw)
    n = clean_expired(root)
    print(f"file_cache clean_expired: {n} files removed")
