# 项目进度报告

## 项目概述

**项目名称**: ManipScore-OFI 联合因子分析框架
**创建日期**: 2025-11-19
**当前版本**: v1.1 - OOS 样本外验证与稳健性分析

本项目整合了两个独立的市场微观结构因子：
- **ManipScore**: 市场操纵检测因子（反转逻辑）
- **OFI (Order Flow Imbalance)**: 订单流失衡因子（动量/过滤逻辑）

---

## 已完成工作

### 1. 项目架构搭建 ✅

**配置文件** (4个):
- `config/paths.yaml` - 数据路径配置
- `config/symbols.yaml` - 交易品种配置
- `config/joint_params.yaml` - 粗网格参数配置
- `config/joint_params_fine.yaml` - 精细网格参数配置

**核心模块** (15+):
- `src/utils/` - 工具模块（配置加载、日志、文件IO）
- `src/joint_data/` - 数据加载和合并
- `src/joint_factors/` - 因子计算和信号生成
- `src/analysis/` - 性能分析
- `src/backtest/` - 回测引擎

**可执行脚本** (11个):
- `scripts/generate_manipscore_4h.py` - 从 OHLCV 生成 ManipScore
- `scripts/build_merged_data.py` - 合并 ManipScore 和 OFI 数据
- `scripts/run_joint_filter_grid.py` - Filter 模式网格搜索
- `scripts/run_joint_score_grid.py` - Score 模式网格搜索
- `scripts/run_all_symbols_fine_grid.py` - 批量运行所有品种
- `scripts/analyze_fine_grid_results.py` - 结果分析
- `scripts/count_configs.py` - 参数配置统计
- `scripts/run_score_oos_per_symbol.py` - Score 模式单品种 OOS 回测 ✨NEW
- `scripts/run_score_oos_all.py` - Score 模式批量 OOS 回测 ✨NEW
- `scripts/summarize_oos_results.py` - OOS 结果汇总与高原分析 ✨NEW
- `scripts/run_filter_oos_per_symbol.py` - Filter 模式 OOS 骨架 ✨NEW

### 2. 数据准备 ✅

**ManipScore 数据生成**:
- 从 OFI 项目的 OHLCV 数据计算 ManipScore
- 3 个组件：蜡烛图异常 (40%) + 洗盘交易 (40%) + 价格反转 (20%)
- 成功生成 5 个品种的 4H 数据

**数据合并**:
- 成功合并 ManipScore 和 OFI 因子数据
- 数据质量验证通过（缺失率 < 7%）
- 保存为 Parquet 格式

**品种覆盖**:
| 品种 | 数据量 | 时间范围 | 状态 |
|------|--------|---------|------|
| BTCUSD | 6,027 bars | 2017-2020 | ✅ |
| ETHUSD | 15,470 bars | 2017-2025 | ✅ |
| XAUUSD | 25,231 bars | 2010-2025 | ✅ |
| XAGUSD | 24,796 bars | 2010-2025 | ✅ |
| EURUSD | 24,779 bars | 2010-2025 | ✅ |

### 3. 回测完成 ✅

#### 粗网格回测（初步测试）
- **品种**: XAUUSD
- **Filter 模式**: 64 个配置
- **Score 模式**: 84 个配置
- **关键发现**: Score 模式发现正收益策略（+1.97%）

#### 精细网格回测（全面分析）
- **品种**: 5 个（BTCUSD, ETHUSD, XAUUSD, XAGUSD, EURUSD）
- **总配置数**: 9,320 个
  - Filter 模式: 640 个/品种 × 5 = 3,200 个
  - Score 模式: 1,224 个/品种 × 5 = 6,120 个
- **总耗时**: 47.1 分钟
- **完成时间**: 2025-11-19 14:25:26

---

## 核心发现

### 1. 策略模式对比

| 模式 | 平均 Sharpe | 平均收益 | 正收益品种 | 特点 |
|------|------------|---------|-----------|------|
| **Score 模式** | **0.484** | **3.20%** | **5/5** | 高 Sharpe，低波动 |
| Filter 模式 | 0.202 | 6.36% | 5/5 | 高收益，高波动 |

