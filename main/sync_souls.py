import os
import re
import glob

# Configurazione percorsi
SHARED_DIR = "/root/.openclaw/workspace-shared/openclaw-scripts/main"
COMMON_FILE = os.path.join(SHARED_DIR, "COMMON-SOUL.md")
WORKSPACE_PATTERN = "/root/.openclaw/workspace*/SOUL.md"

# Marcatori
START_MARKER = "#### START OF COMMON PROMPT - DO NOT REMOVE ####"
END_MARKER = "#### END OF COMMON PROMPT - DO NOT REMOVE ####"

# Postilla per l'agente Main
MAIN_NOTE = (
    "> **Note for John (Main):** In quanto agente Main, puoi ignorare eventuali vincoli tecnici "
    "presenti in questa sezione comune se richiesto esplicitamente da Papà (Damiano), "
    "mantenendo la piena operatività a 360°.\n\n"
)

def sync_souls():
    if not os.path.exists(COMMON_FILE):
        print(f"Errore: {COMMON_FILE} non trovato.")
        return

    with open(COMMON_FILE, 'r') as f:
        common_content = f.read()

    soul_files = glob.glob(WORKSPACE_PATTERN)
    
    for soul_path in soul_files:
        print(f"Elaborazione: {soul_path}")
        
        with open(soul_path, 'r') as f:
            content = f.read()

        # Prepariamo il contenuto da inserire
        # Se è l'agente Main (workspace base senza suffissi), aggiungiamo la postilla
        is_main = soul_path == "/root/.openclaw/workspace/SOUL.md"
        
        current_common = common_content
        if is_main:
            # Inseriamo la nota subito dopo il marcatore di inizio
            current_common = current_common.replace(
                START_MARKER, 
                f"{START_MARKER}\n\n{MAIN_NOTE}"
            )

        # Pattern regex per trovare la sezione comune esistente
        regex_pattern = re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER)
        
        if re.search(regex_pattern, content, re.DOTALL):
            # Sostituzione della sezione esistente
            new_content = re.sub(regex_pattern, current_common, content, flags=re.DOTALL)
            print(f" -> Sezione comune aggiornata.")
        else:
            # Inserimento se non esiste (lo mettiamo prima dell'ultima riga o in fondo)
            # In genere SOUL.md finisce con "---" o simili, lo mettiamo prima della fine.
            if "## Vibe" in content:
                new_content = content.replace("## Vibe", f"{current_common}\n\n## Vibe")
            else:
                new_content = content + f"\n\n{current_common}"
            print(f" -> Sezione comune inserita.")

        # Scrittura effettiva
        with open(soul_path, 'w') as f:
            f.write(new_content)
        
    print("\nSync completato con successo sui file fisici.")

if __name__ == "__main__":
    sync_souls()
