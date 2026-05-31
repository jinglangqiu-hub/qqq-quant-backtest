import pandas as pd
import matplotlib.pyplot as plt

# 1) 璇诲彇 CSV
df = pd.read_csv("QQQ_10y_1d.csv")

# 2) 澶勭悊鏃ユ湡鍒楋細yfinance 瀵煎嚭鐨?CSV 绗竴鍒楅€氬父鏄?Date 鎴栬€?unnamed
#    鎴戜滑鎵炬渶鍍忔棩鏈熺殑閭ｅ垪骞惰涓?index
date_col = df.columns[0]
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col]).set_index(date_col)
df.index.name = "Date"

# 3) 鎷嶆墎澶氬眰琛ㄥご/濂囨€垪鍚?
#    浣犵殑 CSV 閲屽緢鍙兘鍑虹幇锛?'Close','QQQ') 杩欑琚啓鎴?"Close" + 鍙︿竴灞傜殑缁撴瀯
#    璇昏繘鏉ュ悗甯歌琛ㄧ幇鏄垪鍚嶉噷甯?'Close' 浣嗕笉绛変簬 'Close'
def find_close_column(columns):
    # 浼樺厛鎵惧畬鍏ㄧ瓑浜?Close 鐨?
    for c in columns:
        if str(c).strip() == "Close":
            return c
    # 鍐嶆壘鍖呭惈 Close 鐨勫垪锛堟瘮濡?'Close QQQ' / 'Close_...'/ 'Close.1'锛?
    for c in columns:
        if "Close" in str(c):
            return c
    return None

close_col = find_close_column(df.columns)
if close_col is None:
    raise ValueError(f"鎵句笉鍒?Close 鍒楋紝浣犲綋鍓嶇殑鍒楀悕鏄細{list(df.columns)[:20]} ...")

# 4) 寮哄埗鎶?Close 杞垚鏁板€硷紙鎶?'QQQ' 杩欑鑴忎笢瑗垮彉鎴?NaN锛?
df["Close_num"] = pd.to_numeric(df[close_col], errors="coerce")
df = df.dropna(subset=["Close_num"])

# 5) 璁＄畻 20 鏃ュ潎绾?+ 淇″彿
df["MA20"] = df["Close_num"].rolling(window=20).mean()
df["signal"] = (df["Close_num"] > df["MA20"]).astype(int)

# 6) 鎵句拱鍗栫偣锛堜俊鍙蜂粠 0->1 鏄拱锛?->0 鏄崠锛?
df["signal_shift"] = df["signal"].shift(1)
buy_signals = df[(df["signal"] == 1) & (df["signal_shift"] == 0)]
sell_signals = df[(df["signal"] == 0) & (df["signal_shift"] == 1)]

# 7) 鐢诲浘
plt.figure(figsize=(12, 6))
plt.plot(df.index, df["Close_num"], label="Close")
plt.plot(df.index, df["MA20"], label="MA20", linestyle="--")

plt.scatter(buy_signals.index, buy_signals["Close_num"],
            marker="^", label="BUY", s=80)
plt.scatter(sell_signals.index, sell_signals["Close_num"],
            marker="v", label="SELL", s=80)

plt.title("QQQ - MA20 Signal (No Trading Yet)")
plt.legend()
plt.grid(True)
plt.show()
