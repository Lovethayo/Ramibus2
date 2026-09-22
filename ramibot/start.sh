#!/usr/bin/env bash
# RAMIBUS adaptive startup. Docker/rami-kali is optional by design.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source scripts/environment.sh

cyan='\033[0;36m'; yellow='\033[1;33m'; green='\033[0;32m'; reset='\033[0m'
info(){ echo -e "${cyan}[ramibus]${reset} $*"; }
warn(){ echo -e "${yellow}[ramibus]${reset} $*"; }

[[ -x backend/.venv/bin/python ]] || { warn "Run bash install.sh first."; exit 1; }
[[ -d frontend/node_modules ]] || { warn "Run bash install.sh first."; exit 1; }

ramibus_print_environment
if [[ "$RAMIBUS_CAN_RUN_DOCKER" == 1 ]]; then
  if docker ps --filter 'name=^rami-kali$' --filter status=running --format '{{.Names}}' | grep -q '^rami-kali$'; then
    info "rami-kali is already running."
  elif [[ -f rami-kali/docker-compose.yml ]] && docker compose version >/dev/null 2>&1; then
    info "Starting rami-kali..."
    docker compose -f rami-kali/docker-compose.yml up -d
  fi
else
  warn "Skipping rami-kali in $RAMIBUS_ENV; Docker-backed tools will report unavailable."
fi

cleanup(){
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

(cd backend && ../backend/.venv/bin/python -m uvicorn main:app --reload --port 8000) & BACKEND_PID=$!
(cd frontend && npm run dev -- --host 0.0.0.0) & FRONTEND_PID=$!
echo -e "${green}RAMIBUS is starting: http://localhost:5173${reset}"
wait -n "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
