# QQQ 量化入门练习（逐步脚本版）

这个仓库是一个围绕 `QQQ` 的量化入门练习集合，核心思路是：

1. 下载并清洗日线数据。
2. 从最简单的均线信号开始。
3. 逐步加入回测、参数扫描、交易成本、仓位控制、训练/测试拆分、Walk-Forward 验证。

整体更偏“教学演进”，不是一个完整的生产级回测框架。

## 环境依赖

建议 Python 3.9+，主要依赖：

- `pandas`
- `numpy`
- `matplotlib`
- `yfinance`

可用如下命令安装：

```bash
pip install pandas numpy matplotlib yfinance
```

## 文件说明（逐个）

### 数据文件

- `QQQ_10y_1d.csv`
  - `step1_download_qqq.py` 下载后保存的原始数据。
  - 文件前 3 行是 `yfinance` 导出的多层表头痕迹（`Price/Ticker/Date`），所以后续脚本都做了“第一列转日期 + 自动识别 Close 列 + 数值清洗”。

### 脚本文件

- `step1_download_qqq.py`
  - 用 `yfinance` 下载 QQQ 近 10 年日线（`interval=1d`）。
  - 打印数据预览。
  - 保存为 `QQQ_10y_1d.csv`。
  - 画收盘价曲线。

- `step2_signal_qqq.py`
  - 读取并清洗 CSV。
  - 计算 `MA20` 与二值信号：`Close > MA20 -> 1`，否则 `0`。
  - 标注买卖点（`0->1` 买入，`1->0` 卖出）并画图。
  - 注意：这一步只做信号可视化，不做资金回测。

- `step3_backtest_qqq.py`
  - 在 `step2` 信号基础上做最简单全仓/空仓回测（all-in/all-out）。
  - 输出策略收益、最大回撤。
  - 加入 Buy & Hold 对照并绘制资金曲线对比。

- `step5_scan_ma.py`
  - 对 MA 窗口 `5~200` 做参数扫描。
  - 每个窗口回测并记录：`TotalReturn`、`MaxDrawdown`、`Trades`。
  - 打印收益 Top10，并画三张参数敏感性图。

- `step6_scan_ma_costs.py`
  - 在 `step5` 基础上加入交易成本：
    - 手续费 `fee_rate=0.1%`
    - 滑点 `slippage_rate=0.05%`
  - 重新做 MA 扫描，观察成本对收益/交易频率策略的影响。

- `step7_compare_A_B.py`
  - 对比两种“连续仓位”策略（均含成本）：
  - 策略 A：基于 `Close/MA` 偏离度映射仓位（0~1）。
  - 策略 B：双均线方向/强度映射仓位（0~1）。
  - 与 Buy & Hold 做收益和回撤对比，并画资金曲线。

- `step8_vol_target.py`
  - 在趋势仓位基础上叠加“波动率目标控制”：
  - 先算 20 日年化波动，再按 `TARGET_VOL=15%` 缩放仓位。
  - 最终仓位 = 趋势仓位 × 波动率缩放因子。
  - 回测并和 Buy & Hold 对比。

- `step9_train_test_split.py`
  - 做简单的样本内/样本外验证：
    - 训练集到 `2020-12-31`
    - 测试集为其后区间
  - 在训练集网格搜索参数（MA、K），用 `score = ret + 2*mdd` 打分。
  - 固定最优参数在测试集评估（Out-of-Sample），并与 Buy & Hold 对比。

- `step10_walk_forward.py`
  - 做滚动 Walk-Forward 验证：
    - 训练窗口 4 年，测试窗口 1 年。
    - 每一段先在训练期选参数，再在下一年测试。
  - 段与段之间采用“资金接力”（上一段期末作为下一段初始资金）。
  - 最后拼接成完整策略净值，并和 Buy & Hold 对比。

### 其他

- `.idea/`
  - PyCharm 工程配置目录，与策略逻辑无关。

## 运行顺序建议

按下面顺序最容易理解：

1. `step1_download_qqq.py`
2. `step2_signal_qqq.py`
3. `step3_backtest_qqq.py`
4. `step5_scan_ma.py`
5. `step6_scan_ma_costs.py`
6. `step7_compare_A_B.py`
7. `step8_vol_target.py`
8. `step9_train_test_split.py`
9. `step10_walk_forward.py`

> 目录中没有 `step4`，目前是直接从 `step3` 到 `step5`。

## 这个项目当前的特点与局限

- 特点
  - 非常适合初学者按步骤理解：信号 -> 回测 -> 成本 -> 参数 -> 防过拟合。
  - 代码直观，便于改参数做实验。

- 局限
  - 回测成交机制较简化（按收盘价近似成交）。
  - 没有完整绩效指标体系（如年化、Sharpe、Calmar 等）。
  - 没有统一模块化框架，脚本间有重复代码。

## 后续可改进方向

- 抽公共函数：数据清洗、回测引擎、绩效统计。
- 增加更完整指标：年化收益/波动、Sharpe、Sortino、Calmar、胜率等。
- 增加稳健性检验：不同标的、不同周期、参数稳定区间热力图。
- 将脚本改成 notebook 或 package，便于复现和维护。
