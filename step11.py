import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


CSV_PATH = "QQQ_10y_1d.csv"
INITIAL_CAPITAL = 10000.0


def find_close_column(columns):
    for col in columns:
        if str(col).strip() == "Close":
            return col
    for col in columns:
        if "Close" in str(col):
            return col
    return None


def max_drawdown(equity_series):
    running_max = equity_series.cummax()
    drawdown = equity_series / running_max - 1.0
    return drawdown.min(), drawdown


df = pd.read_csv(CSV_PATH)

date_col = df.columns[0]
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col]).set_index(date_col)
df.index.name = "Date"

close_col = find_close_column(df.columns)
if close_col is None:
    raise ValueError(f"Could not find Close column. Columns: {list(df.columns)}")

df["Close"] = pd.to_numeric(df[close_col], errors="coerce")
df = df.dropna(subset=["Close"]).copy()

df["MA20"] = df["Close"].rolling(window=20).mean()
df["MA60"] = df["Close"].rolling(window=60).mean()
df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
df["MACD"] = df["EMA12"] - df["EMA26"]
df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

df = df.dropna(subset=["MA20", "MA60"]).copy()

# Golden cross: MA20 moves above MA60. Death cross: MA20 moves below MA60.
df["signal"] = (df["MA20"] > df["MA60"]).astype(int)
df["signal_prev"] = df["signal"].shift(1).fillna(0).astype(int)
df["golden_cross"] = (df["signal"] == 1) & (df["signal_prev"] == 0)
df["death_cross"] = (df["signal"] == 0) & (df["signal_prev"] == 1)

# Use previous day's position to avoid look-ahead bias.
df["position"] = df["signal"].shift(1).fillna(0)
df["daily_return"] = df["Close"].pct_change().fillna(0.0)
df["strategy_return"] = df["position"] * df["daily_return"]
df["equity"] = INITIAL_CAPITAL * (1.0 + df["strategy_return"]).cumprod()

final_equity = df["equity"].iloc[-1]
total_return = final_equity / INITIAL_CAPITAL - 1.0

trading_days = len(df)
annualized_return = (final_equity / INITIAL_CAPITAL) ** (252 / trading_days) - 1.0

mdd, drawdown = max_drawdown(df["equity"])
df["drawdown"] = drawdown

trade_count = int(df["golden_cross"].sum())

print("========== MA20 / MA60 Simple Backtest ==========")
print(f"Initial capital : {INITIAL_CAPITAL:.2f}")
print(f"Final equity    : {final_equity:.2f}")
print(f"Total return    : {total_return * 100:.2f}%")
print(f"Annualized return: {annualized_return * 100:.2f}%")
print(f"Max drawdown    : {mdd * 100:.2f}%")
print(f"Trade count     : {trade_count}")
print("=================================================")

buy_points = df[df["golden_cross"]]
sell_points = df[df["death_cross"]]

fig_price, ax_price = plt.subplots(figsize=(14, 6))

ax_price.plot(df.index, df["Close"], label="Close", color="black", linewidth=1.5)
ax_price.plot(df.index, df["MA20"], label="MA20", linewidth=1.2)
ax_price.plot(df.index, df["MA60"], label="MA60", linewidth=1.2)
ax_price.scatter(
    buy_points.index,
    buy_points["Close"],
    marker="^",
    s=80,
    color="green",
    label="Buy",
    zorder=3,
)
ax_price.scatter(
    sell_points.index,
    sell_points["Close"],
    marker="v",
    s=80,
    color="red",
    label="Sell",
    zorder=3,
)
ax_price.set_title("QQQ Price with MA20 / MA60 Crossovers")
ax_price.set_xlabel("Date")
ax_price.set_ylabel("Price")
ax_price.legend()
ax_price.grid(True, alpha=0.3)
fig_price.tight_layout()

fig_macd, ax_macd = plt.subplots(figsize=(14, 5))
ax_macd.plot(df.index, df["MACD"], label="MACD", color="tab:blue", linewidth=1.2)
ax_macd.plot(df.index, df["MACD_signal"], label="Signal", color="tab:orange", linewidth=1.2)
hist_colors = np.where(df["MACD_hist"] >= 0, "green", "red")
ax_macd.bar(df.index, df["MACD_hist"], label="Histogram", color=hist_colors, alpha=0.4)
ax_macd.axhline(0, color="gray", linewidth=1, linestyle="--")
ax_macd.set_title("MACD")
ax_macd.set_xlabel("Date")
ax_macd.set_ylabel("MACD")
ax_macd.legend()
ax_macd.grid(True, alpha=0.3)
fig_macd.tight_layout()

fig_equity, ax_equity = plt.subplots(figsize=(14, 5))
ax_equity.plot(df.index, df["equity"], label="Equity Curve", color="tab:blue", linewidth=2)
ax_equity.set_title("Total Equity Curve")
ax_equity.set_xlabel("Date")
ax_equity.set_ylabel("Equity")
ax_equity.legend()
ax_equity.grid(True, alpha=0.3)
fig_equity.tight_layout()

plt.show()
