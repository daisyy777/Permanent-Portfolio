"""
Permanent Portfolio Quantitative Strategy
============================================
Strategy logic: Based on Harry Browne Permanent Portfolio
  - Stocks 25% (SPY)
  - Long-term bonds 25% (TLT)
  - Gold 25% (GLD)
  - Short-term bonds/cash 25% (SHY)

Modules:
  1. Data retrieval layer
  2. Backtest engine
  3. Rebalance logic (time + threshold triggers)
  4. Risk monitoring
  5. Performance analysis report
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# ── Data retrieval ──────────────────────────────────────────────────────────────────

def fetch_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """
    Download daily close prices.
    Requires: pip install yfinance
    Without network, replace with local CSV: pd.read_csv(...)
    """
    try:
        import yfinance as yf
        raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
        prices = raw["Close"][tickers]
    except Exception as e:
        print(f"[Warning] yfinance download failed: {e}")
        print("Using simulated random data instead (demo only)")
        prices = _simulate_prices(tickers, start, end)
    prices = prices.dropna(how="all").ffill()
    return prices


def _simulate_prices(tickers, start, end):
    """Generate simulated price series in offline environment (demo only)"""
    dates = pd.bdate_range(start, end)
    np.random.seed(42)
    # Assumed annual return and volatility
    params = {
        "SPY": (0.10, 0.18),
        "TLT": (0.05, 0.14),
        "GLD": (0.06, 0.16),
        "SHY": (0.03, 0.02),
    }
    data = {}
    for t in tickers:
        mu, sigma = params.get(t, (0.05, 0.15))
        dt = 1 / 252
        daily_ret = np.random.normal(mu * dt, sigma * np.sqrt(dt), len(dates))
        prices = 100 * np.cumprod(1 + daily_ret)
        data[t] = prices
    return pd.DataFrame(data, index=dates)


# ── Rebalance logic ────────────────────────────────────────────────────────────────

def get_rebalance_dates(prices: pd.DataFrame,
                        frequency: str = "quarterly") -> pd.DatetimeIndex:
    """Time-driven rebalance dates"""
    freq_map = {
        "monthly":   "ME",
        "quarterly": "QE",
        "semiannual":"6ME",
        "annual":    "YE",
    }
    rule = freq_map.get(frequency, "QE")
    dates = prices.resample(rule).last().index
    # Map month-end dates to actual trading days
    valid = []
    for d in dates:
        mask = prices.index <= d
        if mask.any():
            valid.append(prices.index[mask][-1])
    return pd.DatetimeIndex(valid)


def check_threshold_rebalance(weights: pd.Series,
                               target: pd.Series,
                               threshold: float = 0.05) -> bool:
    """Threshold rebalance trigger: rebalance if any asset deviates more than threshold"""
    return bool((weights - target).abs().max() > threshold)


# ── Backtest engine ──────────────────────────────────────────────────────────────────

class PermanentPortfolioBacktest:
    """
    Permanent PortfolioBacktest engine

    Parameters
    ----
    prices       : DataFrame, daily close prices
    target_w     : dict, target weights, default equal-weight 25%
    rebal_freq   : rebalance frequency, 'monthly'/'quarterly'/'annual'
    rebal_thresh : threshold trigger band, if exceeded rebalance, None means time-only
    initial_cap  : initial capital
    tx_cost      : one-way transaction cost (ratio)
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        target_w: dict | None = None,
        rebal_freq: str = "quarterly",
        rebal_thresh: float | None = 0.05,
        initial_cap: float = 1_000_000,
        tx_cost: float = 0.001,
    ):
        self.prices = prices.copy()
        self.tickers = list(prices.columns)
        n = len(self.tickers)
        self.target_w = pd.Series(
            target_w if target_w else {t: 1 / n for t in self.tickers}
        )
        self.rebal_freq = rebal_freq
        self.rebal_thresh = rebal_thresh
        self.initial_cap = initial_cap
        self.tx_cost = tx_cost

        # Result containers
        self.portfolio_value: pd.Series = pd.Series(dtype=float)
        self.weights_history: pd.DataFrame = pd.DataFrame()
        self.rebal_log: list[dict] = []

    def run(self) -> "PermanentPortfolioBacktest":
        """Run backtest, return self for chaining"""
        prices = self.prices
        dates = prices.index
        scheduled = set(get_rebalance_dates(prices, self.rebal_freq))

        # Initialization
        holdings = self.target_w * self.initial_cap / prices.iloc[0]
        port_values = []
        weights_hist = []

        for i, date in enumerate(dates):
            p = prices.loc[date]
            mv = (holdings * p).values          # Market value per asset
            total = mv.sum()
            w = pd.Series(mv / total, index=self.tickers)

            port_values.append(total)
            weights_hist.append(w.values)

            # Check whether to rebalance
            do_rebal = date in scheduled
            if not do_rebal and self.rebal_thresh is not None:
                do_rebal = check_threshold_rebalance(w, self.target_w, self.rebal_thresh)

            if do_rebal and i < len(dates) - 1:
                # Calculate turnover
                target_mv = self.target_w * total
                trades = target_mv - (holdings * p)
                cost = trades.abs().sum() * self.tx_cost
                total_after_cost = total - cost
                holdings = self.target_w * total_after_cost / p
                self.rebal_log.append({
                    "date": date,
                    "portfolio_value": round(total, 2),
                    "turnover": round(trades.abs().sum() / total, 4),
                    "tx_cost": round(cost, 2),
                })

        self.portfolio_value = pd.Series(port_values, index=dates, name="Portfolio")
        self.weights_history = pd.DataFrame(
            weights_hist, index=dates, columns=self.tickers
        )
        return self


