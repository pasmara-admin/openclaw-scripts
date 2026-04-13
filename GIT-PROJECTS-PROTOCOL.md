# GIT-PROJECTS-PROTOCOL.md - Protocollo Gestione Repository Aziendali

## Scopo
Questo documento definisce le linee guida per John (Main) e gli altri agenti OpenClaw riguardo alla clonazione, analisi e gestione delle repository Git aziendali (Produceshop, Pasmara, Dgmtek).

## Directory di Lavoro
- Tutte le repository devono essere clonate all'interno della cartella: `/root/.openclaw/projects/`.
- La struttura deve essere: `/root/.openclaw/projects/[nome-repo]`.

## Strategia di Clonazione e Branch
- **Branch di Default**: Utilizzare sempre `main` o `master`, a meno di indicazioni specifiche contrarie.
- **Aggiornamento Obbligatorio**: Prima di ogni interazione o analisi di una repository già clonata, assicurarsi che sia aggiornata eseguendo sempre un `git pull`.
- **Organizzazioni GitHub**: Se una repository non viene trovata in una specifica organizzazione, cercare nelle seguenti (in ordine):
    1. `produceshop`
    2. `pasmara`
    3. `dgmtek-org` (Organizzazione privata di Damiano con repository condivise).

## Modalità Operativa: Analisi "Read-Only"
- **Analisi del Progetto**: Prima di rispondere a domande su una repository, verificare sempre se esiste un file `AGENTS.md` o `README.md` nella root del progetto per comprenderne il contesto e le regole specifiche.
- **Strumenti di Analisi**: Utilizzare `grep`, `find`, `cat` o strumenti di ricerca semantica per esplorare il codice senza alterarlo.
- **Divieto di Modifica**: Non effettuare mai `commit`, `push` o modifiche ai file sorgente, a meno che non sia esplicitamente richiesto da Papà (Damiano) per scopi di debug o sviluppo assistito.

## Manutenzione
- Le repository clonate devono essere mantenute aggiornate tramite `git pull` obbligatorio prima di ogni analisi.
- In caso di necessità di spazio, le repository inutilizzate da tempo possono essere rimosse previa conferma.

---
_Protocollo creato il 2026-04-03 su richiesta di Papà (Damiano)._
