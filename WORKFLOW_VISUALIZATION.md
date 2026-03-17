# Workflow: Generazione e Invio Grafici (Visualization)

Questo documento descrive lo standard per generare grafici dai dati aziendali e inviarli come immagini su Telegram/canali di messaggistica.

## 1. Prerequisiti
- **Librerie Python:** Assicurarsi che siano installate `matplotlib`, `seaborn`, `pandas`.
  - Se mancano: `pip install --break-system-packages matplotlib seaborn pandas`
- **Dati:** Estrarre i dati necessari (es. da MySQL) e strutturarli per lo script Python.

## 2. Procedura Passo-Passo

### A. Estrazione Dati
Eseguire le query SQL necessarie e annotare i risultati. Non passare i risultati grezzi direttamente allo script se sono troppi; sintetizzarli in array o CSV locali.

### B. Creazione Script Python
Scrivere un file temporaneo (es. `chart_gen.py`) che:
1. Importa `matplotlib.pyplot`, `pandas`, `seaborn`.
2. Contiene i dati (hardcoded se pochi, o letti da CSV).
3. Configura il grafico (titolo, label assi, legenda).
4. Salva l'immagine con `plt.savefig('nome_file.png')`.

**Esempio di codice:**
```python
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Dati
data = {'Giorno': ['Lun', 'Mar', 'Mer'], 'Ordini': [10, 15, 8]}
df = pd.DataFrame(data)

# Plot
plt.figure(figsize=(10, 6))
sns.barplot(data=df, x='Giorno', y='Ordini')
plt.title('Esempio Grafico')
plt.tight_layout()

# Salvataggio
plt.savefig('/root/.openclaw/workspace-finance/output_chart.png')
```

### C. Esecuzione
Eseguire lo script:
`python3 chart_gen.py`

Verificare che il file `.png` sia stato creato.

### D. Invio via Messaggistica
Usare il tool `message` per inviare l'immagine come allegato nativo (NON come link testuale).

**Parametri Tool:**
- `action`: "send"
- `channel`: "telegram" (o il canale in uso)
- `media`: "/path/assoluto/a/immagine.png" (es. `/root/.openclaw/workspace-finance/output_chart.png`)
- `message`: "Ecco il grafico richiesto..."

**Nota Importante:** Il parametro `media` nel tool `message` gestisce automaticamente l'upload su Telegram. Non usare comandi `curl` manuali.

## 3. Pulizia
Dopo l'invio, è buona norma rimuovere i file temporanei (`.py` e `.png`) se non servono più per lo storico.