# ── Risk monitoring ──────────────────────────────────────────────────────────────────

class RiskMonitor:
    """
    Realtime/offline risk monitoring

    Monitoring metrics:
      - Rolling volatility (annualized)
      - Drawdown series
      - VaR 95% / CVaR 95% (historical sim)
      - Correlation matrix (past 252 days)
    """

    def __init__(self, portfolio_value: pd.Series, asset_prices: pd.DataFrame):
        self.pv = portfolio_value
        self.prices = asset_prices
        self.returns = portfolio_value.pct_change().dropna()

    def rolling_volatility(self, window: int = 63) -> pd.Series:
        """Rolling quarterly volatility (annualized)"""
        return self.returns.rolling(window).std() * np.sqrt(252)

    def drawdown_series(self) -> pd.Series:
        """Drawdown series"""
        roll_max = self.pv.cummax()
        return (self.pv - roll_max) / roll_max

    def max_drawdown(self) -> float:
        return float(self.drawdown_series().min())

    def var_cvar(self, confidence: float = 0.95) -> tuple[float, float]:
        """Historical-simulation VaR and CVaR (daily)"""
        sorted_r = self.returns.sort_values()
        idx = int((1 - confidence) * len(sorted_r))
        var = float(sorted_r.iloc[idx])
        cvar = float(sorted_r.iloc[:idx].mean())
        return var, cvar

    def correlation_matrix(self, window: int = 252) -> pd.DataFrame:
        """Asset return correlation over the last window trading days"""
        ret = self.prices.pct_change().dropna()
        return ret.tail(window).corr().round(3)

    def alert_check(self,
                    vol_threshold: float = 0.20,
                    dd_threshold: float = -0.15) -> list[str]:
        """Trigger alerts, return alert messages list"""
        alerts = []
        current_vol = self.rolling_volatility().iloc[-1]
        current_dd = self.drawdown_series().iloc[-1]
        var, cvar = self.var_cvar()

        if current_vol > vol_threshold:
            alerts.append(
                f"⚠️  Volatility alert: current annual volatility {current_vol:.1%} > threshold {vol_threshold:.1%}"
            )
        if current_dd < dd_threshold:
            alerts.append(
                f"⚠️  Drawdown alert: current drawdown {current_dd:.1%} < threshold {dd_threshold:.1%}"
            )
        if var < -0.03:
            alerts.append(
                f"⚠️  VaR alert: daily VaR95 = {var:.2%}, tail risk elevated"
            )
        if not alerts:
            alerts.append("✅  All risk metrics are normal")
        return alerts


