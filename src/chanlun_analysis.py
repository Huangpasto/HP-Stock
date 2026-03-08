"""
缠论分析模块
包含：分型识别、笔的生成、中枢判断、三类买卖点
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def handle_inclusion(df: pd.DataFrame) -> pd.DataFrame:
    """
    处理包含关系（包含关系处理）
    缠论中的基本概念：相邻三根K线，如果中间一根的高低点都被前后两根包含，需要合并

    Args:
        df: 股票数据

    Returns:
        处理包含关系后的数据
    """
    df = df.copy()
    df = df.reset_index(drop=True)

    if len(df) < 3:
        return df

    i = 0
    while i < len(df) - 2:
        # 检查是否有包含关系
        curr_high = df.loc[i, 'high']
        curr_low = df.loc[i, 'low']
        next_high = df.loc[i + 1, 'high']
        next_low = df.loc[i + 1, 'low']

        # 判断包含方向
        if (next_high <= curr_high and next_low >= curr_low):
            # 向下包含（向右）
            new_high = max(curr_high, next_high)
            new_low = min(curr_low, next_low)
            df.loc[i, 'high'] = new_high
            df.loc[i, 'low'] = new_low
            df = df.drop(i + 1).reset_index(drop=True)
        elif (next_high >= curr_high and next_low <= curr_low):
            # 向上包含（向左）
            new_high = max(curr_high, next_high)
            new_low = min(curr_low, next_low)
            df.loc[i, 'high'] = new_high
            df.loc[i, 'low'] = new_low
            df = df.drop(i + 1).reset_index(drop=True)
        else:
            i += 1

    return df


def detect_fractals(df: pd.DataFrame) -> dict:
    """
    分型识别（顶分型、底分型）

    顶分型：中间K线的最高点最高，中间K线的最低点也最高
    底分型：中间K线的最低点最低，中间K线的最高点也最低

    Args:
        df: 股票数据

    Returns:
        分型识别结果
    """
    if len(df) < 5:
        return {'top_fractals': [], 'bottom_fractals': []}

    try:
        # 先处理包含关系
        df_processed = handle_inclusion(df)

        highs = df_processed['high'].values
        lows = df_processed['low'].values

        top_fractals = []  # 顶分型
        bottom_fractals = []  # 底分型

        for i in range(1, len(df_processed) - 1):
            # 顶分型
            if (highs[i] > highs[i-1] and highs[i] > highs[i+1] and
                lows[i] > lows[i-1] and lows[i] > lows[i+1]):
                top_fractals.append({
                    'index': i,
                    'high': highs[i],
                    'low': lows[i],
                    'date': df_processed.iloc[i]['date']
                })

            # 底分型
            elif (lows[i] < lows[i-1] and lows[i] < lows[i+1] and
                  highs[i] < highs[i-1] and highs[i] < highs[i+1]):
                bottom_fractals.append({
                    'index': i,
                    'high': highs[i],
                    'low': lows[i],
                    'date': df_processed.iloc[i]['date']
                })

        return {
            'top_fractals': top_fractals,
            'bottom_fractals': bottom_fractals
        }

    except Exception as e:
        logger.error(f"分型识别失败: {str(e)}")
        return {'top_fractals': [], 'bottom_fractals': []}


def generate_strokes(fractals: dict, min_bars: int = 5) -> list:
    """
    笔的生成
    连接相邻的顶分型和底分型，形成笔

    Args:
        fractals: 分型数据
        min_bars: 笔的最少K线数

    Returns:
        笔的列表
    """
    strokes = []

    top_fracs = fractals.get('top_fractals', [])
    bottom_fracs = fractals.get('bottom_fractals', [])

    if not top_fracs or not bottom_fracs:
        return strokes

    # 简化版笔生成：交替连接顶分型和底分型
    all_fracs = []
    for f in top_fracs:
        all_fracs.append(('top', f))
    for f in bottom_fracs:
        all_fracs.append(('bottom', f))

    # 按索引排序
    all_fracs.sort(key=lambda x: x[1]['index'])

    for i in range(len(all_fracs) - 1):
        if all_fracs[i][0] != all_fracs[i+1][0]:
            # 笔的幅度要求
            start_idx = all_fracs[i][1]['index']
            end_idx = all_fracs[i+1][1]['index']

            if end_idx - start_idx >= min_bars:
                stroke_type = 'up' if all_fracs[i][0] == 'bottom' else 'down'
                strokes.append({
                    'type': stroke_type,
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                    'start_price': all_fracs[i][1]['high'] if stroke_type == 'down' else all_fracs[i][1]['low'],
                    'end_price': all_fracs[i+1][1]['high'] if stroke_type == 'down' else all_fracs[i+1][1]['low']
                })

    return strokes


def identify_hub(strokes: list) -> dict:
    """
    中枢识别
    连续三笔或以上重叠区域形成中枢

    Args:
        strokes: 笔的列表

    Returns:
        中枢信息
    """
    if len(strokes) < 3:
        return {'exists': False, 'zhongshu': None}

    try:
        # 简化版中枢识别：找重叠区域
        for i in range(len(strokes) - 2):
            # 取连续三笔
            s1 = strokes[i]
            s2 = strokes[i + 1]
            s3 = strokes[i + 2]

            # 检查是否有重叠
            ranges = []
            for s in [s1, s2, s3]:
                if s['type'] == 'up':
                    ranges.append((s['start_price'], s['end_price']))
                else:
                    ranges.append((s['end_price'], s['start_price']))

            # 找重叠区间
            overlap_high = min([r[1] for r in ranges])
            overlap_low = max([r[0] for r in ranges])

            if overlap_high > overlap_low:
                return {
                    'exists': True,
                    'zhongshu': {
                        'high': overlap_high,
                        'low': overlap_low,
                        'range': overlap_high - overlap_low
                    },
                    'stroke_count': 3
                }

        return {'exists': False, 'zhongshu': None}

    except Exception as e:
        logger.error(f"中枢识别失败: {str(e)}")
        return {'exists': False, 'zhongshu': None}


def identify_buy_points(df: pd.DataFrame, strokes: list, hub: dict) -> dict:
    """
    三类买卖点识别

    第一类买卖点：趋势背驰后的转折点
    第二类买卖点：次级别回调不创新高/低的位置
    第三类买卖点：突破中枢后的回踩不回到中枢内

    Args:
        df: 股票数据
        strokes: 笔的列表
        hub: 中枢信息

    Returns:
        买卖点识别结果
    """
    result = {
        'type1_buy': False,
        'type2_buy': False,
        'type3_buy': False,
        'signals': []
    }

    try:
        current_price = df['close'].iloc[-1]

        if hub.get('exists'):
            zhongshu = hub['zhongshu']
            zhongshu_high = zhongshu['high']
            zhongshu_low = zhongshu['low']

            # 第三类买点：股价突破中枢后回调不回到中枢内
            if len(strokes) >= 3:
                last_stroke = strokes[-1]

                if last_stroke['type'] == 'up':
                    # 检查是否突破中枢
                    if last_stroke['end_price'] > zhongshu_high:
                        # 检查回调是否回到中枢内
                        if current_price > zhongshu_high:
                            result['type3_buy'] = True
                            result['signals'].append('第三类买点（突破中枢后回调不破）')

            # 第二类买点：回调不创新低
            if len(strokes) >= 2:
                last_stroke = strokes[-1]
                if last_stroke['type'] == 'up':
                    # 检查是否回调形成第二类买点
                    if current_price > last_stroke['start_price']:
                        result['type2_buy'] = True
                        result['signals'].append('第二类买点（回调不创新低）')

        # 第一类买点：需要通过背驰判断，这里简化处理
        if len(strokes) >= 2:
            # 简化：连续下跌后企稳
            last_two = strokes[-2:]
            if all(s['type'] == 'down' for s in last_two):
                result['type1_buy'] = True
                result['signals'].append('第一类买点（趋势背驰）')

        return result

    except Exception as e:
        logger.error(f"买卖点识别失败: {str(e)}")
        return result


def analyze_chanlun(df: pd.DataFrame, config: dict = None) -> dict:
    """
    缠论综合分析

    Args:
        df: 股票数据
        config: 配置参数

    Returns:
        缠论分析结果
    """
    if config is None:
        config = {'min_stroke_bars': 5, 'include_handling': True}

    result = {
        'strategy': '缠论',
        'fractals': {},
        'strokes': [],
        'hub': {},
        'buy_points': {},
        'signals': [],
        'recommendation': '观望'
    }

    try:
        # 1. 分型识别
        fractals = detect_fractals(df)
        result['fractals'] = fractals

        top_count = len(fractals.get('top_fractals', []))
        bottom_count = len(fractals.get('bottom_fractals', []))

        if top_count > 0 or bottom_count > 0:
            result['signals'].append(f'检测到 {top_count} 个顶分型，{bottom_count} 个底分型')

        # 2. 笔的生成
        strokes = generate_strokes(fractals, config.get('min_stroke_bars', 5))
        result['strokes'] = strokes

        if strokes:
            result['signals'].append(f'形成 {len(strokes)} 笔')

        # 3. 中枢识别
        hub = identify_hub(strokes)
        result['hub'] = hub

        if hub.get('exists'):
            result['signals'].append('形成中枢')

        # 4. 买卖点识别
        buy_points = identify_buy_points(df, strokes, hub)
        result['buy_points'] = buy_points
        result['signals'].extend(buy_points.get('signals', []))

        # 5. 综合评级
        signal_count = len(result['signals'])
        if buy_points.get('type3_buy'):
            result['recommendation'] = '强烈买入'
        elif buy_points.get('type2_buy') or buy_points.get('type1_buy'):
            result['recommendation'] = '买入'
        elif signal_count >= 2:
            result['recommendation'] = '关注'
        else:
            result['recommendation'] = '观望'

        return result

    except Exception as e:
        logger.error(f"缠论分析失败: {str(e)}")
        result['error'] = str(e)
        return result
