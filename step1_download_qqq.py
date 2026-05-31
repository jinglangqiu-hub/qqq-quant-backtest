import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 1) 涓嬭浇 QQQ 鍘嗗彶鏃ョ嚎鏁版嵁
# period: 鎷夊涔呯殑鏁版嵁锛沬nterval: 鏁版嵁绮掑害锛?d = 鏃ョ嚎锛?
df = yf.download("QQQ", period="10y", interval="1d", auto_adjust=False)

# 2) 鍩烘湰妫€鏌ワ細鐪嬬湅鍓嶅嚑琛?
print("鏁版嵁琛屾暟锛?, len(df))
print(df.head())

# 3) 淇濆瓨鍒?CSV锛堜互鍚庡洖娴嬬洿鎺ヨ杩欎釜鏂囦欢锛屼笉鐢ㄩ噸澶嶄笅杞斤級
csv_path = "QQQ_10y_1d.csv"
df.to_csv(csv_path)
print("宸蹭繚瀛橈細", csv_path)

# 4) 鐢绘敹鐩樹环鏇茬嚎
plt.figure()
plt.plot(df.index, df["Close"])
plt.title("QQQ Close Price (10y, 1d)")
plt.xlabel("Date")
plt.ylabel("Close")
plt.show()
