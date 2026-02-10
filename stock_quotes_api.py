# -*- coding: utf-8 -*-
"""
AKTools API调用 - 行情报价相关接口
基于AKShare股票数据接口完整文档编写
"""

import requests
import pandas as pd
from akshare_client import call_aktools_api


def stock_bid_ask_em(symbol):
    """
    获取行情报价-东方财富
    
    接口名称: stock_bid_ask_em
    目标地址: https://quote.eastmoney.com/sz000001.html
    描述: 东方财富-行情报价
    限量: 单次返回指定股票的行情报价数据
    
    输入参数:
    | 名称 | 类型 | 描述 |
    |------|------|------|
    | symbol | str | symbol="000001"; 股票代码 |
    
    输出参数:
    - 返回行情报价数据
    
    返回类型: pandas.DataFrame
    """
    return call_aktools_api("/api/public/stock_bid_ask_em", params={
        "symbol": symbol
    })


# 示例调用
if __name__ == "__main__":
    print("=== 行情报价数据接口测试 ===")
    
    # 获取行情报价-东方财富
    print("\n1. 行情报价-东方财富(000001):")
    bid_ask_df = stock_bid_ask_em(symbol="000001")
    print(bid_ask_df.head())