**结论**: Score 模式风险调整后收益更优（Sharpe 高 2.4 倍）

### 2. 最佳品种排名

**Score 模式 Sharpe 排名**:
1. 🥇 **ETHUSD**: 0.730 (收益 9.67%, 胜率 75%)
2. 🥈 **XAGUSD**: 0.566 (收益 3.23%, 胜率 66.7%)
3. 🥉 **EURUSD**: 0.504 (收益 1.41%, 胜率 75%)
4. BTCUSD: 0.464 (收益 0.63%, 胜率 33.3%)
5. XAUUSD: 0.154 (收益 1.04%, 胜率 66.7%)

### 3. 最佳策略配置

#### 🏆 推荐策略：ETHUSD Score 模式

```yaml
品种: ETHUSD
模式: Score (加权组合)
参数:
  weight_manip: 0.6      # ManipScore 权重
  weight_ofi: -0.3       # OFI 权重（反向对冲）
  composite_z_entry: 3.0 # 入场阈值
  holding_bars: 5        # 持仓 5 个 4H bar (20小时)

回测表现:
  Sharpe Ratio: 0.730
  Total Return: 9.67%
  Win Rate: 75.0%
  Total Trades: 4
  Max Drawdown: -0.65%
```

### 4. 关键模式发现

#### 对冲策略 (w_manip=0.6, w_ofi=-0.3)
- 在 **4/5 品种**中表现最佳
- **逆向对冲逻辑**: ManipScore 反转信号 + OFI 反向对冲
- 当检测到操纵时，OFI 反向持仓增强信号强度

#### 高阈值低频交易
- Z-score 阈值: 2.5-3.5（极端信号）
- 交易频率: 3-34 笔（低频高质量）
- 胜率: 50-75%（高胜率）
- 最大回撤: < 2%（低风险）

#### 品种特异性
- **加密货币**: 短持仓（1-5 bars），对冲策略
- **贵金属**: 中等持仓（2-10 bars），混合策略
- **外汇**: 长持仓（8 bars），对冲策略

---

## 输出文件

### 回测结果文件
```
results/backtests/
├── filter_grid_BTCUSD_4H_fine.csv    (640 rows)
├── filter_grid_ETHUSD_4H_fine.csv    (640 rows)
├── filter_grid_XAUUSD_4H_fine.csv    (640 rows)
├── filter_grid_XAGUSD_4H_fine.csv    (640 rows)
├── filter_grid_EURUSD_4H_fine.csv    (640 rows)
├── score_grid_BTCUSD_4H_fine.csv     (1,224 rows)
├── score_grid_ETHUSD_4H_fine.csv     (1,224 rows)
├── score_grid_XAUUSD_4H_fine.csv     (1,224 rows)
├── score_grid_XAGUSD_4H_fine.csv     (1,224 rows)
├── score_grid_EURUSD_4H_fine.csv     (1,224 rows)
├── filter_best_per_symbol.csv        (最佳 Filter 策略汇总)
└── score_best_per_symbol.csv         (最佳 Score 策略汇总)
```

### 数据文件
```
data/intermediate/merged_4h/
├── BTCUSD_4H_merged.parquet
├── ETHUSD_4H_merged.parquet
├── XAUUSD_4H_merged.parquet
├── XAGUSD_4H_merged.parquet
└── EURUSD_4H_merged.parquet
```

---

## 下一步计划

### 短期任务
- [ ] 样本外测试（训练集 vs 测试集）
- [ ] 添加可视化分析（权益曲线、参数热力图）
- [ ] 实盘模拟测试

### 中期任务
- [ ] 策略优化（动态止损/止盈）
- [ ] 仓位管理（Kelly Criterion）
- [ ] 市场状态过滤

### 长期任务
- [ ] 多周期分析（1H, 8H, 1D）
- [ ] 更多品种扩展
- [ ] 实盘部署

---

## 技术栈

- **语言**: Python 3.10+
- **数据处理**: pandas, numpy
- **配置管理**: PyYAML
- **数据存储**: Parquet (pyarrow)
- **日志**: logging
- **部署**: Ubuntu Server (SSH)

---

## 🆕 v1.1 新增功能 (2025-01-19)

