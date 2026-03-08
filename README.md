# HP Stock Assistant - 每日股票分析自动发送系统

这是一个基于欧奈尔信徒交易体系和缠论的每日股票分析系统，每天自动分析您关注的股票并发送建议到您的邮箱。

## 功能特点

- 📈 欧奈尔技术分析（杯柄形态、RS评分、趋势模板）
- 🧘 缠论分析（分型、笔、中枢、三类买卖点）
- 📧 每日自动邮件发送
- 🤖 GitHub Actions 定时执行（免费托管）

## 支持的股票

- A股（使用AKShare获取数据）
- 港股
- 美股

## 快速开始

### 1. 配置股票列表

编辑 `config.yaml` 文件，添加您关注的股票代码：

```yaml
stocks:
  - code: "300502"
    name: "新易盛"
    market: "A股"
  - code: "002384"
    name: "东山精密"
    market: "A股"
  # 添加更多股票...
```

### 2. 配置邮箱

在 `.env` 文件中配置邮箱信息：

```env
EMAIL_USER=your_email@qq.com
EMAIL_PASS=your授权码
EMAIL_TO=41526394@qq.com
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
```

### 3. 运行分析

```bash
pip install -r requirements.txt
python main.py
```

## GitHub Actions 自动执行

系统已配置GitHub Actions，每天自动运行并发送邮件。

运行时间：北京时间 20:00（交易日）

## 分析策略

### 欧奈尔信徒体系
- RS评分（相对强度）
- 杯柄形态识别
- 趋势模板（50日、150日、200日均线）

### 缠论体系
- 分型识别（顶分型、底分型）
- 笔的生成
- 中枢判断
- 三类买卖点

## 目录结构

```
HP-Stock/
├── .github/
│   └── workflows/
│       └── daily_analysis.yml
├── src/
│   ├── __init__.py
│   ├── data_fetcher.py
│   ├── oneil_analysis.py
│   ├── chanlun_analysis.py
│   └── notifier.py
├── config.yaml
├── main.py
├── requirements.txt
└── README.md
```

## 注意事项

1. 首次使用请配置邮箱SMTP授权码
2. GitHub Actions免费额度：每月2000分钟
3. 建议仅在工作日（周一至周五）发送分析

## 许可证

MIT License
