# RAMIBUS adaptive setup

`install.sh` detects the host environment before installing or starting optional services.

- **Replit shell:** installs the application and skips `rami-kali`; Replit does not provide a dependable Docker daemon. The runtime reports Docker as unavailable instead of pretending it works.
- **Google Colab:** performs the full Python/frontend/application setup, detects T4/CUDA/NVIDIA when exposed, supports Hugging Face secrets and optional ngrok, and skips only Docker-dependent `rami-kali` when Docker is unavailable.
- **Linux/macOS/WSL/VPS:** uses native Python/Node and starts `rami-kali` only when Docker and Compose are actually responding.
- **Windows:** use the existing PowerShell/batch installer; WSL2 is the preferred path for the Linux-compatible runtime.

```bash
cd ramibot
bash install.sh
bash start.sh
```

Credentials and optional integrations are configured through the RAMIBUS Settings UI. The installer creates `backend/settings.json` without overwriting an existing file. `HF_TOKEN` and `NGROK_AUTHTOKEN` may also be supplied through the host environment, especially in Colab. Public tunnels are opt-in and must never be started silently.
