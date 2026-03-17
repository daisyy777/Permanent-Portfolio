# Permanent Portfolio — Quantitative Strategy

A self-contained Python implementation of Harry Browne's **Permanent Portfolio** with dual-trigger rebalancing, risk monitoring, and performance reporting.

---

## Table of Contents

- [Strategy Overview](#strategy-overview)
- [Features](#features)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Output](#output)
- [Performance Metrics](#performance-metrics)
- [Project Structure](#project-structure)
- [Limitations](#limitations)

---

## Strategy Overview

The **Permanent Portfolio**, conceived by Harry Browne in the 1980s, allocates capital equally across four assets designed to thrive in different macroeconomic environments:

| Asset | Ticker | Weight | Economic Environment |
|-------|--------|--------|----------------------|
| US Equities | SPY | 25% | Prosperity |
| Long-term Treasuries | TLT | 25% | Deflation |
| Gold | GLD | 25% | Inflation |
| Short-term Treasuries / Cash | SHY | 25% | Recession |

The core thesis is that because no one can reliably predict which regime will dominate, holding all four equally provides robust risk-adjusted returns across all economic cycles.

---

## Features

- **Dual-trigger rebalancing** — calendar-based (monthly / quarterly / semiannual / annual) combined with a drift threshold (default 5%). Rebalancing fires whenever either condition is met.
- **Transaction cost modeling** — configurable one-way cost (default 0.1%) applied to every trade.
- **Offline / demo mode** — if `yfinance` data is unavailable, the script automatically falls back to synthetic prices generated with geometric Brownian motion (seed fixed at 42).
- **Risk monitoring** — rolling annualised volatility, drawdown series, historical-simulation VaR / CVaR at 95%, trailing-year correlation matrix, and automated alert checks.
- **Full performance report** — CAGR, annualised volatility, Sharpe ratio, Sortino ratio, Calmar ratio, max drawdown, win rate, best / worst year, and monthly returns table.
- **Benchmark comparison** — SPY buy-and-hold is computed alongside the portfolio for direct comparison.
- **CSV exports** — portfolio NAV, weights history, and rebalance log are written to disk automatically.

---

## Requirements

```
Python >= 3.10
pandas
numpy
yfinance
```

Install dependencies:

```bash
pip install pandas numpy yfinance
```

No `requirements.txt` is included yet; the above four packages are all that is needed.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/daisyy777/Permanent-Portfolio.git
cd Permanent-Portfolio

# Install dependencies
pip install pandas numpy yfinance

# Run the strategy
python PermanentPortfolio_english.py
```

The script will:
1. Download daily adjusted close prices for SPY, TLT, GLD, SHY from 2010-01-01 to 2024-12-31.
2. Run the backtest with quarterly + threshold rebalancing.
3. Print the full performance report to the console.
4. Save three CSV files in the working directory.

---

## Configuration

All parameters are set in the `main()` function at the bottom of `PermanentPortfolio_english.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `tickers` | `['SPY','TLT','GLD','SHY']` | Assets in the portfolio |
| `target_weights` | `[0.25, 0.25, 0.25, 0.25]` | Target allocation per asset |
| `start_date` | `2010-01-01` | Backtest start date |
| `end_date` | `2024-12-31` | Backtest end date |
| `initial_capital` | `1,000,000` | Starting capital (USD) |
| `rebal_freq` | `quarterly` | Calendar rebalance frequency |
| `rebal_thresh` | `0.05` | Drift band threshold (5%) |
| `tx_cost` | `0.001` | One-way transaction cost (0.1%) |

---

## Output

### Console

```
============================================================
           PERMANENT PORTFOLIO PERFORMANCE REPORT
============================================================
Period          : 2010-01-04 to 2024-12-31
Initial Capital : $1,000,000.00

--- Return Metrics ---
CAGR            : X.XX%
Total Return    : XX.XX%
...

--- Risk Metrics ---
Annual Volatility : X.XX%
Sharpe Ratio      : X.XX
Max Drawdown      : -X.XX%
...
```

### CSV Files

| File | Contents |
|------|----------|
| `portfolio_value.csv` | Daily portfolio NAV |
| `weights_history.csv` | Daily asset weights |
| `rebalance_log.csv` | Date, portfolio value, turnover, and transaction cost for every rebalance event |

---

## Performance Metrics

| Metric | Description |
|--------|-------------|
| CAGR | Compound annual growth rate |
| Annual Volatility | Annualised standard deviation of daily returns |
| Sharpe Ratio | Excess return over 4% risk-free rate, per unit of volatility |
| Sortino Ratio | Excess return per unit of downside deviation |
| Calmar Ratio | CAGR divided by max drawdown |
| Max Drawdown | Peak-to-trough decline |
| Win Rate | Proportion of months with positive returns |
| VaR 95% | Daily loss threshold not exceeded 95% of the time |
| CVaR 95% | Expected loss on the worst 5% of days |

---

## Project Structure

```
Permanent-Portfolio/
├── PermanentPortfolio_english.py   # Main strategy script (single file)
└── README.md                       # This file
```

---

## Limitations

- **Single-file design** — no modular packaging, tests, or CI pipeline.
- **No requirements.txt** — dependencies must be installed manually.
- **Survivorship bias** — ETFs (SPY, TLT, GLD, SHY) are used as proxies; their history starts at different dates (GLD: 2004, TLT: 2002, SHY: 2002, SPY: 1993).
- **Simplified transaction costs** — flat percentage; bid-ask spread and market impact are not modelled.
- **No tax handling** — turnover and capital gains taxes are ignored.
- **Simulated fallback data** — if `yfinance` fails, results are based on synthetic GBM prices and do not reflect reality.

---

---

# 永久投资组合 — 量化策略

基于哈里·布朗**永久投资组合**理论的 Python 量化策略实现，包含双触发再平衡机制、风险监控模块及完整的绩效分析报告。

---

## 目录

- [策略概述](#策略概述)
- [功能特性](#功能特性)
- [依赖环境](#依赖环境)
- [快速开始](#快速开始)
- [参数配置](#参数配置)
- [输出结果](#输出结果)
- [绩效指标说明](#绩效指标说明)
- [项目结构](#项目结构)
- [已知局限](#已知局限)

---

## 策略概述

**永久投资组合**由哈里·布朗于 20 世纪 80 年代提出，将资金等权分配至四类资产，以应对不同宏观经济环境：

| 资产 | 代码 | 权重 | 适用经济环境 |
|------|------|------|-------------|
| 美国股票 | SPY | 25% | 繁荣期 |
| 长期国债 | TLT | 25% | 通缩期 |
| 黄金 | GLD | 25% | 通胀期 |
| 短期国债 / 现金 | SHY | 25% | 衰退期 |

核心逻辑：由于无法可靠预测未来经济周期，等权持有四类资产可在所有宏观情景下提供稳健的风险调整收益。

---

## 功能特性

- **双触发再平衡** — 日历触发（每月 / 季度 / 半年 / 每年）与偏离阈值触发（默认 5%）同时支持，任一条件满足即执行再平衡。
- **交易成本建模** — 可配置的单向交易成本（默认 0.1%），每笔交易均扣除。
- **离线 / 演示模式** — 若 `yfinance` 数据获取失败，自动切换至几何布朗运动模拟价格（随机种子固定为 42），保证脚本始终可运行。
- **风险监控** — 滚动年化波动率、回撤序列、历史模拟法 95% VaR / CVaR、近一年资产相关性矩阵，以及自动预警检查。
- **完整绩效报告** — 年化复合收益率（CAGR）、年化波动率、夏普比率、索提诺比率、卡玛比率、最大回撤、月度胜率、最佳 / 最差年度、月度收益热力表。
- **基准对比** — 以 SPY 买入持有为基准，与组合业绩并排输出。
- **CSV 导出** — 自动保存组合净值、权重历史及再平衡日志至本地文件。

---

## 依赖环境

```
Python >= 3.10
pandas
numpy
yfinance
```

安装依赖：

```bash
pip install pandas numpy yfinance
```

项目目前未包含 `requirements.txt`，以上四个包即为全部依赖。

---

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/daisyy777/Permanent-Portfolio.git
cd Permanent-Portfolio

# 安装依赖
pip install pandas numpy yfinance

# 运行策略
python PermanentPortfolio_english.py
```

脚本执行流程：
1. 下载 SPY、TLT、GLD、SHY 从 2010-01-01 至 2024-12-31 的日度复权收盘价。
2. 以季度 + 阈值触发模式运行回测。
3. 在控制台打印完整绩效报告。
4. 在当前目录生成三个 CSV 文件。

---

## 参数配置

所有参数均在 `PermanentPortfolio_english.py` 底部的 `main()` 函数中设置：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tickers` | `['SPY','TLT','GLD','SHY']` | 资产 |
| `target_weights` | `[0.25, 0.25, 0.25, 0.25]` | 各资产目标权重 |
| `start_date` | `2010-01-01` | 回测开始日期 |
| `end_date` | `2024-12-31` | 回测结束日期 |
| `initial_capital` | `1,000,000` | 初始资金（美元） |
| `rebal_freq` | `quarterly` | 日历再平衡频率 |
| `rebal_thresh` | `0.05` | 偏离阈值（5%） |
| `tx_cost` | `0.001` | 单向交易成本（0.1%） |

---

## 输出结果

### 控制台

```
============================================================
           PERMANENT PORTFOLIO PERFORMANCE REPORT
============================================================
Period          : 2010-01-04 to 2024-12-31
Initial Capital : $1,000,000.00

--- Return Metrics ---
CAGR            : X.XX%
Total Return    : XX.XX%
...

--- Risk Metrics ---
Annual Volatility : X.XX%
Sharpe Ratio      : X.XX
Max Drawdown      : -X.XX%
...
```

### CSV 文件

| 文件名 | 内容 |
|--------|------|
| `portfolio_value.csv` | 每日组合净值 |
| `weights_history.csv` | 每日各资产权重 |
| `rebalance_log.csv` | 每次再平衡的日期、组合净值、换手率及交易成本 |

---

## 绩效指标说明

| 指标 | 说明 |
|------|------|
| CAGR | 年化复合增长率 |
| 年化波动率 | 日收益率的年化标准差 |
| 夏普比率 | 超额收益（无风险利率 4%）/ 波动率 |
| 索提诺比率 | 超额收益 / 下行偏差 |
| 卡玛比率 | CAGR / 最大回撤绝对值 |
| 最大回撤 | 峰值至谷值的最大跌幅 |
| 月度胜率 | 正收益月份占比 |
| VaR 95% | 95% 置信水平下的单日最大损失 |
| CVaR 95% | 最差 5% 交易日的平均损失 |

---

## 项目结构

```
Permanent-Portfolio/
├── PermanentPortfolio_english.py   # 主策略脚本（单文件）
└── README.md                       # 本文件
```

---

## 已知局限

- **单文件设计** — 无模块化封装、无单元测试、无 CI 流水线。
- **缺少 requirements.txt** — 需手动安装依赖。
- **幸存者偏差** — 使用现有 ETF 作为资产代理，各 ETF 上市日期不同（GLD: 2004 年，TLT: 2002 年，SHY: 2002 年，SPY: 1993 年）。
- **简化交易成本** — 仅按固定比例扣除，未建模买卖价差和市场冲击成本。
- **未考虑税务** — 换手产生的资本利得税未纳入计算。
- **模拟数据兜底** — 若 `yfinance` 获取失败，结果基于合成 GBM 价格，不反映真实市场表现。
