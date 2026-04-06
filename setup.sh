#!/bin/bash
# ============================================================
# AirSense Cameroon — One-Shot Setup Script
# Run this ONCE after unzipping.
# It installs everything, builds the models, and launches
# the dashboard + API in separate terminal tabs.
# ============================================================

set -e   # exit on any error
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   🌬️  AirSense Cameroon — Setup              ║"
echo "║   IndabaX 2026 Hackathon                     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Step 1: Install dependencies ──────────────────────────
echo -e "${YELLOW}[1/5] Installing Python packages...${NC}"
pip install -r requirements.txt -q
echo -e "${GREEN}    ✓ Packages installed${NC}"

# ── Step 2: Feature engineering ───────────────────────────
echo -e "${YELLOW}[2/5] Running feature engineering pipeline...${NC}"
python data/features.py
echo -e "${GREEN}    ✓ Features built → data/cameroon_features.csv${NC}"

# ── Step 3: Train XGBoost model ───────────────────────────
echo -e "${YELLOW}[3/5] Training XGBoost model...${NC}"
python models/train.py
echo -e "${GREEN}    ✓ Model saved → models/xgb_model.joblib${NC}"

# ── Step 4: Train RL threshold agent ──────────────────────
echo -e "${YELLOW}[4/5] Training REINFORCE RL threshold agent...${NC}"
python models/rl_threshold.py
echo -e "${GREEN}    ✓ RL thresholds saved → models/rl_thresholds.json${NC}"

# ── Step 5: Launch API + Dashboard ────────────────────────
echo -e "${YELLOW}[5/5] Launching services...${NC}"
echo ""
echo -e "${GREEN}  Starting FastAPI backend  → http://localhost:8000${NC}"
echo -e "${GREEN}  API docs                  → http://localhost:8000/docs${NC}"
echo -e "${GREEN}  Starting Streamlit dashboard → http://localhost:8501${NC}"
echo ""
echo "  Press Ctrl+C to stop both services."
echo ""

# Launch API in background
uvicorn api.main:app --reload --port 8000 &
API_PID=$!

# Small delay then launch dashboard
sleep 2
streamlit run dashboard/app.py --server.port 8501

# Cleanup on exit
trap "kill $API_PID 2>/dev/null; echo 'Services stopped.'" EXIT
