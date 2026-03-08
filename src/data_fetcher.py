"""
股票数据获取模块
使用AKShare获取A股、港股数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_stock_data_a股(stock_code: str, days: int = 250) -> pd.DataFrame:
    """
    获取A股股票数据

    Args:
        stock_code: 股票代码（如：300502）
        days: 获取天数

    Returns:
        包含OHLCV数据的DataFrame
    """
    try:
        # 判断股票市场
        if stock_code.startswith('6'):
            symbol = f"{stock_code}.SS"  # 上海交易所
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            symbol = f"{stock_code}.SZ"  # 深圳交易所
        elif stock_code.startswith('688'):
            symbol = f"{stock_code}.SH"  # 科创板
        else:
            symbol = f"{stock_code}.SZ"

        # 使用AKShare获取数据
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                start_date=(datetime.now() - timedelta(days=days)).strftime('%Y%m%d'),
                                end_date=datetime.now().strftime('%Y%m%d'),
                                adjust="qfq")

        # 标准化列名
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turnover'
        })

        # 转换日期格式
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        logger.info(f"成功获取A股股票 {stock_code} 的数据，共 {len(df)} 条记录")
        return df

    except Exception as e:
        logger.error(f"获取A股股票 {stock_code} 数据失败: {str(e)}")
        return pd.DataFrame()


def get_stock_data_港股(stock_code: str, days: int = 250) -> pd.DataFrame:
    """
    获取港股股票数据

    Args:
        stock_code: 股票代码（如：0700）
        days: 获取天数

    Returns:
        包含OHLCV数据的DataFrame
    """
    try:
        # 港股代码格式调整
        symbol = f"{stock_code}.HK"

        df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                start_date=(datetime.now() - timedelta(days=days)).strftime('%Y%m%d'),
                                end_date=datetime.now().strftime('%Y%m%d'),
                                adjust="qfq")

        # 标准化列名
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turnover'
        })

        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        logger.info(f"成功获取港股股票 {stock_code} 的数据，共 {len(df)} 条记录")
        return df

    except Exception as e:
        logger.error(f"获取港股股票 {stock_code} 数据失败: {str(e)}")
        return pd.DataFrame()


def get_stock_data(stock_code: str, market: str = "A股", days: int = 250) -> pd.DataFrame:
    """
    获取股票数据（统一入口）

    Args:
        stock_code: 股票代码
        market: 市场类型（A股/港股/美股）
        days: 获取天数

    Returns:
        包含OHLCV数据的DataFrame
    """
    if market == "A股":
        return get_stock_data_a股(stock_code, days)
    elif market == "港股":
        return get_stock_data_港股(stock_code, days)
    else:
        logger.warning(f"暂不支持市场类型: {market}")
        return pd.DataFrame()


def get_realtime_quote(stock_code: str, market: str = "A股") -> dict:
    """
    获取股票实时行情

    Args:
        stock_code: 股票代码
        market: 市场类型

    Returns:
        包含实时行情的字典
    """
    try:
        if market == "A股":
            if stock_code.startswith('6'):
                symbol = f"{stock_code}.SS"
            else:
                symbol = f"{stock_code}.SZ"
        else:
            symbol = stock_code

        df = ak.stock_zh_a_spot_em()
        stock_info = df[df['代码'] == stock_code]

        if len(stock_info) > 0:
            return {
                'code': stock_code,
                'name': stock_info.iloc[0]['名称'],
                'price': stock_info.iloc[0]['最新价'],
                'change': stock_info.iloc[0]['涨跌幅'],
                'volume': stock_info.iloc[0]['成交量'],
                'amount': stock_info.iloc[0]['成交额'],
                'amplitude': stock_info.iloc[0]['振幅'],
                'high': stock_info.iloc[0]['最高'],
                'low': stock_info.iloc[0]['最低'],
                'open': stock_info.iloc[0]['今开'],
                'close': stock_info.iloc[0]['昨收']
            }
    except Exception as e:
        logger.error(f"获取实时行情失败: {str(e)}")

    return {}
