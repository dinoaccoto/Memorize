import os
import pandas as pd
import streamlit as st
import random

# Funzione per caricare il file .txt
def carica_file_txt(nome_file):
    try:
        # Legge il file di testo con tab come delimitatore
        df = pd.read_csv(nome_file, delimiter="\t")
        return df
    except Exception as e:
        st.error(f"Error while loading the file {nome_file}: {e}")
        return None

# Funzione per creare i batch
def crea_batch(tabella, batch_size):
    return [tabella[i:i + batch_size] for i in range(0, len(tabella), batch_size)]

# Funzione per raggruppare righe
def raggruppa_righe(tabella, r_el):
    rows = len(tabella)
    grouped_data = []
    for i in range(0, rows, r_el):
        chunk = tabella.iloc[i:i + r_el]
        combined_row = []
        for col in tabella.columns:
            combined_value = "\n".join(map(str, chunk[col]))
            combined_row.append(combined_value)
        grouped_data.append(combined_row)
    new_df = pd.DataFrame(grouped_data, columns=tabella.columns)
    return new_df

# Inizializza lo stato
if "selected_directory" not in st.session_state:
    st.session_state["selected_directory"] = None

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

# Mostra il dropdown menu delle directory solo se non è stata ancora selezionata una directory
if st.session_state["selected_directory"] is None:
    subfolders = sorted([f for f in os.listdir("cards") if os.path.isdir(os.path.join("cards", f))])
    if not subfolders:
        st.error("No folders found in the 'cards' directory. Add folders to continue.")
        st.stop()
    selected_subfolder = st.selectbox("Select a folder:", subfolders, index=0)
    if st.button("Confirm folder"):
        st.session_state["selected_directory"] = selected_subfolder
        st.rerun()

else:
    # Usa la directory selezionata
    selected_path = os.path.join("cards", st.session_state["selected_directory"])

    # Mostra il dropdown menu dei file .txt solo se il file non è stato ancora caricato
    if "tabella" not in st.session_state:
        txt_files = sorted([f for f in os.listdir(selected_path) if f.endswith(".txt")])
        if not txt_files:
            st.error(f"No .txt files found in the '{st.session_state['selected_directory']}' folder. Add files to continue.")
            st.stop()

        nome_file = st.selectbox("Select the file to upload:", txt_files, index=0)
        r_el = st.number_input("Rows in an element:", min_value=1, value=1)
        k = st.number_input("Columns in an element:", min_value=1, value=1)
        batch_size = st.number_input("Elements in a batch:", min_value=1, value=10)
        shuffle_choice = st.radio("Shuffle?", ("Yes", "No"), index=0)

        col1, col2 = st.columns([1, 1])
        if col1.button("Back"):
            st.session_state["selected_directory"] = None
            st.rerun()
        if col2.button("Upload"):
            percorso_file = os.path.join(selected_path, nome_file)
            tabella = carica_file_txt(percorso_file)
            if tabella is not None:
                tabella = raggruppa_righe(tabella, r_el)
                if shuffle_choice == "Yes":
                    seed = random.randint(10, 50)
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

    if st.session_state["in_riproposizione"] and st.session_state["no_list"]:
        batch = pd.DataFrame(st.session_state["no_list"]).reset_index(drop=True)
    else:
        batch = batches[batch_index] if batch_index < len(batches) else None

    if batch is not None:
        riga = st.session_state["riga"]

        if riga < len(batch):
            st.write(f"### Batch {batch_index + 1}/{len(batches)} - {len(batch) - riga} remaining")
            k = st.session_state["colonne_da_mostrare"]
            dettaglio_iniziale = ""
            for col_index in range(min(k, len(batch.columns))):
                valore = batch.iloc[riga, col_index]
                valore_formattato = valore.replace("\n", "<br>")
                dettaglio_iniziale += f"**{valore_formattato}**<br>"

            st.markdown(dettaglio_iniziale, unsafe_allow_html=True)

            if st.button("Check", key=f"check_{riga}"):
                st.session_state["mostra_dettagli"] = True
                st.session_state["answered"] = False

            if st.session_state["mostra_dettagli"]:
                dettagli_str = ""
                for col in batch.columns:
                    col_valore = batch.iloc[riga][col].replace("\n", " ")
                    dettagli_str += f"*{col}:* **{col_valore}**<br>"

                st.markdown(dettagli_str, unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

                if col1.button("Back", key=f"back_{riga}"):
                    if st.session_state["riga"] > 0:
                        st.session_state["riga"] -= 1
                        st.session_state["mostra_dettagli"] = False
                        st.session_state["answered"] = False
                        st.rerun()
                    elif st.session_state["batch_index"] > 0:
                        st.session_state["batch_index"] -= 1
                        st.session_state["riga"] = len(st.session_state["batches"][st.session_state["batch_index"]]) - 1
                        st.session_state["mostra_dettagli"] = False
                        st.session_state["answered"] = False
                        st.rerun()

                if col2.button("Yes", key=f"yes_{riga}"):
                    st.session_state["yes_count"] += 1
                    st.session_state["total_answers"] += 1
                    st.session_state["answered"] = True

                if col4.button("No", key=f"no_{riga}"):
                    st.session_state["no_count"] += 1
                    st.session_state["total_answers"] += 1
                    st.session_state["no_list"].append(batch.iloc[riga])
                    st.session_state["answered"] = True

                if st.session_state["answered"]:
                    if col3.button("Next", key=f"next_{riga}"):
                        st.session_state["riga"] += 1
                        st.session_state["mostra_dettagli"] = False
                        st.session_state["answered"] = False
                        st.rerun()

        else:
            if st.session_state["in_riproposizione"]:
                st.write("Review of elements completed.")
                st.session_state["no_list"] = []
                st.session_state["in_riproposizione"] = False
                st.session_state["batch_index"] += 1
            else:
                st.write(f"Batch {batch_index + 1} completed!")
                if st.session_state["no_list"]:
                    st.write("Let's review wrong answers...")
                    st.session_state["in_riproposizione"] = True
                else:
                    st.session_state["batch_index"] += 1

            st.session_state["riga"] = 0
            st.rerun()
    else:
        st.write("All batches completed!")
        st.stop()
