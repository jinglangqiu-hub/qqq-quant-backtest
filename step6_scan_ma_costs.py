import pandas as pd
import matplotlib.pyplot as plt

# ===== 0) 璇诲彇 CSV + 娓呮礂 Close锛堝鐢ㄦ渶绋崇増锛?=====
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
    raise ValueError(f"鎵句笉鍒?Close 鍒楋紝浣犲綋鍓嶇殑鍒楀悕鏄細{list(df_raw.columns)[:20]} ...")

df_raw["Close_num"] = pd.to_numeric(df_raw[close_col], errors="coerce")
df_raw = df_raw.dropna(subset=["Close_num"]).copy()

close = df_raw["Close_num"]

# ===== 1) 鍥炴祴鍑芥暟锛氬姞鍏ユ墜缁垂鍜屾粦鐐?=====
def backtest_with_costs(
    close: pd.Series,
    signal: pd.Series,
    initial_cash: float = 10000.0,
    fee_rate: float = 0.001,        # 0.1% 鎵嬬画璐?
    slippage_rate: float = 0.0005,  # 0.05% 婊戠偣
):
    cash = initial_cash
    shares = 0.0
    position = 0
    equity = []
    trades = 0

    for price, sig in zip(close.values, signal.values):
        sig = int(sig)

        # 涔板叆锛氫粠绌轰粨->鎸佷粨
        if sig == 1 and position == 0:
            exec_price = price * (1 + slippage_rate)  # 涔拌吹涓€鐐?
            # 鍏堟墸鎵嬬画璐癸紙鎸夋垚浜ら噾棰濇墸锛?
            # 鐢?cash 涔板叆锛歝ash = shares*exec_price*(1+fee_rate)
            shares = cash / (exec_price * (1 + fee_rate))
            cash = 0.0
            position = 1
            trades += 1

        # 鍗栧嚭锛氫粠鎸佷粨->绌轰粨
        elif sig == 0 and position == 1:
            exec_price = price * (1 - slippage_rate)  # 鍗栦究瀹滀竴鐐?
            gross = shares * exec_price
            cash = gross * (1 - fee_rate)             # 鍐嶆墸鎵嬬画璐?
            shares = 0.0
            position = 0
            trades += 1

        equity.append(cash + shares * price)

    equity = pd.Series(equity, index=close.index)
    final_equity = float(equity.iloc[-1])
    total_return = final_equity / initial_cash - 1.0

    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    max_drawdown = float(drawdown.min())

    return total_return, max_drawdown, trades

# ===== 2) 鍙傛暟鎵弿锛歁A = 5..200锛堝甫鎴愭湰锛?=====
FEE = 0.001        # 0.1%
SLIP = 0.0005      # 0.05%

results = []

for window in range(5, 201):
    ma = close.rolling(window=window).mean()
    tmp = pd.DataFrame({"Close": close, "MA": ma}).dropna()

    signal = (tmp["Close"] > tmp["MA"]).astype(int)

    total_ret, mdd, trades = backtest_with_costs(
        tmp["Close"],
        signal,
        initial_cash=10000.0,
        fee_rate=FEE,
        slippage_rate=SLIP
    )

    results.append({
        "MA": window,
        "TotalReturn": total_ret,
        "MaxDrawdown": mdd,
        "Trades": trades
    })

res = pd.DataFrame(results)

# ===== 3) 鎵撳嵃 Top 10锛堟敹鐩婃帓搴忥級 =====
top = res.sort_values("TotalReturn", ascending=False).head(10)
print(f"=== 甯︽垚鏈壂鎻?Top10 | fee={FEE*100:.2f}% slip={SLIP*100:.2f}% ===")
print(top.to_string(index=False))

# ===== 4) 鐢诲浘锛氭敹鐩?鍥炴挙/浜ゆ槗娆℃暟 =====
plt.figure(figsize=(12, 5))
plt.plot(res["MA"], res["TotalReturn"] * 100)
plt.title(f"MA Window vs Total Return (%)  (fee={FEE*100:.2f}%, slip={SLIP*100:.2f}%)")
plt.xlabel("MA Window (days)")
plt.ylabel("Total Return (%)")
plt.grid(True)
plt.show()

plt.figure(figsize=(12, 5))
plt.plot(res["MA"], res["MaxDrawdown"] * 100)
plt.title("MA Window vs Max Drawdown (%)  (closer to 0 is better)")
plt.xlabel("MA Window (days)")
plt.ylabel("Max Drawdown (%)")
plt.grid(True)
plt.show()

plt.figure(figsize=(12, 5))
plt.plot(res["MA"], res["Trades"])
plt.title("MA Window vs Number of Trades")
plt.xlabel("MA Window (days)")
plt.ylabel("Trades (count)")
plt.grid(True)
plt.show()
