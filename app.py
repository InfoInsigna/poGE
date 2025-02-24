import streamlit as st
import pandas as pd
import requests
import os
os.system("pip install openpyxl")


# --- 📌 Configuration API Pipefy ---
PIPEFY_API_URL = "https://api.pipefy.com/graphql"
PIPEFY_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3MzIxMjY5NTcsImp0aSI6ImQwM2NkNDdhLWQyZjItNDZjMi04YjllLTcyZTY1YjU0N2MxOSIsInN1YiI6MzAyMjYwMDEzLCJ1c2VyIjp7ImlkIjozMDIyNjAwMTMsImVtYWlsIjoiaW5mb0BpbnNpZ25hY29uc3VsdG9yaWEuY29tLmJyIn19.1seVSjoEzFsWeTbgTmik56V1fVOPfnz559IwF1xP-A6vX5QTKT6bh3oYpeSs_pILSvOlVSt4LFXK0N--kXFEFw"
PIPE_ID = 304651818  # ID du pipe
DATABASE_ID = 303088910  # ID de la database des institutions

HEADERS = {
    "Authorization": f"Bearer {PIPEFY_TOKEN}",
    "Content-Type": "application/json"
}

# --- 📌 Interface Streamlit ---
st.title("📥 Importer un fichier Excel et envoyer à Pipefy")

# Upload du fichier Excel
uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="Consolidado")
    
    # Affichage d'un aperçu
    st.write("📌 Aperçu des données :", df.head())

    # Extraire les PO et institutions (sans doublons)
    df_cards = df[["Nome da instituição (Fornecedor)", "PO"]].drop_duplicates()
    df_cards.rename(columns={"Nome da instituição (Fornecedor)": "institui_o_ge", "PO": "n_po"}, inplace=True)

    # --- 📌 Fonction pour récupérer l'ID de l'institution dans la database Pipefy ---
    def get_institution_id(name):
        query = f"""
        query {{
            table_record_search(table_id: {DATABASE_ID}, search: "{name}") {{
                edges {{
                    node {{
                        id
                        record_fields {{
                            name
                            value
                        }}
                    }}
                }}
            }}
        }}
        """
        response = requests.post(PIPEFY_API_URL, json={"query": query}, headers=HEADERS)
        data = response.json()

        if "data" in data and "table_record_search" in data["data"]:
            edges = data["data"]["table_record_search"]["edges"]
            if edges:
                return edges[0]["node"]["id"]  # Retourne l'ID de la première correspondance
        
        return None  # Retourne None si aucune correspondance n'est trouvée

    # --- 📌 Bouton pour envoyer les cartes à Pipefy ---
    if st.button("📤 Envoyer les données à Pipefy"):
        results = []

        for _, row in df_cards.iterrows():
            institution_id = get_institution_id(row["institui_o_ge"])
            
            if not institution_id:
                results.append(f"❌ Institution non trouvée : {row['institui_o_ge']}")
                continue

            # Création de la mutation GraphQL pour Pipefy
            mutation = f"""
            mutation {{
                createCard(input: {{
                    pipe_id: {PIPE_ID},
                    fields_attributes: [
                        {{field_id: "n_po", field_value: "{row['n_po']}"}},
                        {{field_id: "institui_o_ge", field_value: "{institution_id}"}}
                    ]
                }}) {{
                    card {{
                        id
                    }}
                }}
            }}
            """
            
            response = requests.post(PIPEFY_API_URL, json={"query": mutation}, headers=HEADERS)
            data = response.json()

            if "errors" in data:
                results.append(f"❌ Erreur pour PO {row['n_po']}: {data['errors']}")
            else:
                results.append(f"✅ Card créé pour PO {row['n_po']} - Institution: {row['institui_o_ge']}")

        # Afficher les résultats
        st.write("📌 Résultats de l'import :", results)
