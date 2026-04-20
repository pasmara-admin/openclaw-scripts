import pandas as pd
import sys
import os

def classify_product(name):
    """
    Logica di classificazione euristica basata sulla descrizione del prodotto.
    Restituisce (Codice Doganale, Unità Addizionale).
    """
    name = str(name).upper()
    
    # Ombrelli e Ombrelloni
    if 'OMBRELLONE' in name or 'OMBRELLO' in name:
        return '66011000', 1
    
    # Mobili in Legno (Tavoli, Panche, Sedie, Librerie)
    if any(k in name for k in ['TAVOLO', 'MOBILE', 'PANCA', 'SEDIA', 'LIBRERIA', 'SCAFFALE']) and \
       any(k in name for k in ['LEGNO', 'ACACIA', 'NOCE', 'ROVERE', 'PINO', 'BAMBU', 'TEAK']):
        return '94036010', 0
    
    # Mobili in Metallo / Lettini / Sdraio (Classificazione comune per arredamento esterno)
    if any(k in name for k in ['LETTINO', 'SDRAIO', 'SPIAGGINA', 'DONDOLO', 'BASCULA', 'PIEGHEVOLE']):
        return '94017900', 0
    
    # Gazebo e Tende
    if 'GAZEBO' in name or 'TENDA' in name:
        return '63062200', 0
        
    # Barbecue e Accessori Cottura
    if any(k in name for k in ['BARBECUE', 'GRIGLIA', 'PIASTRA', 'FORNO']):
        return '73211190', 0
    
    # Cuscini e Articoli da Letto
    if 'CUSCINO' in name or 'MATERASSO' in name:
        return '94049090', 0
        
    # Manufatti in legno generici (Fioriere, Cancelli, Steccati)
    if any(k in name for k in ['FIORIERA', 'GRIGLIA', 'CANCELLO', 'RECINTO', 'PANNELLO']) and 'LEGNO' in name:
        return '44219999', 0
        
    # Basi per Ombrellone (Pietra/Cemento)
    if 'BASE' in name and any(k in name for k in ['KG', 'MARMO', 'GRANITO', 'CEMENTO']):
        return '68029990', 0

    # Mobili in plastica
    if 'POLIPROPILENE' in name or 'RESINA' in name:
        return '94037000', 0

    # Default: Altri mobili in metallo (voce generica molto comune per il nostro catalogo)
    return '94032080', 0

def process_file(input_path):
    # Caricamento file
    if input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
    else:
        df = pd.read_excel(input_path)

    # Ry structure: Col A (SKU), Col B (Name), Col C (EAN)
    # Verifichiamo di avere almeno 3 colonne
    if len(df.columns) < 3:
        print("Errore: Il file deve avere almeno 3 colonne (SKU, Nome, EAN).")
        return

    name_col = df.columns[1]
    
    print(f"Esecuzione classificazione AI su {len(df)} righe...")
    
    # Applicazione logica di classificazione
    results = df[name_col].apply(classify_product)
    
    # Popolamento colonne D ed E
    df['Codice Doganale'] = [res[0] for res in results]
    df['Unità Addizionale'] = [res[1] for res in results]

    output_path = "PROCESSED_" + os.path.basename(input_path)
    if output_path.endswith('.csv'):
        df.to_csv(output_path, index=False)
    else:
        df.to_excel(output_path, index=False)
    
    print(f"File processato con successo: {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 arricchisci_dogana.py [path_file]")
    else:
        process_file(sys.argv[1])
