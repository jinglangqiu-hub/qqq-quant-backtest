import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =============================
# 1. 璇诲彇鏁版嵁
# =============================
df = pd.read_csv("QQQ_10y_1d.csv")

date_col = df.columns[0]
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col]).set_index(date_col)
df.index.name = "Date"

def find_close_column(cols):
    for c in cols:
        if str(c).strip() == "Close":
            return c
    for c in cols:
        if "Close" in str(c):
            return c
    return None

close_col = find_close_column(df.columns)
df["Close"] = pd.to_numeric(df[close_col], errors="coerce")
df = df.dropna(subset=["Close"])

close = df["Close"]

# =============================
# 2. 璁＄畻鏀剁泭鐜?& 娉㈠姩鐜?
# =============================
returns = close.pct_change()

VOL_WINDOW = 20
annual_vol = returns.rolling(VOL_WINDOW).std() * np.sqrt(252)

# =============================
# 3. 绛栫暐 A锛氳秼鍔夸粨浣?
# =============================
MA = 180
K = 0.06

ma = close.rolling(MA).mean()
trend_weight = 0.5 + (close / ma - 1.0) / K
trend_weight = trend_weight.clip(0, 1)

# =============================
# 4. 娉㈠姩鐜囩洰鏍囷紙鍏抽敭锛?
# =============================
TARGET_VOL = 0.15   # 鐩爣骞村寲娉㈠姩 15%

vol_scaler = TARGET_VOL / annual_vol
vol_scaler = vol_scaler.clip(0, 1)

# 鏈€缁堜粨浣?= 瓒嬪娍浠撲綅 脳 娉㈠姩鐜囪皟鑺?
final_weight = trend_weight * vol_scaler

# 瀵归綈
data = pd.DataFrame({
    "Close": close,
    "Weight": final_weight
}).dropna()

# =============================
# 5. 鍥炴祴锛堝惈鎴愭湰锛?
# =============================
def backtest_weighted(close, weight, fee=0.001, slip=0.0005, init_cash=10000):
    cash = init_cash
    shares = 0.0
    equity = []
    trades = 0

    for price, w in zip(close.values, weight.values):
        total = cash + shares * price
        target_value = total * w
        current_value = shares * price
        diff = target_value - current_value

        if abs(diff) > total * 1e-6:
            trades += 1
            if diff > 0:
                exec_price = price * (1 + slip)
                buy_shares = diff / exec_price
                cost = buy_shares * exec_price
                fee_cost = cost * fee
                if cost + fee_cost > cash:
                    cost = cash / (1 + fee)
                    fee_cost = cost * fee
                    buy_shares = cost / exec_price
                cash -= (cost + fee_cost)
                shares += buy_shares
            else:
                exec_price = price * (1 - slip)
                sell_val = -diff
                sell_shares = min(sell_val / exec_price, shares)
                proceeds = sell_shares * exec_price
                fee_cost = proceeds * fee
                cash += proceeds - fee_cost
                shares -= sell_shares

        equity.append(cash + shares * price)

    equity = pd.Series(equity, index=close.index)
    ret = equity.iloc[-1] / init_cash - 1
    dd = equity / equity.cummax() - 1
    return equity, ret, dd.min(), trades


# =============================
# 6. 璺戝洖娴?
# =============================
equity, ret, mdd, trades = backtest_weighted(
    data["Close"],
    data["Weight"],
    fee=0.001,
    slip=0.0005
)

# Buy & Hold 瀵圭収
bh_shares = 10000 / data["Close"].iloc[0]
bh_equity = bh_shares * data["Close"]
bh_dd = bh_equity / bh_equity.cummax() - 1

print("===== 娉㈠姩鐜囨帶鍒剁瓥鐣?=====")
print(f"鎬绘敹鐩? {ret*100:.2f}%")
print(f"鏈€澶у洖鎾? {mdd*100:.2f}%")
print(f"璋冧粨娆℃暟: {trades}")

print("\n===== Buy & Hold =====")
print(f"鎬绘敹鐩? {(bh_equity.iloc[-1]/10000 - 1)*100:.2f}%")
print(f"鏈€澶у洖鎾? {bh_dd.min()*100:.2f}%")

# =============================
# 7. 鍙鍖?
# =============================
plt.figure(figsize=(12,6))
plt.plot(equity.index, equity, label="Vol Target Strategy")
plt.plot(bh_equity.index, bh_equity, label="Buy & Hold", linestyle="--")
plt.title("Volatility Targeting Strategy vs Buy & Hold")
plt.xlabel("Date")
plt.ylabel("Equity ($)")
plt.legend()
plt.grid(True)
plt.show()
