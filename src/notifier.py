"""
邮件通知模块
使用SMTP发送股票分析报告
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def create_html_report(results: list, date: str = None) -> str:
    """
    创建HTML格式的分析报告

    Args:
        results: 分析结果列表
        date: 日期

    Returns:
        HTML报告内容
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    # 统计买入信号
    strong_buy = [r for r in results if r.get('oneil', {}).get('recommendation') == '强烈买入' or
                  r.get('chanlun', {}).get('recommendation') == '强烈买入']
    buy = [r for r in results if r.get('oneil', {}).get('recommendation') == '买入' or
           r.get('chanlun', {}).get('recommendation') == '买入']
    watch = [r for r in results if r.get('oneil', {}).get('recommendation') == '关注' or
             r.get('chanlun', {}).get('recommendation') == '关注']

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>HP Stock Assistant - 每日股票分析报告</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .date {{ text-align: center; color: #7f8c8d; }}
            .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
            .summary-item {{ text-align: center; padding: 15px; border-radius: 8px; }}
            .strong-buy {{ background-color: #27ae60; color: white; }}
            .buy {{ background-color: #f39c12; color: white; }}
            .watch {{ background-color: #3498db; color: white; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #3498db; color: white; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .signal {{ padding: 5px 10px; border-radius: 5px; font-weight: bold; }}
            .signal-strong-buy {{ background-color: #27ae60; color: white; }}
            .signal-buy {{ background-color: #f39c12; color: white; }}
            .signal-watch {{ background-color: #3498db; color: white; }}
            .signal-hold {{ background-color: #95a5a6; color: white; }}
            .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 12px; }}
            .disclaimer {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📈 HP Stock Assistant</h1>
            <h2>每日股票分析报告</h2>
            <p class="date">日期：{date}</p>

            <div class="summary">
                <div class="summary-item strong-buy">
                    <h3>{len(strong_buy)}</h3>
                    <p>强烈买入</p>
                </div>
                <div class="summary-item buy">
                    <h3>{len(buy)}</h3>
                    <p>买入</p>
                </div>
                <div class="summary-item watch">
                    <h3>{len(watch)}</h3>
                    <p>关注</p>
                </div>
            </div>

            <h3>📊 详细分析</h3>
            <table>
                <thead>
                    <tr>
                        <th>股票代码</th>
                        <th>股票名称</th>
                        <th>当前价格</th>
                        <th>涨跌幅</th>
                        <th>欧奈尔</th>
                        <th>缠论</th>
                        <th>综合建议</th>
                    </tr>
                </thead>
                <tbody>
    """

    for r in results:
        code = r.get('code', '')
        name = r.get('name', '')
        price = r.get('price', 0)
        change = r.get('change', 0)

        oneil_rec = r.get('oneil', {}).get('recommendation', '观望')
        chanlun_rec = r.get('chanlun', {}).get('recommendation', '观望')

        # 确定最终建议
        if '强烈买入' in [oneil_rec, chanlun_rec]:
            final_rec = '强烈买入'
        elif '买入' in [oneil_rec, chanlun_rec]:
            final_rec = '买入'
        elif '关注' in [oneil_rec, chanlun_rec]:
            final_rec = '关注'
        else:
            final_rec = '观望'

        # 样式类
        signal_class = f'signal-{final_rec.lower().replace(" ", "-")}'

        html += f"""
                    <tr>
                        <td>{code}</td>
                        <td>{name}</td>
                        <td>{price:.2f}</td>
                        <td>{change:+.2f}%</td>
                        <td>{oneil_rec}</td>
                        <td>{chanlun_rec}</td>
                        <td><span class="signal {signal_class}">{final_rec}</span></td>
                    </tr>
        """

    html += """
                </tbody>
            </table>
    """

    # 添加详细信号
    html += """
            <h3>📋 技术信号详情</h3>
    """

    for r in results:
        code = r.get('code', '')
        name = r.get('name', '')

        oneil_signals = r.get('oneil', {}).get('signals', [])
        chanlun_signals = r.get('chanlun', {}).get('signals', [])

        html += f"""
            <div style="margin: 15px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #3498db;">
                <strong>{code} {name}</strong><br>
                <small>欧奈尔信号：{', '.join(oneil_signals) if oneil_signals else '无'}</small><br>
                <small>缠论信号：{', '.join(chanlun_signals) if chanlun_signals else '无'}</small>
            </div>
        """

    # 添加免责声明
    html += """
            <div class="disclaimer">
                <strong>⚠️ 免责声明</strong><br>
                本报告仅供学习参考，不构成任何投资建议。投资有风险，入市需谨慎。
                请根据自身风险承受能力做出投资决策。
            </div>

            <div class="footer">
                <p>HP Stock Assistant - 每日自动发送</p>
                <p>本报告由AI自动生成</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def send_email(results: list, config: dict) -> bool:
    """
    发送邮件

    Args:
        results: 分析结果
        config: 邮件配置

    Returns:
        是否发送成功
    """
    try:
        date = datetime.now().strftime('%Y-%m-%d')
        html_content = create_html_report(results, date)

        # 邮件配置
        smtp_server = config.get('smtp_server', 'smtp.qq.com')
        smtp_port = config.get('smtp_port', 587)
        email_user = config.get('email_user')
        email_pass = config.get('email_pass')
        email_to = config.get('email_to')

        if not email_user or not email_pass or not email_to:
            logger.error("邮件配置不完整")
            return False

        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📈 HP Stock Assistant - 每日股票分析报告 {date}'
        msg['From'] = email_user
        msg['To'] = email_to

        # 添加HTML内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # 发送邮件
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, email_to, msg.as_string())
        server.quit()

        logger.info(f"邮件发送成功：{email_to}")
        return True

    except Exception as e:
        logger.error(f"邮件发送失败: {str(e)}")
        return False


def send_test_email(config: dict) -> bool:
    """
    发送测试邮件

    Args:
        config: 邮件配置

    Returns:
        是否发送成功
    """
    test_results = [{
        'code': 'TEST',
        'name': '测试股票',
        'price': 100.00,
        'change': 1.23,
        'oneil': {
            'recommendation': '关注',
            'signals': ['RS评分达标 (85)', '趋势模板达标']
        },
        'chanlun': {
            'recommendation': '买入',
            'signals': ['形成中枢', '第二类买点']
        }
    }]

    return send_email(test_results, config)