# ── Performance analysis report ──────────────────────────────────────────────────────────────

class PerformanceReport:
    """
    Generate a complete performance analysis report

    Includes: CAGR · Sharpe · Sortino · Max drawdown · Calmar ratio · monthly return heatmap
    """

    def __init__(self, portfolio_value: pd.Series,
                 benchmark_value: pd.Series | None = None,
                 rf_annual: float = 0.04):
        self.pv = portfolio_value
        self.bv = benchmark_value
        self.rf_daily = (1 + rf_annual) ** (1 / 252) - 1
        self.returns = portfolio_value.pct_change().dropna()

    # ── Core metrics ──────────────────────────────────────────────────────────────

    def cagr(self) -> float:
        n_years = len(self.pv) / 252
        return float((self.pv.iloc[-1] / self.pv.iloc[0]) ** (1 / n_years) - 1)

    def annual_volatility(self) -> float:
        return float(self.returns.std() * np.sqrt(252))

    def sharpe_ratio(self) -> float:
        excess = self.returns - self.rf_daily
        return float(excess.mean() / excess.std() * np.sqrt(252))

    def sortino_ratio(self) -> float:
        excess = self.returns - self.rf_daily
        downside = excess[excess < 0].std() * np.sqrt(252)
        return float(excess.mean() * 252 / downside) if downside > 0 else np.nan

    def max_drawdown(self) -> float:
        roll_max = self.pv.cummax()
        dd = (self.pv - roll_max) / roll_max
        return float(dd.min())

    def calmar_ratio(self) -> float:
        mdd = abs(self.max_drawdown())
        return float(self.cagr() / mdd) if mdd > 0 else np.nan

    def win_rate(self) -> float:
        return float((self.returns > 0).mean())

    def best_worst_year(self) -> dict:
        annual = self.returns.resample("YE").apply(lambda x: (1 + x).prod() - 1)
        return {
            "best_year":  (annual.idxmax().year, float(annual.max())),
            "worst_year": (annual.idxmin().year, float(annual.min())),
        }

    def monthly_returns_table(self) -> pd.DataFrame:
        """Monthly returns pivot table, rows=year, columns=month"""
        monthly = self.returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
        tbl = monthly.groupby([monthly.index.year, monthly.index.month]).first().unstack()
        tbl.columns = ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"]
        return tbl.round(4)

    def summary(self) -> pd.Series:
        bw = self.best_worst_year()
        return pd.Series({
            "Initial capital":       f"${self.pv.iloc[0]:,.0f}",
            "Final capital":       f"${self.pv.iloc[-1]:,.0f}",
            "Total return":         f"{(self.pv.iloc[-1]/self.pv.iloc[0]-1):.2%}",
            "CAGR (annual return)": f"{self.cagr():.2%}",
            "Annual volatility":      f"{self.annual_volatility():.2%}",
            "Sharpe ratio":        f"{self.sharpe_ratio():.2f}",
            "Sortino ratio":      f"{self.sortino_ratio():.2f}",
            "Max drawdown":        f"{self.max_drawdown():.2%}",
            "Calmar ratio":        f"{self.calmar_ratio():.2f}",
            "Win rate (daily)":      f"{self.win_rate():.2%}",
            "Best year":        f"{bw['best_year'][0]} ({bw['best_year'][1]:.2%})",
            "Worst year":        f"{bw['worst_year'][0]} ({bw['worst_year'][1]:.2%})",
        }, name="Permanent Portfolio")

    def print_report(self, risk_monitor: RiskMonitor | None = None,
                     rebal_log: list | None = None):
        """Print full report to console"""
        sep = "=" * 60

        print(f"\n{sep}")
        print("  Permanent Portfolio — Performance analysis report")
        print(sep)
        print(self.summary().to_string())

        if risk_monitor:
            print(f"\n{'─'*60}")
            print("  Risk monitoring")
            print(f"{'─'*60}")
            var, cvar = risk_monitor.var_cvar()
            print(f"  Daily VaR 95%  : {var:.3%}")
            print(f"  Daily CVaR 95% : {cvar:.3%}")
            print(f"\n  Asset correlation matrix (last 252 days):")
            print(risk_monitor.correlation_matrix().to_string())
            print(f"\n  Risk alerts:")
            for alert in risk_monitor.alert_check():
                print(f"  {alert}")

        if rebal_log:
            df_log = pd.DataFrame(rebal_log).set_index("date")
            print(f"\n{'─'*60}")
            print(f"  Rebalance records (total {len(df_log)} times)")
            print(f"{'─'*60}")
            print(df_log.tail(10).to_string())
            total_cost = df_log["tx_cost"].sum()
            print(f"\n  Cumulative transaction cost：${total_cost:,.2f}")

        print(f"\n  Monthly returns (%):")
        print((self.monthly_returns_table() * 100).round(2).to_string())
        print(f"\n{sep}\n")


