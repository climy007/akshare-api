# akshare_client.py
"""
AKShare API 客户端
统一管理 AKTools API 的调用
"""
import os
import requests
import pandas as pd


def get_aktools_base_url():
    """获取 AKTools 基础 URL，优先使用环境变量"""
    return os.getenv("AKTOOLS_BASE_URL", "http://127.0.0.1:8080")


def call_aktools_api(endpoint, params=None):
    """
    调用 AKTools API

    Args:
        endpoint: API 端点，例如 "/api/public/stock_sse_summary"
        params: 查询参数（可选）

    Returns:
        pandas.DataFrame: 返回的数据
    """
    base_url = get_aktools_base_url()
    url = f"{base_url}{endpoint}"

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return pd.DataFrame()
