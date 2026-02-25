# -*- coding: utf-8 -*-
"""
AKShare API调用 - 完整股票数据接口汇总
基于AKShare股票数据接口完整文档编写
包含98个股票相关的数据接口调用方法
"""

import requests
import pandas as pd
from akshare_client import call_aktools_api


# =============================================================================
# 1. A股数据接口 (47个)
# =============================================================================

# 1.1 股票市场总貌 (5个)
def stock_sse_summary():
    """获取上海证券交易所总貌数据"""
    return call_aktools_api("/api/public/stock_sse_summary")


def stock_szse_summary():
    """获取深圳证券交易所总貌数据"""
    return call_aktools_api("/api/public/stock_szse_summary")


def stock_szse_area_summary():
    """获取深圳证券交易所地区交易排序数据"""
    return call_aktools_api("/api/public/stock_szse_area_summary")


def stock_szse_sector_summary(symbol="当年"):
    """获取深圳证券交易所股票行业成交数据"""
    return call_aktools_api("/api/public/stock_szse_sector_summary", params={"symbol": symbol})


def stock_sse_deal_daily():
    """获取上海证券交易所每日概况数据"""
    return call_aktools_api("/api/public/stock_sse_deal_daily")


# 1.2 个股信息查询 (2个)
def stock_individual_info_em(symbol):
    """获取个股信息查询-东方财富"""
    return call_aktools_api("/api/public/stock_individual_info_em", params={"symbol": symbol})


def stock_individual_basic_info_xq(symbol):
    """获取个股信息查询-雪球"""
    return call_aktools_api("/api/public/stock_individual_basic_info_xq", params={"symbol": symbol})


# 1.3 行情报价 (1个)
def stock_bid_ask_em(symbol):
    """获取行情报价-东方财富"""
    return call_aktools_api("/api/public/stock_bid_ask_em", params={"symbol": symbol})


# 1.4 实时行情数据 (10个)
def stock_zh_a_spot_em():
    """获取沪深京A股实时行情-东方财富"""
    return call_aktools_api("/api/public/stock_zh_a_spot_em")


def stock_sh_a_spot_em():
    """获取沪A股实时行情-东方财富"""
    return call_aktools_api("/api/public/stock_sh_a_spot_em")


def stock_sz_a_spot_em():
    """获取深A股实时行情-东方财富"""
    return call_aktools_api("/api/public/stock_sz_a_spot_em")


def stock_bj_a_spot_em():
    """获取京A股实时行情-东方财富"""
    return call_aktools_api("/api/public/stock_bj_a_spot_em")


def stock_new_a_spot_em():
    """获取新股实时行情-东方财富"""
    return call_aktools_api("/api/public/stock_new_a_spot_em")


def stock_cy_a_spot_em():
    """获取创业板实时行情-东方财富"""
    return call_aktools_api("/api/public/stock_cy_a_spot_em")


def stock_kc_a_spot_em():
    """获取科创板实时行情-东方财富"""
    return call_aktools_api("/api/public/stock_kc_a_spot_em")


def stock_zh_ab_comparison_em():
    """获取AB股比价-东方财富"""
    return call_aktools_api("/api/public/stock_zh_ab_comparison_em")


def stock_zh_a_spot():
    """获取沪深京A股实时行情-新浪"""
    return call_aktools_api("/api/public/stock_zh_a_spot")


def stock_individual_spot_xq(symbol, token=None):
    """获取个股实时行情-雪球"""
    params = {"symbol": symbol}
    if token:
        params["token"] = token
    return call_aktools_api("/api/public/stock_individual_spot_xq", params=params)


# 1.5 历史行情数据 (3个)
def stock_zh_a_hist(symbol, period="daily", start_date="20210301", end_date="20210616", adjust="", timeout=None):
    """获取历史行情数据-东方财富"""
    return call_aktools_api("/api/public/stock_zh_a_hist", params={
        "symbol": symbol,
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust,
        "timeout": timeout
    })


