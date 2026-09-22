#!/usr/bin/env bash
# RAMIBUS adaptive installer for Linux, macOS, WSL, Replit, Colab, and VPS.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"
source scripts/environment.sh

cyan='\033[0;36m'; yellow='\033[1;33m'; green='\033[0;32m'; red='\033[0;31m'; reset='\033[0m'
info(){ echo -e "${cyan}[ramibus]${reset} $*"; }
warn(){ echo -e "${yellow}[ramibus]${reset} $*"; }
ok(){ echo -e "${green}[ramibus]${reset} $*"; }
die(){ echo -e "${red}[ramibus]${reset} $*" >&2; exit 1; }

ramibus_print_environment
[[ -n "$RAMIBUS_PYTHON" ]] || die "Python 3 is required. Install Python 3.9+ and rerun."
[[ -n "$RAMIBUS_NODE" ]] || die "Node.js is required for the frontend. Install Node 18+ and rerun."

PY_MAJOR="$($RAMIBUS_PYTHON -c 'import sys; print(sys.version_info.major)')"
PY_MINOR="$($RAMIBUS_PYTHON -c 'import sys; print(sys.version_info.minor)')"
(( PY_MAJOR > 3 || (PY_MAJOR == 3 && PY_MINOR >= 9) )) || die "Python 3.9+ required."
NODE_MAJOR="$(node --version | sed 's/^v//' | cut -d. -f1)"
(( NODE_MAJOR >= 18 )) || die "Node.js 18+ required."

# Colab/Replit are ephemeral and usually cannot run Docker. They still receive
# the complete RAMIBUS app, providers, OSINT adapters, HF setup, and UI; only
# the Docker-dependent rami-kali service is skipped.
if [[ ! -x backend/.venv/bin/python ]]; then
  info "Creating backend virtual environment..."
  "$RAMIBUS_PYTHON" -m venv backend/.venv
fi
backend/.venv/bin/python -m pip install --upgrade pip >/dev/null
backend/.venv/bin/python -m pip install -r backend/requirements.txt

info "Installing frontend dependencies..."
(cd frontend && npm install --silent)

if [[ ! -f backend/settings.json ]]; then
  cp backend/settings.example.json backend/settings.json
  warn "Created backend/settings.json. Add credentials in the RAMIBUS Settings UI."
fi

if [[ "$RAMIBUS_CAN_RUN_DOCKER" == 1 ]]; then
  if command -v docker compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1; then
    info "Docker is available; building rami-kali..."
    docker build -t rami-kali rami-kali/
    docker compose -f rami-kali/docker-compose.yml up -d
    ok "rami-kali is running."
  else
    warn "Docker daemon is available but Docker Compose is missing; skipping rami-kali."
  fi
else
  warn "Skipping rami-kali: this environment has no usable Docker daemon."
  warn "RAMIBUS remains usable for chat, OSINT, providers, and non-Docker capabilities."
fi

cat <<EOF

RAMIBUS setup complete for: $RAMIBUS_ENV
Frontend: http://localhost:5173
Backend:  http://localhost:8000/docs

Next steps:
  1. Start with: bash start.sh
  2. Open Settings and add only the provider/data-source keys you own.
  3. For Colab/Replit, configure HF_TOKEN and optionally NGROK_AUTHTOKEN in the environment.
  4. Public URLs are never opened automatically; use the explicit tunnel setup flow.
EOF
