#!/usr/bin/env bash
# RAMIBUS environment detection. Source this file from setup/start scripts.
set -u

ramibus_detect_environment() {
  RAMIBUS_ENV="linux"
  RAMIBUS_CAN_RUN_DOCKER=0
  RAMIBUS_IS_EPHEMERAL=0

  if [[ -n "${COLAB_RELEASE_TAG:-}" || -n "${COLAB_GPU:-}" || -d /content ]]; then
    RAMIBUS_ENV="colab"
    RAMIBUS_IS_EPHEMERAL=1
  elif [[ -n "${REPL_ID:-}" || -n "${REPLIT_DB_URL:-}" || -n "${REPL_OWNER:-}" ]]; then
    RAMIBUS_ENV="replit"
    RAMIBUS_IS_EPHEMERAL=1
  elif [[ -n "${CODESPACES:-}" ]]; then
    RAMIBUS_ENV="codespaces"
  elif [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
    RAMIBUS_ENV="wsl"
  elif [[ "$(uname -s 2>/dev/null || true)" == "Darwin" ]]; then
    RAMIBUS_ENV="macos"
  elif [[ "$(uname -s 2>/dev/null || true)" == "Linux" ]]; then
    RAMIBUS_ENV="linux"
  fi

  # Docker is deliberately opt-in by availability. Replit and Colab commonly
  # expose a docker binary without a usable daemon, so test the daemon too.
  if [[ "$RAMIBUS_ENV" != "replit" && "$RAMIBUS_ENV" != "colab" ]] && command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1 || sudo -n docker info >/dev/null 2>&1; then
      RAMIBUS_CAN_RUN_DOCKER=1
    fi
  fi

  RAMIBUS_PYTHON=""
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then RAMIBUS_PYTHON="$candidate"; break; fi
  done
  RAMIBUS_NODE="$(command -v node || true)"
  RAMIBUS_GPU="cpu"
  if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
    RAMIBUS_GPU="nvidia"
  elif [[ -n "${COLAB_GPU:-}" ]]; then
    RAMIBUS_GPU="colab-${COLAB_GPU}"
  fi
}

ramibus_print_environment() {
  echo "Environment: ${RAMIBUS_ENV:-unknown}"
  echo "Python: ${RAMIBUS_PYTHON:-missing}"
  echo "Node: ${RAMIBUS_NODE:-missing}"
  echo "GPU: ${RAMIBUS_GPU:-unknown}"
  echo "Docker/rami-kali: $([[ "${RAMIBUS_CAN_RUN_DOCKER:-0}" == 1 ]] && echo available || echo skipped/unavailable)"
}

ramibus_detect_environment