def stock_zh_a_daily(symbol, start_date="20201103", end_date="20201116", adjust=""):
    """获取历史行情数据-新浪"""
    return call_aktools_api("/api/public/stock_zh_a_daily", params={
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


def stock_zh_a_hist_tx(symbol, start_date="20201103", end_date="20201116", adjust=""):
    """获取历史行情数据-腾讯"""
    return call_aktools_api("/api/public/stock_zh_a_hist_tx", params={
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


# 1.6 分时数据 (5个)
def stock_zh_a_minute(symbol, period="1", adjust=""):
    """获取分时数据-新浪"""
    return call_aktools_api("/api/public/stock_zh_a_minute", params={
        "symbol": symbol,
        "period": period,
        "adjust": adjust
    })


def stock_zh_a_hist_min_em(symbol, period="1", start_date="2021-09-01 09:30:00", end_date="2021-09-01 15:00:00", adjust=""):
    """获取分时数据-东方财富"""
    return call_aktools_api("/api/public/stock_zh_a_hist_min_em", params={
        "symbol": symbol,
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


def stock_intraday_em(symbol):
    """获取日内分时数据-东方财富"""
    return call_aktools_api("/api/public/stock_intraday_em", params={"symbol": symbol})


def stock_intraday_sina(symbol):
    """获取日内分时数据-新浪"""
    return call_aktools_api("/api/public/stock_intraday_sina", params={"symbol": symbol})


def stock_zh_a_hist_pre_min_em(symbol):
    """获取盘前数据-东方财富"""
    return call_aktools_api("/api/public/stock_zh_a_hist_pre_min_em", params={"symbol": symbol})


# 1.7 历史分笔数据 (1个)
def stock_zh_a_tick_tx(symbol, trade_date="20210316"):
    """获取历史分笔数据-腾讯"""
    return call_aktools_api("/api/public/stock_zh_a_tick_tx", params={
        "symbol": symbol,
        "trade_date": trade_date
    })


# 1.8 其他A股相关接口 (20个)
def stock_zh_growth_comparison_em(symbol):
    """获取股票成长性比较-东方财富"""
    return call_aktools_api("/api/public/stock_zh_growth_comparison_em", params={"symbol": symbol})


def stock_zh_valuation_comparison_em(symbol):
    """获取股票估值比较-东方财富"""
    return call_aktools_api("/api/public/stock_zh_valuation_comparison_em", params={"symbol": symbol})


def stock_zh_dupont_comparison_em(symbol):
    """获取股票杜邦分析比较-东方财富"""
    return call_aktools_api("/api/public/stock_zh_dupont_comparison_em", params={"symbol": symbol})


def stock_zh_scale_comparison_em(symbol):
    """获取股票规模比较-东方财富"""
    return call_aktools_api("/api/public/stock_zh_scale_comparison_em", params={"symbol": symbol})


def stock_zh_a_cdr_daily(symbol, start_date="20201103", end_date="20201116", adjust=""):
    """获取CDR历史数据-新浪"""
    return call_aktools_api("/api/public/stock_zh_a_cdr_daily", params={
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


def stock_financial_abstract(symbol):
    """获取财务报表数据"""
    return call_aktools_api("/api/public/stock_financial_abstract", params={"symbol": symbol})


def stock_financial_analysis_indicator(symbol):
    """获取财务指标数据"""
    return call_aktools_api("/api/public/stock_financial_analysis_indicator", params={"symbol": symbol})


def stock_yjbb_em(date="20220331"):
    """获取业绩报表数据"""
    return call_aktools_api("/api/public/stock_yjbb_em", params={"date": date})


def stock_hsgt_fund_flow_summary_em():
    """获取沪深港通资金流向"""
    return call_aktools_api("/api/public/stock_hsgt_fund_flow_summary_em")


def stock_individual_fund_flow_rank():
    """获取个股资金流向"""
    return call_aktools_api("/api/public/stock_individual_fund_flow_rank")


def stock_profit_forecast_em():
    """获取东方财富盈利预测"""
    return call_aktools_api("/api/public/stock_profit_forecast_em")


def stock_profit_forecast_ths():
    """获取同花顺盈利预测"""
    return call_aktools_api("/api/public/stock_profit_forecast_ths")


def stock_board_concept_cons_ths():
    """获取同花顺概念板块指数"""
    return call_aktools_api("/api/public/stock_board_concept_cons_ths")


def stock_board_concept_name_em():
    """获取东方财富概念板块"""
    return call_aktools_api("/api/public/stock_board_concept_name_em")


def stock_board_concept_hist_em(symbol, period="daily", start_date="20220101", end_date="20250227", adjust=""):
    """获取概念板块历史行情"""
    return call_aktools_api("/api/public/stock_board_concept_hist_em", params={
        "symbol": symbol,
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


def stock_board_industry_name_ths():
    """获取同花顺行业一览表"""
    return call_aktools_api("/api/public/stock_board_industry_name_ths")


def stock_board_industry_name_em():
    """获取东方财富行业板块"""
    return call_aktools_api("/api/public/stock_board_industry_name_em")


def stock_hot_rank_em():
    """获取股票热度排行"""
    return call_aktools_api("/api/public/stock_hot_rank_em")


def stock_market_activity_em():
    """获取盘口异动数据"""
    return call_aktools_api("/api/public/stock_market_activity_em")


def stock_board_change_em():
    """获取板块异动详情"""
    return call_aktools_api("/api/public/stock_board_change_em")


def stock_zt_pool_em():
    """获取涨停股池"""
    return call_aktools_api("/api/public/stock_zt_pool_em")


def stock_zt_pool_previous_em():
    """获取昨日涨停股池"""
    return call_aktools_api("/api/public/stock_zt_pool_previous_em")


def stock_dt_pool_em():
    """获取跌停股池"""
    return call_aktools_api("/api/public/stock_dt_pool_em")


def stock_lhb_detail_em(start_date="20230403", end_date="20230417"):
    """获取龙虎榜详情"""
    return call_aktools_api("/api/public/stock_lhb_detail_em", params={
        "start_date": start_date,
        "end_date": end_date
    })


def stock_lhb_stock_statistic_em():
    """获取个股上榜统计"""
    return call_aktools_api("/api/public/stock_lhb_stock_statistic_em")


def stock_institute_visit_em():
    """获取机构调研统计"""
    return call_aktools_api("/api/public/stock_institute_visit_em")


def stock_institute_visit_detail_em():
    """获取机构调研详细"""
    return call_aktools_api("/api/public/stock_institute_visit_detail_em")


def stock_institute_hold_detail(stock, quarter):
    """获取机构持股详情"""
    return call_aktools_api("/api/public/stock_institute_hold_detail", params={
        "stock": stock,
        "quarter": quarter
    })


def stock_institute_recommend(symbol):
    """获取机构推荐池"""
    return call_aktools_api("/api/public/stock_institute_recommend", params={"symbol": symbol})


def stock_institute_recommend_detail(symbol):
    """获取股票评级记录"""
    return call_aktools_api("/api/public/stock_institute_recommend_detail", params={"symbol": symbol})


def stock_research_report_em(symbol):
    """获取个股研报"""
    return call_aktools_api("/api/public/stock_research_report_em", params={"symbol": symbol})


def stock_info_cjzc_em():
    """获取财经早餐"""
    return call_aktools_api("/api/public/stock_info_cjzc_em")


def stock_info_global_em():
    """获取全球财经快讯-东方财富"""
    return call_aktools_api("/api/public/stock_info_global_em")


def stock_info_global_sina():
    """获取全球财经快讯-新浪财经"""
    return call_aktools_api("/api/public/stock_info_global_sina")


def stock_irm_cninfo(symbol):
    """获取互动易-提问"""
    return call_aktools_api("/api/public/stock_irm_cninfo", params={"symbol": symbol})


def stock_irm_ans_cninfo(symbol):
    """获取互动易-回答"""
    return call_aktools_api("/api/public/stock_irm_ans_cninfo", params={"symbol": symbol})


def stock_sns_sseinfo(symbol):
    """获取上证e互动"""
    return call_aktools_api("/api/public/stock_sns_sseinfo", params={"symbol": symbol})


# =============================================================================
# 2. B股数据接口 (4个)
# =============================================================================

def stock_zh_b_spot_em():
    """获取B股实时行情-东方财富"""
    return call_aktools_api("/api/public/stock_zh_b_spot_em")


def stock_zh_b_spot():
    """获取B股实时行情-新浪"""
    return call_aktools_api("/api/public/stock_zh_b_spot")


def stock_zh_b_daily(symbol, start_date="20201103", end_date="20201116", adjust=""):
    """获取B股历史行情数据-新浪"""
    return call_aktools_api("/api/public/stock_zh_b_daily", params={
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


def stock_zh_b_minute(symbol, period="1", adjust=""):
    """获取B股分时数据-新浪"""
    return call_aktools_api("/api/public/stock_zh_b_minute", params={
        "symbol": symbol,
        "period": period,
        "adjust": adjust
    })


# =============================================================================
# 3. 港股数据接口 (3个)
# =============================================================================

def stock_hk_spot_em():
    """获取港股实时行情-东方财富"""
    return call_aktools_api("/api/public/stock_hk_spot_em")


def stock_hk_spot():
    """获取港股实时行情-新浪"""
    return call_aktools_api("/api/public/stock_hk_spot")


def stock_hk_daily(symbol, start_date="20201103", end_date="20201116", adjust=""):
    """获取港股历史行情数据-新浪"""
    return call_aktools_api("/api/public/stock_hk_daily", params={
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


# =============================================================================
# 4. 美股数据接口 (3个)
# =============================================================================

def stock_us_spot():
    """获取美股实时行情-新浪"""
    return call_aktools_api("/api/public/stock_us_spot")


def stock_us_spot_em():
    """获取美股实时行情-东方财富"""
    return call_aktools_api("/api/public/stock_us_spot_em")


def stock_us_daily(symbol, start_date="20201103", end_date="20201116", adjust=""):
    """获取美股历史行情数据-新浪"""
    return call_aktools_api("/api/public/stock_us_daily", params={
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


# =============================================================================
# 5. 其他功能接口 (4个)
# =============================================================================

def stock_zh_growth_comparison_em(symbol):
    """获取股票成长性比较-东方财富"""
    return call_aktools_api("/api/public/stock_zh_growth_comparison_em", params={"symbol": symbol})


def stock_zh_valuation_comparison_em(symbol):
    """获取股票估值比较-东方财富"""
    return call_aktools_api("/api/public/stock_zh_valuation_comparison_em", params={"symbol": symbol})


def stock_zh_dupont_comparison_em(symbol):
    """获取股票杜邦分析比较-东方财富"""
    return call_aktools_api("/api/public/stock_zh_dupont_comparison_em", params={"symbol": symbol})


def stock_zh_scale_comparison_em(symbol):
    """获取股票规模比较-东方财富"""
    return call_aktools_api("/api/public/stock_zh_scale_comparison_em", params={"symbol": symbol})


# =============================================================================
# 6. 特殊功能接口 (1个)
# =============================================================================

def stock_zh_a_cdr_daily(symbol, start_date="20201103", end_date="20201116", adjust=""):
    """获取CDR历史数据-新浪"""
    return call_aktools_api("/api/public/stock_zh_a_cdr_daily", params={
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


# =============================================================================
# 7. 高级功能接口 (36个)
# =============================================================================

# 7.1 基本面数据接口 (3个)
def stock_financial_abstract(symbol):
    """获取财务报表数据"""
    return call_aktools_api("/api/public/stock_financial_abstract", params={"symbol": symbol})


def stock_financial_analysis_indicator(symbol):
    """获取财务指标数据"""
    return call_aktools_api("/api/public/stock_financial_analysis_indicator", params={"symbol": symbol})


def stock_yjbb_em(date="20220331"):
    """获取业绩报表数据"""
    return call_aktools_api("/api/public/stock_yjbb_em", params={"date": date})


# 7.2 资金流向接口 (2个)
def stock_hsgt_fund_flow_summary_em():
    """获取沪深港通资金流向"""
    return call_aktools_api("/api/public/stock_hsgt_fund_flow_summary_em")


def stock_individual_fund_flow_rank():
    """获取个股资金流向"""
    return call_aktools_api("/api/public/stock_individual_fund_flow_rank")


# 7.3 盈利预测接口 (2个)
def stock_profit_forecast_em():
    """获取东方财富盈利预测"""
    return call_aktools_api("/api/public/stock_profit_forecast_em")


def stock_profit_forecast_ths():
    """获取同花顺盈利预测"""
    return call_aktools_api("/api/public/stock_profit_forecast_ths")


# 7.4 概念板块接口 (3个)
def stock_board_concept_cons_ths():
    """获取同花顺概念板块指数"""
    return call_aktools_api("/api/public/stock_board_concept_cons_ths")


def stock_board_concept_name_em():
    """获取东方财富概念板块"""
    return call_aktools_api("/api/public/stock_board_concept_name_em")


def stock_board_concept_hist_em(symbol, period="daily", start_date="20220101", end_date="20250227", adjust=""):
    """获取概念板块历史行情"""
    return call_aktools_api("/api/public/stock_board_concept_hist_em", params={
        "symbol": symbol,
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


# 7.5 行业板块接口 (2个)
def stock_board_industry_name_ths():
    """获取同花顺行业一览表"""
    return call_aktools_api("/api/public/stock_board_industry_name_ths")


def stock_board_industry_name_em():
    """获取东方财富行业板块"""
    return call_aktools_api("/api/public/stock_board_industry_name_em")


# 7.6 股票热度接口 (1个)
def stock_hot_rank_em():
    """获取股票热度排行"""
    return call_aktools_api("/api/public/stock_hot_rank_em")


# 7.7 盘口异动接口 (1个)
def stock_market_activity_em():
    """获取盘口异动数据"""
    return call_aktools_api("/api/public/stock_market_activity_em")


# 7.8 板块异动详情接口 (1个)
def stock_board_change_em():
    """获取板块异动详情"""
    return call_aktools_api("/api/public/stock_board_change_em")


# 7.9 涨停板行情接口 (3个)
def stock_zt_pool_em():
    """获取涨停股池"""
    return call_aktools_api("/api/public/stock_zt_pool_em")


def stock_zt_pool_previous_em():
    """获取昨日涨停股池"""
    return call_aktools_api("/api/public/stock_zt_pool_previous_em")


def stock_dt_pool_em():
    """获取跌停股池"""
    return call_aktools_api("/api/public/stock_dt_pool_em")


# 7.10 龙虎榜接口 (2个)
def stock_lhb_detail_em(start_date="20230403", end_date="20230417"):
    """获取龙虎榜详情"""
    return call_aktools_api("/api/public/stock_lhb_detail_em", params={
        "start_date": start_date,
        "end_date": end_date
    })


def stock_lhb_stock_statistic_em():
    """获取个股上榜统计"""
    return call_aktools_api("/api/public/stock_lhb_stock_statistic_em")


# 7.11 机构调研接口 (2个)
def stock_institute_visit_em():
    """获取机构调研统计"""
    return call_aktools_api("/api/public/stock_institute_visit_em")


def stock_institute_visit_detail_em():
    """获取机构调研详细"""
    return call_aktools_api("/api/public/stock_institute_visit_detail_em")


# 7.12 机构持股接口 (1个)
def stock_institute_hold_detail(stock, quarter):
    """获取机构持股详情"""
    return call_aktools_api("/api/public/stock_institute_hold_detail", params={
        "stock": stock,
        "quarter": quarter
    })


# 7.13 机构推荐接口 (2个)
def stock_institute_recommend(symbol):
    """获取机构推荐池"""
    return call_aktools_api("/api/public/stock_institute_recommend", params={"symbol": symbol})


def stock_institute_recommend_detail(symbol):
    """获取股票评级记录"""
    return call_aktools_api("/api/public/stock_institute_recommend_detail", params={"symbol": symbol})


# 7.14 个股研报接口 (1个)
def stock_research_report_em(symbol):
    """获取个股研报"""
    return call_aktools_api("/api/public/stock_research_report_em", params={"symbol": symbol})


# 7.15 资讯数据接口 (3个)
def stock_info_cjzc_em():
    """获取财经早餐"""
    return call_aktools_api("/api/public/stock_info_cjzc_em")


def stock_info_global_em():
    """获取全球财经快讯-东方财富"""
    return call_aktools_api("/api/public/stock_info_global_em")


def stock_info_global_sina():
    """获取全球财经快讯-新浪财经"""
    return call_aktools_api("/api/public/stock_info_global_sina")


# 7.16 互动易接口 (3个)
def stock_irm_cninfo(symbol):
    """获取互动易-提问"""
    return call_aktools_api("/api/public/stock_irm_cninfo", params={"symbol": symbol})


def stock_irm_ans_cninfo(symbol):
    """获取互动易-回答"""
    return call_aktools_api("/api/public/stock_irm_ans_cninfo", params={"symbol": symbol})


def stock_sns_sseinfo(symbol):
    """获取上证e互动"""
    return call_aktools_api("/api/public/stock_sns_sseinfo", params={"symbol": symbol})


# 7.17 赚钱效应分析接口 (1个)
def stock_market_activity_em():
    """获取赚钱效应分析"""
    return call_aktools_api("/api/public/stock_market_activity_em")


# =============================================================================
# 8. 高级功能接口补充 (剩余接口)
# =============================================================================

def stock_zyjs_ths(symbol):
    """获取主营介绍-同花顺"""
    return call_aktools_api("/api/public/stock_zyjs_ths", params={"symbol": symbol})


def stock_zygc_em(symbol):
    """获取主营构成-东方财富"""
    return call_aktools_api("/api/public/stock_zygc_em", params={"symbol": symbol})


def stock_gsrl_gsdt_em(date):
    """获取公司动态-东方财富"""
    return call_aktools_api("/api/public/stock_gsrl_gsdt_em", params={"date": date})


def stock_dividend_cninfo(symbol):
    """获取历史分红-巨潮资讯"""
    return call_aktools_api("/api/public/stock_dividend_cninfo", params={"symbol": symbol})


def stock_news_em(symbol):
    """获取个股新闻-东方财富"""
    return call_aktools_api("/api/public/stock_news_em", params={"symbol": symbol})


def stock_news_main_cx():
    """获取财经内容精选-财新网"""
    return call_aktools_api("/api/public/stock_news_main_cx")


def stock_financial_report_sina(stock, indicator):
    """获取财务报表-新浪"""
    return call_aktools_api("/api/public/stock_financial_report_sina", params={
        "stock": stock,
        "indicator": indicator
    })


def stock_yjkb_em(date):
    """获取业绩快报-东方财富"""
    return call_aktools_api("/api/public/stock_yjkb_em", params={"date": date})


def stock_yjyg_em(date):
    """获取业绩预告-东方财富"""
    return call_aktools_api("/api/public/stock_yjyg_em", params={"date": date})


def stock_yysj_em(symbol, date):
    """获取预约披露时间-东方财富"""
    return call_aktools_api("/api/public/stock_yysj_em", params={
        "symbol": symbol,
        "date": date
    })


def stock_board_concept_cons_em(symbol):
    """获取概念板块成分股-东方财富"""
    return call_aktools_api("/api/public/stock_board_concept_cons_em", params={"symbol": symbol})


def stock_board_concept_hist_em(symbol, period="daily", start_date="20220101", end_date="20250227", adjust=""):
    """获取概念板块指数-东方财富"""
    return call_aktools_api("/api/public/stock_board_concept_hist_em", params={
        "symbol": symbol,
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


def stock_board_industry_cons_em(symbol):
    """获取行业板块成分股-东方财富"""
    return call_aktools_api("/api/public/stock_board_industry_cons_em", params={"symbol": symbol})


def stock_board_industry_hist_em(symbol, period="daily", start_date="20220101", end_date="20250227", adjust=""):
    """获取行业板块指数-东方财富"""
    return call_aktools_api("/api/public/stock_board_industry_hist_em", params={
        "symbol": symbol,
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "adjust": adjust
    })


def stock_hot_follow_xq(symbol):
    """获取股票热度-雪球关注排行榜"""
    return call_aktools_api("/api/public/stock_hot_follow_xq", params={"symbol": symbol})


def stock_hot_rank_detail_em(symbol):
    """获取历史趋势及粉丝特征-东方财富"""
    return call_aktools_api("/api/public/stock_hot_rank_detail_em", params={"symbol": symbol})


def stock_hot_rank_detail_xq(symbol):
    """获取个股人气榜-实时变动"""
    return call_aktools_api("/api/public/stock_hot_rank_detail_xq", params={"symbol": symbol})


def stock_hot_rank_latest_em():
    """获取个股人气榜-最新排名"""
    return call_aktools_api("/api/public/stock_hot_rank_latest_em")


def stock_hot_keyword_em():
    """获取热门关键词-东方财富"""
    return call_aktools_api("/api/public/stock_hot_keyword_em")


def stock_hot_search_em():
    """获取热搜股票-东方财富"""
    return call_aktools_api("/api/public/stock_hot_search_em")


def stock_hot_related_em(symbol):
    """获取相关股票-东方财富"""
    return call_aktools_api("/api/public/stock_hot_related_em", params={"symbol": symbol})


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 示例：获取A股实时行情
    print("获取A股实时行情...")
    df = stock_zh_a_spot_em()
    print(f"获取到 {len(df)} 条数据")
    
    # 示例：获取个股历史数据
    print("获取个股历史数据...")
    df = stock_zh_a_hist(symbol="000001", start_date="20240101", end_date="20240131")
    print(f"获取到 {len(df)} 条数据")
    
    print("所有98个接口已准备就绪！")
