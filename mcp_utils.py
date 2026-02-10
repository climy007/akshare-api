# mcp_utils.py
"""
MCP 工具函数 - DataFrame 转换为 MCP 友好格式
"""
import pandas as pd
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def dataframe_to_mcp_result(df: pd.DataFrame) -> Dict[str, Any]:
    """
    将 pandas DataFrame 转换为 MCP 友好的 JSON 格式

    Args:
        df: pandas DataFrame 对象

    Returns:
        dict: 包含 success, rows, columns, data 的字典
    """
    if df.empty:
        logger.warning("返回空 DataFrame")
        return {
            "success": False,
            "message": "No data available",
            "rows": 0,
            "columns": [],
            "data": []
        }

    try:
        # 转换为字典列表格式
        data_dict = df.to_dict(orient="records")

        # 处理 NaN 值（JSON 不支持 NaN）
        for record in data_dict:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None

        return {
            "success": True,
            "rows": len(df),
            "columns": list(df.columns),
            "data": data_dict
        }
    except Exception as e:
        logger.error(f"DataFrame 转换失败: {e}")
        return {
            "success": False,
            "message": f"Data conversion error: {str(e)}",
            "rows": 0,
            "columns": [],
            "data": []
        }


def format_error_response(error: Exception) -> Dict[str, Any]:
    """
    格式化错误响应

    Args:
        error: 异常对象

    Returns:
        dict: 错误信息字典
    """
    return {
        "success": False,
        "message": f"Error: {str(error)}",
        "rows": 0,
        "columns": [],
        "data": []
    }