# ── Main program ────────────────────────────────────────────────────────────────────

def main():
    # ── 1. Configure parameters ───────────────────────────────────────────────────────────
    TICKERS      = ["SPY", "TLT", "GLD", "SHY"]   # Stocks/long bonds/gold/short bonds
    START        = "2010-01-01"
    END          = "2024-12-31"
    INITIAL_CAP  = 1_000_000        # Initial capital $1,000,000
    REBAL_FREQ   = "quarterly"      # Quarterly rebalance
    REBAL_THRESH = 0.05             # Any asset deviation ±5% triggers extra rebalance
    TX_COST      = 0.001            # One-way 0.1% transaction cost

    # ── 2. Fetch data ───────────────────────────────────────────────────────────
    print("Fetching price data...")
    prices = fetch_prices(TICKERS, START, END)
    print(f"Data range: {prices.index[0].date()} → {prices.index[-1].date()}, "
          f"{len(prices)} trading days\n")

    # ── 3. Run backtest ───────────────────────────────────────────────────────────
    print("Running backtest engine...")
    bt = PermanentPortfolioBacktest(
        prices=prices,
        rebal_freq=REBAL_FREQ,
        rebal_thresh=REBAL_THRESH,
        initial_cap=INITIAL_CAP,
        tx_cost=TX_COST,
    ).run()

    # ── 4. Risk monitoring ───────────────────────────────────────────────────────────
    risk = RiskMonitor(bt.portfolio_value, prices)

    # ── 5. Benchmark: buy and hold SPY ─────────────────────────────────────────────────
    spy_bm = (prices["SPY"] / prices["SPY"].iloc[0]) * INITIAL_CAP

    # ── 6. Performance report ───────────────────────────────────────────────────────────
    report = PerformanceReport(bt.portfolio_value, benchmark_value=spy_bm)
    report.print_report(risk_monitor=risk, rebal_log=bt.rebal_log)

    # ── 7. Optional: export results to CSV ───────────────────────────────────────────────
    bt.portfolio_value.to_csv("portfolio_value.csv", header=True)
    bt.weights_history.to_csv("weights_history.csv")
    pd.DataFrame(bt.rebal_log).to_csv("rebalance_log.csv", index=False)
    print("Results exported: portfolio_value.csv / weights_history.csv / rebalance_log.csv")


if __name__ == "__main__":
    main()