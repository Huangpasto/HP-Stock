"""
欧奈尔信徒交易体系分析模块
包含：RS评分、趋势模板、杯柄形态识别
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def calculate_rps(df: pd.DataFrame, periods: list = [3, 6, 12],
                  weights: list = [0.4, 0.2, 0.4]) -> float:
    """
    计算RS评分（相对强度评分）

    Args:
        df: 股票数据
        periods: 评分周期（月）
        weights: 各周期权重

    Returns:
        RS评分 (0-100)
    """
    if len(df) < 250:
        logger.warning(f"数据不足250天，无法计算RS评分")
        return 0

    try:
        # 计算各周期涨跌幅
        rps_values = []
        for period in periods:
            days = period * 21  # 每月约21个交易日
            if len(df) >= days:
                current_price = df['close'].iloc[-1]
                past_price = df['close'].iloc[-days]
                pct_change = (current_price - past_price) / past_price * 100
                rps_values.append(pct_change)
            else:
                rps_values.append(0)

        # 加权计算RS评分
        weighted_rps = sum(r * w for r, w in zip(rps_values, weights))

        # 转换为0-100评分（假设最高涨跌幅为100%）
        rps_score = min(100, max(0, (weighted_rps + 50)))

        return round(rps_score, 2)

    except Exception as e:
        logger.error(f"计算RS评分失败: {str(e)}")
        return 0


def check_trend_template(df: pd.DataFrame) -> dict:
    """
    检查趋势模板（Trend Template）
    条件：
    1. 股价 > 50日均线 > 150日均线 > 200日均线
    2. 股价距52周低点上涨超过30%
    3. 股价距52周高点在25%以内

    Args:
        df: 股票数据

    Returns:
        趋势模板检查结果
    """
    if len(df) < 200:
        return {'passed': False, 'reason': '数据不足200天'}

    try:
        # 计算均线
        df['MA50'] = df['close'].rolling(50).mean()
        df['MA150'] = df['close'].rolling(150).mean()
        df['MA200'] = df['close'].rolling(200).mean()

        current_price = df['close'].iloc[-1]
        ma50 = df['MA50'].iloc[-1]
        ma150 = df['MA150'].iloc[-1]
        ma200 = df['MA200'].iloc[-1]

        # 获取52周数据（约250天）
        df_52week = df.tail(250)
        low_52week = df_52week['low'].min()
        high_52week = df_52week['high'].max()

        # 检查条件
        conditions = {
            'price_above_ma50': current_price > ma50,
            'ma50_above_ma150': ma50 > ma150,
            'ma150_above_ma200': ma150 > ma200,
            'above_30_percent_low': (current_price - low_52week) / low_52week >= 0.30,
            'within_25_percent_high': (high_52week - current_price) / high_52week <= 0.25
        }

        passed = all(conditions.values())

        return {
            'passed': passed,
            'conditions': conditions,
            'current_price': current_price,
            'ma50': ma50,
            'ma150': ma150,
            'ma200': ma200,
            'low_52week': low_52week,
            'high_52week': high_52week,
            'distance_from_low': round((current_price - low_52week) / low_52week * 100, 2),
            'distance_from_high': round((high_52week - current_price) / high_52week * 100, 2)
        }

    except Exception as e:
        logger.error(f"检查趋势模板失败: {str(e)}")
        return {'passed': False, 'reason': str(e)}


def detect_cup_and_handle(df: pd.DataFrame, lookback: int = 50) -> dict:
    """
    检测杯柄形态（Cup and Handle）

    形态特征：
    1. 杯底：前期高点后下跌，形成U型底
    2. 左杯壁：杯底左侧的上升波段
    3. 右杯壁：杯底右侧的上升波段
    4. 杯柄：右杯壁高点后的短期回调整理

    Args:
        df: 股票数据
        lookback: 回溯检测天数

    Returns:
        杯柄形态检测结果
    """
    if len(df) < 60:
        return {'detected': False, 'reason': '数据不足60天'}

    try:
        df_recent = df.tail(lookback).copy()
        highs = df_recent['high'].values
        lows = df_recent['low'].values
        closes = df_recent['close'].values
        volumes = df_recent['volume'].values

        # 简化版杯柄检测
        # 1. 找到近期最高点
        max_idx = np.argmax(highs)
        max_price = highs[max_idx]

        # 2. 找到最高点后的回调区域（杯柄）
        if max_idx < len(highs) - 10:
            post_high = highs[max_idx:]
            post_low = lows[max_idx:]

            # 检查是否在回调（杯柄形成）
            handle_depth = (max_price - np.min(post_low)) / max_price

            # 3. 检查当前是否在盘整后向上突破
            current_price = closes[-1]
            handle_high = np.max(post_high[:-5]) if len(post_high) > 5 else max_price
            breakdown = current_price > handle_high

            # 4. 检查成交量
            avg_volume_50 = np.mean(volumes[-50:]) if len(volumes) >= 50 else np.mean(volumes)
            recent_volume = np.mean(volumes[-5:])
            volume_confirm = recent_volume > avg_volume_50 * 1.2

            # 综合判断
            detected = breakdown and (0.05 < handle_depth < 0.33)

            return {
                'detected': detected,
                'handle_depth': round(handle_depth * 100, 2),
                'breakdown': breakdown,
                'volume_confirm': volume_confirm,
                'max_price': max_price,
                'current_price': current_price
            }
        else:
            return {'detected': False, 'reason': '近期无明显高点'}

    except Exception as e:
        logger.error(f"检测杯柄形态失败: {str(e)}")
        return {'detected': False, 'reason': str(e)}


def check_pocket_pivot(df: pd.DataFrame) -> dict:
    """
    检测口袋支点（Pocket Pivot）
    出现在股价还没有突破前期最高点时

    Args:
        df: 股票数据

    Returns:
        口袋支点检测结果
    """
    if len(df) < 20:
        return {'detected': False, 'reason': '数据不足20天'}

    try:
        df_recent = df.tail(20).copy()
        volumes = df_recent['volume'].values
        closes = df_recent['close'].values
        lows = df_recent['low'].values

        # 找到过去10天中下跌日的最大成交量
        down_days = []
        for i in range(1, len(closes)):
            if closes[i] < closes[i-1]:
                down_days.append(volumes[i])

        max_down_volume = max(down_days) if down_days else 0

        # 检查今天是否放量大涨
        today_volume = volumes[-1]
        today_change = (closes[-1] - closes[-2]) / closes[-2] * 100

        # 口袋支点条件：
        # 1. 成交量超过过去10天最大下跌日成交量
        # 2. 股价上涨
        # 3. 收盘价在近期高位附近

        pocket_pivot = (today_volume > max_down_volume * 1.0 and
                       today_change > 0 and
                       closes[-1] > np.max(closes[:-1]) * 0.95)

        return {
            'detected': pocket_pivot,
            'today_volume': today_volume,
            'max_down_volume': max_down_volume,
            'today_change': round(today_change, 2),
            'volume_ratio': round(today_volume / max_down_volume, 2) if max_down_volume > 0 else 0
        }

    except Exception as e:
        logger.error(f"检测口袋支点失败: {str(e)}")
        return {'detected': False, 'reason': str(e)}


def analyze_oneil(df: pd.DataFrame, config: dict = None) -> dict:
    """
    欧奈尔体系综合分析

    Args:
        df: 股票数据
        config: 配置参数

    Returns:
        欧奈尔分析结果
    """
    if config is None:
        config = {'min_rps': 80, 'volume_multiplier': 1.4}

    result = {
        'strategy': '欧奈尔信徒',
        'rps_score': 0,
        'trend_template': {},
        'cup_handle': {},
        'pocket_pivot': {},
        'signals': [],
        'recommendation': '观望'
    }

    try:
        # 1. 计算RS评分
        rps = calculate_rps(df)
        result['rps_score'] = rps
        if rps >= config.get('min_rps', 80):
            result['signals'].append(f'RS评分达标 ({rps})')

        # 2. 检查趋势模板
        trend = check_trend_template(df)
        result['trend_template'] = trend
        if trend.get('passed'):
            result['signals'].append('趋势模板达标')

        # 3. 检测杯柄形态
        cup = detect_cup_and_handle(df)
        result['cup_handle'] = cup
        if cup.get('detected'):
            result['signals'].append('检测到杯柄形态')

        # 4. 检测口袋支点
        pocket = check_pocket_pivot(df)
        result['pocket_pivot'] = pocket
        if pocket.get('detected'):
            result['signals'].append('检测到口袋支点')

        # 5. 综合评级
        signal_count = len(result['signals'])
        if signal_count >= 3:
            result['recommendation'] = '强烈买入'
        elif signal_count >= 2:
            result['recommendation'] = '买入'
        elif signal_count >= 1:
            result['recommendation'] = '关注'
        else:
            result['recommendation'] = '观望'

        return result

    except Exception as e:
        logger.error(f"欧奈尔分析失败: {str(e)}")
        result['error'] = str(e)
        return result
