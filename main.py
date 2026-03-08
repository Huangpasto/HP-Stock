"""
HP Stock Assistant - 主程序
每日股票分析自动发送系统
"""

import yaml
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 导入分析模块
from src.data_fetcher import get_stock_data, get_realtime_quote
from src.oneil_analysis import analyze_oneil
from src.chanlun_analysis import analyze_chanlun
from src.notifier import send_email, send_test_email

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """加载配置文件"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info("配置文件加载成功")
        return config
    except Exception as e:
        logger.error(f"配置文件加载失败: {str(e)}")
        sys.exit(1)


def load_email_config():
    """加载邮件配置"""
    load_dotenv()

    config = {
        'email_user': os.getenv('EMAIL_USER'),
        'email_pass': os.getenv('EMAIL_PASS'),
        'email_to': os.getenv('EMAIL_TO'),
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.qq.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587))
    }

    return config


def analyze_stock(stock_info: dict) -> dict:
    """
    分析单只股票

    Args:
        stock_info: 股票信息 {'code': '300502', 'name': '新易盛', 'market': 'A股'}

    Returns:
        分析结果
    """
    code = stock_info['code']
    name = stock_info['name']
    market = stock_info['market']

    logger.info(f"开始分析股票：{code} {name}")

    result = {
        'code': code,
        'name': name,
        'market': market,
        'price': 0,
        'change': 0,
        'oneil': {},
        'chanlun': {},
        'error': None
    }

    try:
        # 1. 获取实时行情
        quote = get_realtime_quote(code, market)
        if quote:
            result['price'] = quote.get('price', 0)
            result['change'] = quote.get('change', 0)
        else:
            logger.warning(f"获取实时行情失败：{code}")

        # 2. 获取历史数据进行分析
        df = get_stock_data(code, market, days=250)

        if df.empty:
            result['error'] = "无法获取股票数据"
            logger.error(f"获取股票数据失败：{code}")
            return result

        # 3. 欧奈尔分析
        oneil_result = analyze_oneil(df)
        result['oneil'] = oneil_result

        # 4. 缠论分析
        chanlun_result = analyze_chanlun(df)
        result['chanlun'] = chanlun_result

        logger.info(f"股票分析完成：{code} - 欧奈尔:{oneil_result.get('recommendation')}, 缠论:{chanlun_result.get('recommendation')}")

        return result

    except Exception as e:
        logger.error(f"股票分析出错：{code} - {str(e)}")
        result['error'] = str(e)
        return result


def main():
    """主函数"""
    logger.info("="*50)
    logger.info("HP Stock Assistant 每日股票分析开始")
    logger.info("="*50)

    # 加载配置
    config = load_config()
    email_config = load_email_config()

    # 检查邮件配置
    if not email_config['email_user'] or not email_config['email_pass']:
        logger.error("请在.env文件中配置邮件信息")
        sys.exit(1)

    # 获取关注的股票列表
    stocks = config.get('stocks', [])

    if not stocks:
        logger.error("配置文件中没有股票列表")
        sys.exit(1)

    logger.info(f"即将分析 {len(stocks)} 只股票")

    # 分析每只股票
    results = []
    for stock in stocks:
        result = analyze_stock(stock)
        results.append(result)

    # 统计结果
    strong_buy = sum(1 for r in results if
                    r.get('oneil', {}).get('recommendation') == '强烈买入' or
                    r.get('chanlun', {}).get('recommendation') == '强烈买入')

    buy = sum(1 for r in results if
              r.get('oneil', {}).get('recommendation') == '买入' or
              r.get('chanlun', {}).get('recommendation') == '买入')

    logger.info(f"分析完成：强烈买入 {strong_buy} 只，买入 {buy} 只")

    # 发送邮件
    logger.info("正在发送邮件...")
    success = send_email(results, email_config)

    if success:
        logger.info("邮件发送成功！")
    else:
        logger.error("邮件发送失败，请检查配置")

    logger.info("="*50)
    logger.info("HP Stock Assistant 每日股票分析完成")
    logger.info("="*50)


if __name__ == '__main__':
    main()
