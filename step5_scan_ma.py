import pandas as pd
import matplotlib.pyplot as plt

# ===== 0) 璇诲彇 CSV + 娓呮礂 Close锛堝鐢ㄤ綘鍓嶉潰鐨勨€滄渶绋崇増鈥濓級 =====
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

# ===== 1) 鍥炴祴鍑芥暟锛氱粰瀹?signal(0/1)锛岃繑鍥炴敹鐩?鍥炴挙/浜ゆ槗娆℃暟 =====
def backtest_all_in_all_out(close: pd.Series, signal: pd.Series, initial_cash: float = 10000.0):
    cash = initial_cash
    shares = 0.0
    position = 0

    equity = []
    trades = 0

    for price, sig in zip(close.values, signal.values):
        sig = int(sig)

        # 涔板叆
        if sig == 1 and position == 0:
            shares = cash / price
            cash = 0.0
            position = 1
            trades += 1

        # 鍗栧嚭
        elif sig == 0 and position == 1:
            cash = shares * price
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

# ===== 2) 鍙傛暟鎵弿锛歁A = 5..200 =====
results = []
close = df_raw["Close_num"]

for window in range(5, 201):
    ma = close.rolling(window=window).mean()
    tmp = pd.DataFrame({"Close": close, "MA": ma}).dropna()

    # 淇″彿锛欳lose > MA 鈫?1锛屽惁鍒?0
    signal = (tmp["Close"] > tmp["MA"]).astype(int)

    total_ret, mdd, trades = backtest_all_in_all_out(tmp["Close"], signal, initial_cash=10000.0)

    results.append({
        "MA": window,
        "TotalReturn": total_ret,
        "MaxDrawdown": mdd,
        "Trades": trades
    })

res = pd.DataFrame(results)

# ===== 3) 鎵锯€滅湅璧锋潵鏈€寮衡€濈殑鍑犱釜锛堝厛鐢ㄦ敹鐩婃帓搴忥級 =====
top = res.sort_values("TotalReturn", ascending=False).head(10)
print("=== 鎬绘敹鐩?Top 10锛堜粎渚涜瀵燂紝涓嶇瓑浜庢渶浣筹級===")
print(top.to_string(index=False))

# ===== 4) 鐢诲浘锛氭敹鐩娿€佸洖鎾ゃ€佷氦鏄撴鏁伴殢 MA 鍙樺寲 =====
plt.figure(figsize=(12, 5))
plt.plot(res["MA"], res["TotalReturn"] * 100)
plt.title("MA Window vs Total Return (%)")
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
