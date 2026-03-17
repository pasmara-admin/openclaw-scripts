# INFRASTRUCTURE.md - System Overview

## Server Principale
- **Hardware:** vmi3129567
- **Sistema Operativo:** Linux 6.12.38+deb13-cloud-amd64 (Debian 13)
- **Porta Gateway:** 18789

## Agenti OpenClaw
- **Main Agent (id: main):** 
  - Workspace: `/root/.openclaw/workspace/`
  - Model: `gemini-3-flash`
- **Finance Agent (id: finance):** 
  - Workspace: `/root/.openclaw/workspace-finance/`
  - Model: `gemini-3-pro`
- **Shared Knowledge:** 
  - Directory: `/root/.openclaw/workspace-shared/`

## Image Generation Workflow (Nano Banana Pro)

Per generare o modificare immagini tramite la skill `nano-banana-pro` (Gemini 3 Pro Image):

1. **API Key:** Utilizzare la `GEMINI_API_KEY` configurata nella skill `nano-banana-pro`.
2. **Ambiente:** Assicurarsi che `uv` sia disponibile (installato in `/root/.local/bin/uv`).
3. **Comando:** Eseguire lo script tramite `uv run`.
    - **Percorso Script:** `/usr/lib/node_modules/openclaw/skills/nano-banana-pro/scripts/generate_image.py`
    - **Argomenti:** `--prompt "..."`, `--filename "..."`, `--resolution 1K` (o 2K/4K).
    - **Modifiche:** Usare `-i "/percorso/input.png"` per fornire un'immagine di riferimento.
4. **Consegna Telegram:** Dopo la generazione, usare il tool `message` con `action: "send"` includendo il `filePath`.
5. **Archiviazione:** Salvare gli avatar o asset grafici in `/root/.openclaw/workspace/avatars/`.
