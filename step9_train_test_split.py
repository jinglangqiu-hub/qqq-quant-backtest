import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# 1. 璇诲彇鏁版嵁
# =========================
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

df["Close"] = pd.to_numeric(df[find_close_column(df.columns)], errors="coerce")
df = df.dropna(subset=["Close"])

close = df["Close"]

# =========================
# 2. 鍥炴祴鍑芥暟锛堝鐢ㄤ箣鍓嶏級
# =========================
def backtest_vol_target(close, weight, fee=0.001, slip=0.0005, init_cash=10000):
    cash = init_cash
    shares = 0.0
    equity = []

    for price, w in zip(close.values, weight.values):
        total = cash + shares * price
        target_val = total * w
        cur_val = shares * price
        diff = target_val - cur_val

        if abs(diff) > total * 1e-6:
            if diff > 0:
                exec_price = price * (1 + slip)
                buy_val = diff
                buy_shares = buy_val / exec_price
                cost = buy_shares * exec_price
                fee_cost = cost * fee
                if cost + fee_cost > cash:
                    cost = cash / (1 + fee)
                    fee_cost = cost * fee
                    buy_shares = cost / exec_price
                cash -= cost + fee_cost
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
    mdd = (equity / equity.cummax() - 1).min()
    return equity, ret, mdd


# =========================
# 3. 鍒掑垎璁粌 / 娴嬭瘯
# =========================
train_end = "2020-12-31"

train = df.loc[:train_end].copy()
test = df.loc[train_end:].copy()

# =========================
# 4. 鍦ㄨ缁冮泦涓婇€夊弬鏁?
# =========================
best_score = -1e9
best_params = None

for MA in range(120, 221, 10):
    for K in [0.04, 0.05, 0.06, 0.08]:
        ma = train["Close"].rolling(MA).mean()
        w = 0.5 + (train["Close"] / ma - 1) / K
        w = w.clip(0, 1)

        eq, ret, mdd = backtest_vol_target(train["Close"], w)

        # 涓€涓畝鍗曠殑璇勫垎鍑芥暟锛堜綘浠ュ悗鍙互鏀癸級
        score = ret + 2 * mdd   # mdd 鏄礋鏁帮紝鐩稿綋浜庢儵缃?

        if score > best_score:
            best_score = score
            best_params = (MA, K, ret, mdd)

print("===== 璁粌鏈熸渶浼樺弬鏁?=====")
print("MA =", best_params[0], " K =", best_params[1])
print("璁粌鏈熸敹鐩?", f"{best_params[2]*100:.2f}%")
print("璁粌鏈熸渶澶у洖鎾?", f"{best_params[3]*100:.2f}%")

# =========================
# 5. 鐢ㄥ悓鏍峰弬鏁拌窇銆愭祴璇曟湡銆?
# =========================
MA, K = best_params[0], best_params[1]

ma_test = test["Close"].rolling(MA).mean()
w_test = 0.5 + (test["Close"] / ma_test - 1) / K
w_test = w_test.clip(0, 1)

eq_test, ret_test, mdd_test = backtest_vol_target(test["Close"], w_test)

# Buy & Hold 娴嬭瘯鏈?
bh_shares = 10000 / test["Close"].iloc[0]
bh_equity = bh_shares * test["Close"]
bh_ret = bh_equity.iloc[-1] / 10000 - 1
bh_mdd = (bh_equity / bh_equity.cummax() - 1).min()

print("\n===== 娴嬭瘯鏈熺粨鏋滐紙Out-of-Sample锛?====")
print(f"绛栫暐鏀剁泭: {ret_test*100:.2f}%   鏈€澶у洖鎾? {mdd_test*100:.2f}%")
print(f"Buy&Hold 鏀剁泭: {bh_ret*100:.2f}%   鏈€澶у洖鎾? {bh_mdd*100:.2f}%")

# =========================
# 6. 鍙鍖?
# =========================
plt.figure(figsize=(12,6))
plt.plot(eq_test.index, eq_test, label="Strategy (OOS)")
plt.plot(bh_equity.index, bh_equity, label="Buy & Hold", linestyle="--")
plt.title("Out-of-Sample Performance (Test Period)")
plt.xlabel("Date")
plt.ylabel("Equity ($)")
plt.legend()
plt.grid(True)
plt.show()
