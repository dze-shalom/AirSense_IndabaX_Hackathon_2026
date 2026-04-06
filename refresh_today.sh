#!/bin/bash
# ============================================================
# AirSense Cameroon — Daily Refresh Script
# Run this every morning to update predictions to TODAY's
# real meteorological data from Open-Meteo.
#
# Usage:  bash refresh_today.sh
# Cron:   0 6 * * * cd /path/to/AirSense_Cameroon && bash refresh_today.sh
# ============================================================

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   🌬️  AirSense Cameroon — Daily Refresh      ║"
echo "║   Pulling today's real weather data          ║"
echo "╚══════════════════════════════════════════════╝"
echo "   $(date '+%A, %d %B %Y  %H:%M')"
echo ""

# ── Step 1: Pull today's real data from Open-Meteo ────────────────────────────
echo -e "${YELLOW}[1/4] Fetching today's weather from Open-Meteo (42 cities)...${NC}"
python data/fetch_real_data.py
echo -e "${GREEN}    ✓ Real meteorological data fetched${NC}"

# ── Step 2: Update config to use real data ────────────────────────────────────
echo -e "${YELLOW}[2/4] Switching to real dataset...${NC}"
python3 -c "
import re
with open('config.py','r') as f: content = f.read()
content = re.sub(
    r'DATA_PATH\s*=\s*[\"\'](.*?)[\"\']',
    'DATA_PATH = \"data/cameroon_real_dataset.csv\"',
    content)
with open('config.py','w') as f: f.write(content)
print('    config.py updated → data/cameroon_real_dataset.csv')
"
echo -e "${GREEN}    ✓ Config updated${NC}"

# ── Step 3: Re-run feature engineering ────────────────────────────────────────
echo -e "${YELLOW}[3/4] Re-running feature pipeline...${NC}"
python data/features.py
echo -e "${GREEN}    ✓ Features updated${NC}"

# ── Step 4: Restart services ──────────────────────────────────────────────────
echo -e "${YELLOW}[4/4] Restarting dashboard and API...${NC}"
pkill -f "streamlit run" 2>/dev/null || true
pkill -f "uvicorn"       2>/dev/null || true
sleep 1
uvicorn api.main:app --reload --port 8000 &
sleep 2
streamlit run dashboard/app.py --server.port 8501 &
echo -e "${GREEN}    ✓ Services restarted with today's real data${NC}"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  ✅ Dashboard updated with today's data      ║"
echo "║  Dashboard → http://localhost:8501           ║"
echo "║  API docs  → http://localhost:8000/docs      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
