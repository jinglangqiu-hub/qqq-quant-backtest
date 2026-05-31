import pandas as pd
import matplotlib.pyplot as plt

# ===== 1) 璇诲彇 CSV + 娓呮礂 Close =====
df = pd.read_csv("QQQ_10y_1d.csv")

date_col = df.columns[0]
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col]).set_index(date_col)
df.index.name = "Date"

def find_close_column(columns):
    for c in columns:
        if str(c).strip() == "Close":
            return c
    for c in columns:
        if "Close" in str(c):
            return c
    return None

close_col = find_close_column(df.columns)
if close_col is None:
    raise ValueError(f"鎵句笉鍒?Close 鍒楋紝浣犲綋鍓嶇殑鍒楀悕鏄細{list(df.columns)[:20]} ...")

df["Close_num"] = pd.to_numeric(df[close_col], errors="coerce")
df = df.dropna(subset=["Close_num"])

# ===== 2) 鐢熸垚绛栫暐淇″彿锛歁A20 瓒嬪娍璺熼殢 =====
df["MA20"] = df["Close_num"].rolling(window=20).mean()
df["signal"] = (df["Close_num"] > df["MA20"]).astype(int)

# 娉ㄦ剰锛氬墠 20 澶?MA20 涓虹┖锛屼俊鍙蜂細鏄?0锛屾垜浠妸杩欎簺澶╀涪鎺?
df = df.dropna(subset=["MA20"]).copy()

# ===== 3) 鍥炴祴锛氬叏浠撴寔鏈?/ 鍏ㄤ粨绌轰粨锛堟渶绠€鍗曠増鏈級 =====
initial_cash = 10000.0

cash = initial_cash
shares = 0.0
position = 0

equity_curve = []

for dt, row in df.iterrows():
    price = row["Close_num"]
    sig = int(row["signal"])

    if sig == 1 and position == 0:
        shares = cash / price
        cash = 0.0
        position = 1

    elif sig == 0 and position == 1:
        cash = shares * price
        shares = 0.0
        position = 0

    equity = cash + shares * price
    equity_curve.append(equity)

df["equity"] = equity_curve

# ===== 6) Buy & Hold 鍩哄噯绛栫暐 =====
bh_shares = initial_cash / df["Close_num"].iloc[0]
df["buy_hold_equity"] = bh_shares * df["Close_num"]

bh_final = df["buy_hold_equity"].iloc[-1]
bh_return = bh_final / initial_cash - 1

bh_running_max = df["buy_hold_equity"].cummax()
bh_drawdown = df["buy_hold_equity"] / bh_running_max - 1
bh_max_drawdown = bh_drawdown.min()

# ===== 4) 杈撳嚭鍏抽敭鎸囨爣锛堟渶灏忛泦鍚堬級 =====
df["equity_return"] = df["equity"].pct_change().fillna(0.0)

final_equity = df["equity"].iloc[-1]
total_return = final_equity / initial_cash - 1

running_max = df["equity"].cummax()
drawdown = df["equity"] / running_max - 1
max_drawdown = drawdown.min()

print("========== 鍥炴祴缁撴灉瀵规瘮 ==========")
print(f"MA20 Strategy")
print(f"  Initial cash: {initial_cash:.2f}")
print(f"  Final equity: {final_equity:.2f}")
print(f"  Total return: {total_return*100:.2f}%")
print(f"  Max drawdown: {max_drawdown*100:.2f}%")
print("")
print(f"Buy & Hold")
print(f"  Final equity: {bh_final:.2f}")
print(f"  Total return: {bh_return*100:.2f}%")
print(f"  Max drawdown: {bh_max_drawdown*100:.2f}%")
print("===================================")

# ===== 5) 鐢昏祫閲戞洸绾?=====
plt.figure(figsize=(12, 6))
plt.plot(df.index, df["equity"], label="MA20 Strategy", linewidth=2)
plt.plot(df.index, df["buy_hold_equity"], label="Buy & Hold", linestyle="--")
plt.title("Equity Curve Comparison (MA20 vs Buy & Hold)")
plt.xlabel("Date")
plt.ylabel("Equity ($)")
plt.legend()
plt.grid(True)
plt.show()
