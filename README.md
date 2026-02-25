# ⚛️ J.A.R.V.I.S. (Jarvis-AI-HA)

If you want a personal, single-user assistant that feels local, fast, always-on, and can actually control your home, this is it.

J.A.R.V.I.S. is a self-hosted AI assistant platform. You run an always-on process (the Gateway) on a machine you control (like an Ubuntu Server). The Gateway connects your Telegram to Google's Gemini 2.0 intelligence, and acts as the secure bridge to your Home Assistant network.

---

## ⚡ Why J.A.R.V.I.S.?

- **Local-first execution:** The gateway runs on your hardware. You own the runtime and the environment variables. Your data doesn't pass through third-party dashboard servers.
- **Conversation-first:** You interact via Telegram. No web logins, no new apps to install. Just text your assistant.
- **Always-on:** Designed to run continuously in the background (via `tmux`) as a silent daemon waiting for your commands.
- **Home Assistant native:** Not just a chatbot. It's designed to issue execution commands to your physical smart home devices.

## 🏗️ Architecture

J.A.R.V.I.S. is easiest to understand as 4 core layers:

1. **Gateway (Control Plane)** — One long-running Python process (`main.py`) that handles message ingress/egress.
2. **Channel** — The adapter for **Telegram**, normalizing chat messages into the system.
3. **Agent Runtime** — Takes your context, connects to **Google Gemini 2.0 Flash** via the new `google-genai` SDK, and streams elegant, butler-style responses.
4. **Tools** — Capabilities beyond text. (Integrating Home Assistant REST API control).

---

## 🚀 Quick Start (TL;DR)

### Prerequisites
- **Python ≥ 3.10**
- A Telegram Bot Token (from `@BotFather`)
- A Google Gemini API Key (from Google AI Studio)
- An active Home Assistant instance (URL & Long-Lived Access Token)

### 1. Install & Setup Gateway

Clone the repository to your remote server (e.g., Ubuntu 24.04 Server):

```bash
git clone [https://github.com/s9112004/Jarvis-AI-HA.git](https://github.com/s9112004/Jarvis-AI-HA.git)
cd Jarvis-AI-HA

# Install dependencies directly to the system (for dedicated VMs)
sudo apt update && sudo apt install python3-pip -y
pip install pyTelegramBotAPI python-dotenv google-genai --break-system-packages
```

### 2. Configure Security & Keys
Create your local environment file. **Never commit this file to Git.**

```bash
nano .env
```

Add your credentials:

```env
TG_TOKEN="your_telegram_token"
GEMINI_API_KEY="your_gemini_key"
HA_URL="http://your_ha_ip:8123"
HA_TOKEN="your_ha_token"
```

### 3. Start the Daemon
We run the Gateway inside `tmux` so it stays alive after you disconnect SSH.

```bash
tmux new -s jarvis
python3 main.py
```
*(Press `Ctrl+B`, then `D` to safely detach from the background session).*

---

## 🔒 Security & Troubleshooting

- **Lock down the Gateway:** Your Ubuntu Server has direct access to your Home Assistant. Do not expose this server directly to the open internet.
- **Keep `.env` isolated:** The `.gitignore` is pre-configured to block `.env`. Never bypass this.
- **Proxy Interference [Errno 101]:** The `main.py` is hardcoded to flush system proxies (`http_proxy`, `https_proxy`) on boot. This prevents `urllib3` "Network is unreachable" fatal errors caused by ghost environment variables on headless Linux machines.