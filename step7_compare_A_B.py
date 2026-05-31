import pandas as pd
import matplotlib.pyplot as plt


df_raw = pd.read_csv("QQQ_10y_1d.csv")

date_col = df_raw.columns[0]
df_raw[date_col] = pd.to_datetime(df_raw[date_col], errors="coerce")
df_raw = df_raw.dropna(subset=[date_col]).set_index(date_col)
df_raw.index.name = "Date"


def find_close_column(columns):
    for c in columns:
        if str(c).strip() == "Close":
            return c
    for c in columns:
        if "Close" in str(c):
            return c
    return None


close_col = find_close_column(df_raw.columns)
if close_col is None:
    raise ValueError(f"Could not find Close column: {list(df_raw.columns)[:20]} ...")

df_raw["Close"] = pd.to_numeric(df_raw[close_col], errors="coerce")
df_raw = df_raw.dropna(subset=["Close"]).copy()
close = df_raw["Close"]


def backtest_target_weight(close: pd.Series, target_w: pd.Series, initial_cash: float = 10000.0,
                           fee_rate: float = 0.001, slippage_rate: float = 0.0005):
    cash = initial_cash
    shares = 0.0
    equity = []
    trades = 0

    for price, w in zip(close.values, target_w.values):
        w = float(max(0.0, min(1.0, w)))
        total = cash + shares * price
        target_value = total * w
        current_value = shares * price
        diff_value = target_value - current_value

        if abs(diff_value) > total * 1e-6:
            trades += 1
            if diff_value > 0:
                exec_price = price * (1 + slippage_rate)
                buy_shares = diff_value / exec_price
                cost = buy_shares * exec_price
                fee = cost * fee_rate
                if cost + fee > cash:
                    cost = cash / (1 + fee_rate)
                    fee = cost * fee_rate
                    buy_shares = cost / exec_price
                cash -= cost + fee
                shares += buy_shares
            else:
                exec_price = price * (1 - slippage_rate)
                sell_value = -diff_value
                sell_shares = min(sell_value / exec_price, shares)
                proceeds = sell_shares * exec_price
                fee = proceeds * fee_rate
                cash += proceeds - fee
                shares -= sell_shares

        equity.append(cash + shares * price)

    equity = pd.Series(equity, index=close.index)
    total_return = float(equity.iloc[-1] / initial_cash - 1.0)
    drawdown = equity / equity.cummax() - 1.0
    max_drawdown = float(drawdown.min())
    return equity, total_return, max_drawdown, trades


A_MA = 180
A_K = 0.06
ma_a = close.rolling(A_MA).mean()
tmp_a = pd.DataFrame({"Close": close, "MA": ma_a}).dropna()
tmp_a["w_A"] = 0.5 + (tmp_a["Close"] / tmp_a["MA"] - 1.0) / A_K
tmp_a["w_A"] = tmp_a["w_A"].clip(0.0, 1.0)

B_FAST = 50
B_SLOW = 200
B_K = 0.05
ma_fast = close.rolling(B_FAST).mean()
ma_slow = close.rolling(B_SLOW).mean()
tmp_b = pd.DataFrame({"Close": close, "fast": ma_fast, "slow": ma_slow}).dropna()
tmp_b["strength"] = (tmp_b["fast"] / tmp_b["slow"] - 1.0) / B_K
tmp_b["w_B"] = tmp_b["strength"].clip(0.0, 1.0)

start = max(tmp_a.index.min(), tmp_b.index.min())
close_aligned = close[close.index >= start]
w_a = tmp_a["w_A"].reindex(close_aligned.index).ffill().fillna(0.0)
w_b = tmp_b["w_B"].reindex(close_aligned.index).ffill().fillna(0.0)

initial_cash = 10000.0
bh_shares = initial_cash / close_aligned.iloc[0]
bh_equity = bh_shares * close_aligned
bh_drawdown = bh_equity / bh_equity.cummax() - 1.0
bh_mdd = float(bh_drawdown.min())
bh_return = float(bh_equity.iloc[-1] / initial_cash - 1.0)

FEE = 0.001
SLIP = 0.0005

eq_a, ret_a, mdd_a, trades_a = backtest_target_weight(close_aligned, w_a, initial_cash, FEE, SLIP)
eq_b, ret_b, mdd_b, trades_b = backtest_target_weight(close_aligned, w_b, initial_cash, FEE, SLIP)

print("========== A vs B vs Buy&Hold ==========")
print(f"Costs: fee={FEE*100:.2f}% slip={SLIP*100:.2f}%")
print(f"[Strategy A] MA={A_MA} K={A_K} return={ret_a*100:.2f}% mdd={mdd_a*100:.2f}% trades={trades_a}")
print(f"[Strategy B] fast={B_FAST} slow={B_SLOW} K={B_K} return={ret_b*100:.2f}% mdd={mdd_b*100:.2f}% trades={trades_b}")
print(f"[Buy & Hold] return={bh_return*100:.2f}% mdd={bh_mdd*100:.2f}%")
print("========================================")

plt.figure(figsize=(12, 6))
plt.plot(eq_a.index, eq_a.values, label="A: Continuous Weight")
plt.plot(eq_b.index, eq_b.values, label="B: Dual MA Weight")
plt.plot(bh_equity.index, bh_equity.values, label="Buy & Hold", linestyle="--")
plt.title("Equity Curve Comparison (A vs B vs Buy & Hold)")
plt.xlabel("Date")
plt.ylabel("Equity ($)")
plt.legend()
plt.grid(True)
plt.show()
