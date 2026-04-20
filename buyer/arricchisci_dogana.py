import pandas as pd
import mysql.connector
import sys
import os

def process_file(input_path):
    # Caricamento file (supporta .xlsx e .csv)
    if input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
    else:
        df = pd.read_excel(input_path)

    # Identificazione EAN (Colonna C / Indice 2)
    # Ry ha rettificato: Col A (SKU), Col B (Nome), Col C (EAN)
    ean_col = df.columns[2]
    eans = [str(ean).split('.')[0] for ean in df[ean_col].dropna().unique() if str(ean).strip() != '']

    if not eans:
        print("Nessun EAN trovato nel file.")
        return

    # ... (connessione db invariata) ...

        # Popolamento colonne D (3) e E (4)
        df['Codice Doganale'] = df[ean_col].apply(lambda x: data_map.get(str(x).split('.')[0], {}).get('customs', 'NON TROVATO'))
        df['Unità Addizionale'] = df[ean_col].apply(lambda x: data_map.get(str(x).split('.')[0], {}).get('unit', 0))

        # Riordino per avere A, B, C, D come richiesto se possibile, o aggiunta in coda
        # Qui le aggiungiamo semplicemente; se Ry vuole un template fisso possiamo forzare l'ordine.
        
        output_path = "PROCESSED_" + os.path.basename(input_path)
        if output_path.endswith('.csv'):
            df.to_csv(output_path, index=False)
        else:
            df.to_excel(output_path, index=False)
        
        print(f"File processato con successo: {output_path}")
        return output_path

    except Exception as e:
        print(f"Errore durante l'elaborazione: {e}")
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 arricchisci_dogana.py [path_file]")
    else:
        process_file(sys.argv[1])
