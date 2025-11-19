# 在服务器上运行 OOS 测试 - 快速指南

## 📋 前提条件

1. ✅ 服务器 IP: `49.51.244.154`
2. ✅ SSH 密钥: `mishi/lianxi.pem`
3. ✅ 服务器上已有数据和之前的回测结果

## 🚀 方法 1: 使用自动化脚本（推荐）

### Windows PowerShell

```powershell
# 1. 部署代码并运行 OOS 测试
.\scripts\deploy_and_run_oos.ps1

# 2. 下载结果
.\scripts\download_oos_results.ps1

# 3. 本地分析结果
python scripts/summarize_oos_results.py
```

### Linux/Mac Bash

```bash
# 1. 给脚本执行权限
chmod +x scripts/deploy_and_run_oos.sh
chmod +x scripts/download_oos_results.sh

# 2. 部署代码并运行 OOS 测试
./scripts/deploy_and_run_oos.sh

# 3. 下载结果
./scripts/download_oos_results.sh

# 4. 本地分析结果
python scripts/summarize_oos_results.py
```

## 🔧 方法 2: 手动步骤

### 1. 连接到服务器

```bash
ssh -i mishi/lianxi.pem ubuntu@49.51.244.154
```

### 2. 同步代码到服务器

在本地运行：

```bash
# Windows (PowerShell)
scp -i mishi/lianxi.pem -r config src scripts requirements.txt ubuntu@49.51.244.154:/home/ubuntu/manip-ofi-joint-analysis/

# Linux/Mac
rsync -avz -e "ssh -i mishi/lianxi.pem" \
    --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' \
    ./ ubuntu@49.51.244.154:/home/ubuntu/manip-ofi-joint-analysis/
```

### 3. 在服务器上运行测试

SSH 到服务器后：

```bash
cd /home/ubuntu/manip-ofi-joint-analysis

# 测试 OOS 设置
python3 scripts/test_oos_setup.py

# 运行单个品种 OOS 测试（快速测试）
python3 scripts/run_score_oos_per_symbol.py --symbol BTCUSD

# 运行所有品种 OOS 测试（后台运行）
nohup python3 scripts/run_score_oos_all.py > results/logs/oos_all_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# 查看进度
tail -f results/logs/oos_all_*.log
```

### 4. 下载结果

在本地运行：

```bash
# Windows (PowerShell)
scp -i mishi/lianxi.pem -r ubuntu@49.51.244.154:/home/ubuntu/manip-ofi-joint-analysis/results/oos/* ./results/oos/

# Linux/Mac
rsync -avz -e "ssh -i mishi/lianxi.pem" \
    ubuntu@49.51.244.154:/home/ubuntu/manip-ofi-joint-analysis/results/oos/ \
    ./results/oos/
```

### 5. 本地分析结果

```bash
python scripts/summarize_oos_results.py
```

## 📊 预期输出文件

运行完成后，`results/oos/` 目录将包含：

### 每个品种的结果
- `score_oos_train_{SYMBOL}_4H.csv` - 训练集结果
- `score_oos_test_{SYMBOL}_4H.csv` - 测试集结果
- `score_oos_core_combo_{SYMBOL}_4H.csv` - 核心组合 (0.6, -0.3) 跟踪

### 汇总结果
- `score_oos_summary_per_symbol.csv` - 各品种汇总
- `score_oos_summary_overall.csv` - 总体汇总
- `score_oos_plateau_analysis_per_symbol.csv` - 各品种高原分析
- `score_oos_plateau_analysis_overall.csv` - 总体高原分析

## ⏱️ 预计运行时间

- **单个品种**: 约 5-10 分钟
- **所有品种 (5个)**: 约 30-60 分钟

取决于：
- 参数网格大小（默认：1,224 configs per symbol）
- 服务器性能
- 数据量

## 🔍 监控进度

### 查看日志

```bash
# SSH 到服务器
ssh -i mishi/lianxi.pem ubuntu@49.51.244.154

# 查看最新日志
tail -f /home/ubuntu/manip-ofi-joint-analysis/results/logs/oos_all_*.log

# 或者查看特定品种的进度
grep "Progress:" /home/ubuntu/manip-ofi-joint-analysis/results/logs/oos_all_*.log
```

### 检查进程

```bash
# 查看 Python 进程
ps aux | grep python3

# 查看 OOS 脚本是否在运行
ps aux | grep run_score_oos
```

## ⚠️ 故障排除

### 问题 1: SSH 连接失败

```bash
# 检查密钥权限（Linux/Mac）
chmod 600 mishi/lianxi.pem

# 测试连接
ssh -i mishi/lianxi.pem ubuntu@49.51.244.154 "echo 'Connection successful'"
```

### 问题 2: 数据文件不存在

```bash
# SSH 到服务器检查数据
ssh -i mishi/lianxi.pem ubuntu@49.51.244.154
cd /home/ubuntu/manip-ofi-joint-analysis
python3 scripts/test_oos_setup.py
```

如果数据缺失，需要先运行：
```bash
python3 scripts/generate_manipscore_4h.py
python3 scripts/build_merged_data.py
```

### 问题 3: Python 依赖缺失

```bash
# SSH 到服务器安装依赖
ssh -i mishi/lianxi.pem ubuntu@49.51.244.154
cd /home/ubuntu/manip-ofi-joint-analysis
pip3 install -r requirements.txt
```

## 📝 下一步

运行完成后：

1. **查看结果**: 检查 `results/oos/` 中的 CSV 文件
2. **分析高原稳定性**: 查看 `score_oos_plateau_analysis_per_symbol.csv`
3. **验证核心组合**: 查看 `score_oos_core_combo_{SYMBOL}_4H.csv`
4. **评估策略**: 根据测试集 Sharpe 和稳健性指标决定是否部署

## 🎯 成功标准

- ✅ 测试集平均 Sharpe > 0.3
- ✅ 正 Sharpe 比例 > 70%
- ✅ Sharpe 衰减 < 0.5
- ✅ 高原区大小 > 15

---

**准备好了吗？运行 `.\scripts\deploy_and_run_oos.ps1` 开始测试！** 🚀

