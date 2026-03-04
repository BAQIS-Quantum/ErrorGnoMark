#!/bin/bash

# ===== 配置 =====
LOG_DIR="ai_logs/raw"
TODAY=$(date +%F)
LOG_FILE="$LOG_DIR/$TODAY.log"

# ===== 确保目录存在 =====
mkdir -p "$LOG_DIR"

# ===== 记录开始 =====
echo -e "\n\n===============================" >> "$LOG_FILE"
echo "SESSION START: $(date)" >> "$LOG_FILE"
echo "===============================" >> "$LOG_FILE"

# ===== 使用 script 记录整个终端会话 =====
script -q -a "$LOG_FILE" claude "$@"

# ===== 记录结束 =====
echo -e "\n===============================" >> "$LOG_FILE"
echo "SESSION END: $(date)" >> "$LOG_FILE"
echo "===============================\n" >> "$LOG_FILE"