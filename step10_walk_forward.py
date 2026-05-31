import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
def ann_vol(close, window=20):
    r = close.pct_change()
    return r.rolling(window).std() * np.sqrt(252)

# ======================
# 璇诲彇鏁版嵁
# ======================
df = pd.read_csv("QQQ_10y_1d.csv")
df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
df = df.dropna().set_index(df.columns[0])
df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
df = df.dropna()

# ======================
# 鍥炴祴鍑芥暟锛堜綘宸茬粡寰堢啛浜嗭級
# ======================
def backtest(close, weight, fee=0.001, slip=0.0005, init_cash=10000):
    cash = init_cash
    shares = 0.0
    equity = []

    for price, w in zip(close, weight):
        total = cash + shares * price
        target = total * w
        cur = shares * price
        diff = target - cur

        if abs(diff) > 1e-6:
            if diff > 0:
                px = price * (1 + slip)
                buy = diff / px
                cost = buy * px
                fee_cost = cost * fee
                if cost + fee_cost > cash:
                    cost = cash / (1 + fee)
                    buy = cost / px
                    fee_cost = cost * fee
                cash -= cost + fee_cost
                shares += buy
            else:
                px = price * (1 - slip)
                sell = min(-diff / px, shares)
                proceeds = sell * px
                fee_cost = proceeds * fee
                cash += proceeds - fee_cost
                shares -= sell

        equity.append(cash + shares * price)

    equity = pd.Series(equity, index=close.index)
    ret = equity.iloc[-1] / equity.iloc[0] - 1
    mdd = (equity / equity.cummax() - 1).min()
    return equity, ret, mdd

BASE_W = 0.6        # 鍩虹椋庨櫓鏆撮湶锛氭€讳綋鎰挎剰鎷垮灏戜粨浣嶅湪甯傚満閲?
TARGET_VOL = 0.15   # 鐩爣骞村寲娉㈠姩

# ======================
# Walk-Forward 鍙傛暟
# ======================
train_years = 4
test_years = 1

years = sorted(df.index.year.unique())

results = []
equity_all = []
capital = 10000.0   # 鉁?鎺ュ姏璧勯噾锛氱涓€娈典粠10000寮€濮嬶紝鍚庨潰鐢ㄤ笂涓€娈电殑鏈熸湯

for i in range(train_years, len(years) - test_years):

    train_start = f"{years[i-train_years]}-01-01"
    train_end   = f"{years[i]-1}-12-31"
    test_start  = f"{years[i]}-01-01"
    test_end    = f"{years[i+test_years-1]}-12-31"

    train = df.loc[train_start:train_end]
    test  = df.loc[test_start:test_end]

    best_score = -1e9
    best_param = None

    # === 鍙傛暟鎼滅储 ===
    for MA in range(100, 221, 20):
        for K in [0.03, 0.04, 0.05, 0.06]:

            ma = train["Close"].rolling(MA).mean()

            # 鉁?瓒嬪娍淇″彿锛氬湪鍧囩嚎涓婃柟鎵嶅弬涓庯紙0/1 寮€鍏筹級
            trend_signal = (train["Close"] > ma).astype(float)

            # 鉁?娉㈠姩鐜囩缉鏀撅細娉㈠姩灏忓彲鍔犱粨锛屾尝鍔ㄥぇ鍑忎粨
            vol = ann_vol(train["Close"], window=20)
            vol_scaler = (TARGET_VOL / vol).clip(0.5, 2.0)

            # 鉁?鏈€缁堜粨浣嶏細鍩虹鏆撮湶 脳 瓒嬪娍寮€鍏?脳 娉㈠姩缂╂斁
            w = (BASE_W * trend_signal * vol_scaler).clip(0.2, 1.5)
            w = w.fillna(0.2)

            _, ret, mdd = backtest(train["Close"], w, init_cash=10000)  # 璁粌鏈熻瘎鍒嗙敤缁熶竴璧风偣鍗冲彲
            score = ret + 2 * mdd

            if score > best_score:
                best_score = score
                best_param = (MA, K)

    MA, K = best_param

    # === 娴嬭瘯鏈燂細鐢ㄢ€滄帴鍔涜祫閲?capital鈥?===
    ma_test = test["Close"].rolling(MA).mean()

    trend_signal_test = (test["Close"] > ma_test).astype(float)

    vol_test = ann_vol(test["Close"], window=20)
    vol_scaler_test = (TARGET_VOL / vol_test).clip(0.5, 2.0)

    w_test = (BASE_W * trend_signal_test * vol_scaler_test).clip(0.2, 1.5)
    w_test = w_test.fillna(0.2)
    eq_test, ret_test, mdd_test = backtest(test["Close"], w_test, init_cash=capital)

    # 鉁?鏇存柊鎺ュ姏璧勯噾
    capital = float(eq_test.iloc[-1])

    print(f"[{test_start[:4]}] MA={MA}, K={K} | Return={ret_test:.2%}, MDD={mdd_test:.2%} | End={capital:.2f}")

    # 鉁?鎷兼帴鏃堕伩鍏嶉噸澶嶆棩鏈燂紙姣忔鍘绘帀棣栬锛岄槻姝㈣繛鎺ョ偣閲嶅锛?
    if len(equity_all) > 0:
        eq_test = eq_test.iloc[1:]

    equity_all.append(eq_test)

# 鎷兼帴鎴愬畬鏁寸瓥鐣ユ洸绾?
equity_all = pd.concat(equity_all)

equity_all = equity_all[~equity_all.index.duplicated()]

# Buy & Hold
bh = 10000 * df.loc[equity_all.index, "Close"] / df.loc[equity_all.index, "Close"].iloc[0]


# ======================
# 鍙鍖?
# ======================
plt.figure(figsize=(12,6))
plt.plot(equity_all, label="Walk-Forward Strategy")
plt.plot(bh, "--", label="Buy & Hold")
plt.title("Walk-Forward Validation (Rolling)")
plt.xlabel("Date")
plt.ylabel("Equity ($)")
plt.legend()
plt.grid(True)
plt.show()
