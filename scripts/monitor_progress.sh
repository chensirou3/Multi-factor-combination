#!/bin/bash
# Monitor the progress of fine grid search

echo "============================================================"
echo "Fine Grid Search Progress Monitor"
echo "============================================================"
echo ""

# Check if process is running
if ps aux | grep -q "[r]un_all_symbols_fine_grid.py"; then
    echo "✓ Process is RUNNING"
else
    echo "✗ Process is NOT running"
fi

echo ""
echo "============================================================"
echo "Latest Log Output (last 30 lines)"
echo "============================================================"
tail -30 /home/ubuntu/manip-ofi-joint-analysis/fine_grid_run.log

echo ""
echo "============================================================"
echo "Completed Result Files"
echo "============================================================"
ls -lh /home/ubuntu/manip-ofi-joint-analysis/results/backtests/*_fine.csv 2>/dev/null | tail -10

echo ""
echo "============================================================"
echo "File Count"
echo "============================================================"
filter_count=$(ls /home/ubuntu/manip-ofi-joint-analysis/results/backtests/filter_grid_*_fine.csv 2>/dev/null | wc -l)
score_count=$(ls /home/ubuntu/manip-ofi-joint-analysis/results/backtests/score_grid_*_fine.csv 2>/dev/null | wc -l)
echo "Filter mode results: $filter_count / 5"
echo "Score mode results: $score_count / 5"

echo ""
echo "============================================================"
echo "Estimated Progress"
echo "============================================================"
total_expected=10  # 5 symbols × 2 modes
total_completed=$((filter_count + score_count))
progress=$((total_completed * 100 / total_expected))
echo "Completed: $total_completed / $total_expected ($progress%)"