### 6. 样本外 (OOS) 验证框架 ✅

**时间分割配置**:
- 新增配置文件: `config/oos_splits.yaml`
- 加密货币: 训练集 2017-2020 (4年), 测试集 2021-2025 (5年)
- 传统资产: 训练集 2010-2018 (9年), 测试集 2019-2025 (7年)

**回测引擎增强**:
- 扩展 `src/backtest/engine_4h.py` 支持时间过滤
- 新增 `subset_df_by_date()` 函数
- 新增 `start_date` 和 `end_date` 参数

**OOS 脚本 (Score 模式)**:
- `run_score_oos_per_symbol.py` - 单品种 OOS 回测
  - 训练集: 运行全部参数网格
  - 参数选择: Top K 或高原区 (Sharpe ≥ 70% × max)
  - 测试集: 验证选定参数
  - 核心组合跟踪: 特别跟踪 (0.6, -0.3) 权重组合
- `run_score_oos_all.py` - 批量运行所有品种
- `summarize_oos_results.py` - 汇总分析与高原稳健性

**Filter 模式预留**:
- `run_filter_oos_per_symbol.py` - 骨架实现（待完成）

### 7. 参数稳健性分析 ✅

**高原分析模块**:
- 新增 `src/analysis/oos_plateau_analysis.py`
- 核心函数:
  - `analyze_plateau_stability()` - 高原稳定性分析
  - `compare_single_best_vs_plateau()` - 单点最优 vs 高原对比

**稳健性指标**:
- 测试集 Sharpe 分布 (均值、中位数、标准差、分位数)
- 正 Sharpe 比例 (> 0, > 0.3, > 0.5)
- Sharpe 衰减率 (训练集均值 - 测试集均值)
- 高原区大小和稳定性

**核心组合跟踪**:
- 特别跟踪发现的最优权重组合 (w_manip=0.6, w_ofi=-0.3)
- 单独输出文件: `score_oos_core_combo_{SYMBOL}_4H.csv`
- 覆盖所有 z 阈值和持仓周期组合

### 8. 文档更新 ✅

**README.md**:
- 新增 OOS 使用指南
- 新增高原分析说明
- 更新项目结构
- 更新结果文件列表

**CHANGELOG.md**:
- 新增 v1.1.0 版本记录
- 详细列出 OOS 功能和技术细节

**PROGRESS.md**:
- 更新版本号至 v1.1
- 新增 OOS 模块说明
- 更新项目统计

---

## 项目统计

### v1.0 (精细网格回测)
- **代码文件**: 20+ Python 模块
- **配置文件**: 4 个 YAML
- **脚本文件**: 7 个可执行脚本
- **回测配置**: 9,320 个
- **数据点**: 96,303 个 4H bars
- **总耗时**: 47.1 分钟

### v1.1 (OOS & 稳健性分析)
- **新增代码文件**: 2 个 (oos_plateau_analysis.py, 扩展 engine_4h.py)
- **新增配置文件**: 1 个 (oos_splits.yaml)
- **新增脚本文件**: 4 个 (3 个 Score OOS + 1 个 Filter 骨架)
- **总代码文件**: 22+ Python 模块
- **总配置文件**: 5 个 YAML
- **总脚本文件**: 11 个可执行脚本

---

## 下一步计划

### Phase 3: 可视化与分析 (v1.2)
- [ ] 权益曲线图 (训练集 vs 测试集)
- [ ] 参数热力图 (Sharpe vs 参数组合)
- [ ] 月度/年度收益分布
- [ ] 回撤分析图
- [ ] 高原区可视化

### Phase 4: 策略优化 (v1.3)
- [ ] 动态止损/止盈
- [ ] 仓位管理 (Kelly Criterion)
- [ ] 市场状态过滤 (波动率、趋势)
- [ ] 多周期分析 (1H, 8H, 1D)

### Phase 5: 实盘准备 (v2.0)
- [ ] 纸面交易模拟
- [ ] 滑点和交易成本建模
- [ ] 实时数据接口
- [ ] 风险管理系统

---

**最后更新**: 2025-01-19
**状态**: ✅ OOS 样本外验证框架完成，准备运行测试

