import streamlit as st
import pandas as pd
import requests

# --- Configuration de Streamlit ---
st.title("📥 Importa o arquivo de PO aqui.")

# Upload du fichier Excel
uploaded_file = st.file_uploader("Escolhe seu arquivo excel", type=["xlsx"])

# Vérifier si un fichier est uploadé
if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="Consolidado")
    
    # Affichage des premières lignes
    st.write("Seus dados :", df.head())

    # Extraire les PO uniques
    po_groups = df.groupby("PO")

    # Bouton pour envoyer les cartes à Pipefy
    if st.button("📤 Envoyer les données à Pipefy"):
        pipefy_token = "TON_PIPEFY_TOKEN_ICI"
        pipe_id = "TON_PIPE_ID_ICI"

        headers = {
            "Authorization": f"Bearer {pipefy_token}",
            "Content-Type": "application/json"
        }

        results = []

        for po, data in po_groups:
            # Récupération des données clés pour chaque PO
            po_data = {
                "po_number": po,
                "collaborators": data["Colaborador"].tolist(),
                "emails": data["Email do colaborador"].tolist(),
                "institution": data["Nome da instituição (Fornecedor)"].iloc[0],
                "investment": data["Previsão de Investimento Anual (Valor do PO)"].iloc[0],
                "unit": data["Unidade de negocio"].iloc[0],
                "billing_cnpj": data["CNPJ de faturamento"].iloc[0],
            }

            # Création du payload pour Pipefy
            mutation = """
            mutation {
                createCard(input: {
                    pipe_id: %s,
                    fields_attributes: [
                        {field_id: "po_number", field_value: "%s"},
                        {field_id: "collaborators", field_value: "%s"},
                        {field_id: "emails", field_value: "%s"},
                        {field_id: "institution", field_value: "%s"},
                        {field_id: "investment", field_value: "%s"},
                        {field_id: "unit", field_value: "%s"},
                        {field_id: "billing_cnpj", field_value: "%s"}
                    ]
                }) {
                    card {
                        id
                    }
                }
            }
            """ % (pipe_id, po_data["po_number"], ",".join(po_data["collaborators"]),
                   ",".join(po_data["emails"]), po_data["institution"],
                   po_data["investment"], po_data["unit"], po_data["billing_cnpj"])

            response = requests.post("https://api.pipefy.com/graphql", json={"query": mutation}, headers=headers)

            if response.status_code == 200:
                results.append(f"PO {po} - ✅ Créé avec succès")
            else:
                results.append(f"PO {po} - ❌ Erreur lors de la création")

        # Afficher les résultats
        st.write("Résultats de l'import :", results)
