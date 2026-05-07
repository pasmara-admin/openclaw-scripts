import pandas as pd
import mysql.connector
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
    
    # Mobili in Metallo / Lettini / Sdraio
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
        
    # Manufatti in legno generici (Fioriere, Cancelli)
    if any(k in name for k in ['FIORIERA', 'GRIGLIA', 'CANCELLO', 'RECINTO', 'PANNELLO']) and 'LEGNO' in name:
        return '44219999', 0
        
    # Basi per Ombrellone (Pietra/Cemento)
    if 'BASE' in name and any(k in name for k in ['KG', 'MARMO', 'GRANITO', 'CEMENTO']):
        return '68029990', 0

    # Mobili in plastica
    if 'POLIPROPILENE' in name or 'RESINA' in name:
        return '94037000', 0

    # Default: Altri mobili in metallo
    return '94032080', 0

def get_prestashop_info(skus):
    """
    Recupera nome e descrizione da Prestashop basandosi sullo SKU (reference).
    """
    ps_data = {}
    try:
        db = mysql.connector.connect(
            host='62.84.190.199',
            user='john',
            password='qARa6aRozi6I',
            database='produceshop',
            ssl_disabled=True
        )
        cursor = db.cursor(dictionary=True)
        
        # Gestione batch per performance
        format_strings = ','.join(['%s'] * len(skus))
        query = f"""
            SELECT p.reference, pl.name, pl.description_short 
            FROM ps_product p
            JOIN ps_product_lang pl ON p.id_product = pl.id_product
            WHERE p.reference IN ({format_strings}) AND pl.id_lang = 1 AND pl.id_shop = 1
        """
        cursor.execute(query, tuple(skus))
        results = cursor.fetchall()
        
        for res in results:
            # Pulizia HTML minima dalla descrizione
            clean_desc = res['description_short'].replace('<p>', '').replace('</p>', ' ').replace('<br />', ' ').strip()
            ps_data[res['reference']] = f"{res['name']} {clean_desc}"
            
    except Exception as e:
        print(f"Errore connessione Prestashop: {e}")
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()
    return ps_data

def process_file(input_path):
    if input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
    else:
        df = pd.read_excel(input_path)

    if len(df.columns) < 3:
        print("Errore: Il file deve avere almeno 3 colonne (SKU, Nome, EAN).")
        return

    sku_col = df.columns[0]
    name_col = df.columns[1]
    
    # Lista SKU per query Prestashop
    skus = [str(sku).strip() for sku in df[sku_col].dropna().unique() if str(sku).strip() != '']
    
    print("Recupero informazioni estese da Prestashop...")
    ps_info = get_prestashop_info(skus)
    
    print(f"Esecuzione classificazione su {len(df)} righe...")
    
    results_dogana = []
    results_unita = []
    
    for _, row in df.iterrows():
        sku = str(row[sku_col]).strip()
        name_file = str(row[name_col])
        
        # Se la descrizione nel file è corta (<15 caratteri) e abbiamo info da PS, usiamo quelle
        extended_name = ps_info.get(sku, name_file)
        if len(name_file) < 15 and sku in ps_info:
            final_name = extended_name
        else:
            final_name = name_file
            
        dogana, unita = classify_product(final_name)
        results_dogana.append(dogana)
        results_unita.append(unita)
    
    df['Codice Doganale'] = results_dogana
    df['Unità Addizionale'] = results_unita

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
