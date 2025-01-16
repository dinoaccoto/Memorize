import os
import pandas as pd
import streamlit as st
import random

def carica_file_txt(nome_file):
    try:
        # Legge il file di testo con tab come delimitatore
        df = pd.read_csv(nome_file, delimiter="\t")
        return df
    except Exception as e:
        st.error(f"Error while loading the file {nome_file}: {e}")
        return None

def crea_batch(tabella, batch_size):
    return [tabella[i:i + batch_size] for i in range(0, len(tabella), batch_size)]

def raggruppa_righe(tabella, r_el):
    # Raggruppa le righe della tabella in gruppi di r_el righe
    rows = len(tabella)
    grouped_data = []
    for i in range(0, rows, r_el):
        chunk = tabella.iloc[i:i+r_el]
        combined_row = []
        for col in tabella.columns:
            # Unisce il contenuto delle righe di questa colonna con un a capo
            combined_value = "\n".join(map(str, chunk[col]))
            combined_row.append(combined_value)
        grouped_data.append(combined_row)
    new_df = pd.DataFrame(grouped_data, columns=tabella.columns)
    return new_df

# Inizializza lo stato
if "riga" not in st.session_state:
    st.session_state["riga"] = 0

if "batch_index" not in st.session_state:
    st.session_state["batch_index"] = 0

if "batches" not in st.session_state:
    st.session_state["batches"] = []

if "no_list" not in st.session_state:
    st.session_state["no_list"] = []

if "total_answers" not in st.session_state:
    st.session_state["total_answers"] = 0

if "yes_count" not in st.session_state:
    st.session_state["yes_count"] = 0

if "no_count" not in st.session_state:
    st.session_state["no_count"] = 0

if "mostra_dettagli" not in st.session_state:
    st.session_state["mostra_dettagli"] = False

if "in_riproposizione" not in st.session_state:
    st.session_state["in_riproposizione"] = False

if "answered" not in st.session_state:
    st.session_state["answered"] = False

if "colonne_da_mostrare" not in st.session_state:
    st.session_state["colonne_da_mostrare"] = None

# Mostra i file .txt presenti nella directory "cards"
txt_files = sorted([f for f in os.listdir("cards") if f.endswith(".txt")])
if not txt_files:
    st.error("No .txt files found in the 'cards' folder. Add files to continue.")
    st.stop()

# Se la tabella non è stata ancora caricata, chiedi all'utente di selezionare file, r_el, k, batch_size e shuffle
if "tabella" not in st.session_state:
    nome_file = st.selectbox("Select the file to upload:", txt_files, index=0)
    r_el = st.number_input("Rows in an element:", min_value=1, value=1)
    k = st.number_input("Columns in an element:", min_value=1, value=1)
    batch_size = st.number_input("Elements in a batch:", min_value=1, value=10)
    shuffle_choice = st.radio("Shuffle?", ("Yes", "No"), index=0)

    if st.button("Upload"):
        # Carica la tabella
        percorso_file = os.path.join("cards", nome_file)
        tabella = carica_file_txt(percorso_file)
        if tabella is not None:
            # Prima raggruppa le righe
            tabella = raggruppa_righe(tabella, r_el)
            # Mischia le righe solo se l'utente ha scelto "Sì"
            if shuffle_choice == "Sì":
                seed = random.randint(10,50)
                tabella = tabella.sample(frac=1, random_state=seed).reset_index(drop=True)
            st.session_state["batches"] = crea_batch(tabella, batch_size)
            st.session_state["tabella"] = tabella
            st.session_state["colonne_da_mostrare"] = k
            st.rerun()
    else:
        st.stop()

# Da qui in avanti la tabella è caricata
batches = st.session_state["batches"]
batch_index = st.session_state["batch_index"]

# Determina il batch corrente
if st.session_state["in_riproposizione"] and st.session_state["no_list"]:
    # Usa gli elementi con risposta "No"
    batch = pd.DataFrame(st.session_state["no_list"]).reset_index(drop=True)
else:
    # Usa il batch normale
    batch = batches[batch_index] if batch_index < len(batches) else None

if batch is not None:
    riga = st.session_state["riga"]

    if riga < len(batch):
        st.write(f"### Batch {batch_index + 1}/{len(batches)}, Elemento {riga + 1}/{len(batch)}")

        # Mostra il contenuto delle prime k colonne, tutte insieme, prima del pulsante "Check"
        k = st.session_state["colonne_da_mostrare"]
        dettaglio_iniziale = ""
        for col_index in range(min(k, len(batch.columns))):
            valore = batch.iloc[riga, col_index]
            valore_formattato = valore.replace("\n", "<br>")
            # Rendiamo in grassetto la prima colonna, le altre possono rimanere in semplice testo.
            # Ma se si preferisce, si possono tutte rendere in grassetto.
            
            dettaglio_iniziale += f"**{valore_formattato}**<br>"

        st.markdown(dettaglio_iniziale, unsafe_allow_html=True)

        # Mostra il pulsante "Check"
        if st.button("Check", key=f"check_{riga}"):
            st.session_state["mostra_dettagli"] = True
            st.session_state["answered"] = False  # Reset dopo aver premuto Check

        if st.session_state["mostra_dettagli"]:
            # Qui si mostra TUTTA la riga (tutte le colonne) in dettaglio formattato,
            # come prima, senza modifiche
            dettagli_str = ""
            for col in batch.columns:
                col_valore = batch.iloc[riga][col].replace("\n", " ")
                dettagli_str += f"*{col}:* **{col_valore}**<br>"

            st.markdown(dettagli_str, unsafe_allow_html=True)

            # Disposizione dei pulsanti: Yes - Next - No
            col1, col2, col3 = st.columns([1, 1, 1])

            # Pulsante Yes
            if col1.button("Yes", key=f"yes_{riga}"):
                st.session_state["yes_count"] += 1
                st.session_state["total_answers"] += 1
                st.session_state["answered"] = True  # Risposta fornita

            # Pulsante No
            if col3.button("No", key=f"no_{riga}"):
                st.session_state["no_count"] += 1
                st.session_state["total_answers"] += 1
                # Aggiunge la riga attuale alla lista "No"
                st.session_state["no_list"].append(batch.iloc[riga])
                st.session_state["answered"] = True  # Risposta fornita

            # Mostra il pulsante Next solo dopo che è stata fornita una risposta (Yes o No)
            if st.session_state["answered"]:
                if col2.button("Next", key=f"next_{riga}"):
                    st.session_state["riga"] += 1  # Avanza alla riga successiva
                    st.session_state["mostra_dettagli"] = False
                    st.session_state["answered"] = False
                    st.rerun()

    else:
        # Quando termina il batch corrente
        if st.session_state["in_riproposizione"]:
            st.write("Review of elements completed.")
            st.session_state["no_list"] = []  # Resetta la lista "No"
            st.session_state["in_riproposizione"] = False
            st.session_state["batch_index"] += 1  # Passa al batch successivo
        else:
            st.write(f"Batch {batch_index + 1} completed!")

            if st.session_state["no_list"]:
                st.write("Review of the items with wrong answers.")
                st.session_state["in_riproposizione"] = True
            else:
                st.session_state["batch_index"] += 1  # Passa al batch successivo

        st.session_state["riga"] = 0  # Reset della riga
        if st.button("Next"):
            st.rerun()

else:
    st.write("All batches completed.")
    st.write(f"Total answers: {st.session_state['total_answers']}")
    st.write(f"Yes: {st.session_state['yes_count']}")
    st.write(f"No: {st.session_state['no_count']}")
