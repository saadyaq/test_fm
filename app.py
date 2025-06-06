import streamlit as st
import asyncio
import pdfplumber
from data_extractor import extract_info_with_groq
from sentence_transformers import SentenceTransformer
import logging

# Configurer les logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure an independent event loop to avoid conflicts with PyTorch
asyncio.set_event_loop(asyncio.new_event_loop())

# Initialisation de embedding_model après le démarrage de Streamlit
embedding_model = None
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    logging.info("embedding_model initialisé avec succès.")
except Exception as e:
    logging.error(f"Erreur lors de l'initialisation de embedding_model : {e}")
    st.error(f"Erreur lors de l'initialisation de l'encodeur de texte : {e}")
    st.stop()

# Interface Streamlit
st.title("Analyseur de CV - JESA")
st.write("Téléversez un CV au format PDF pour extraire les informations pertinentes.")

# Téléversement du fichier
uploaded_file = st.file_uploader("Choisir un fichier PDF", type="pdf")

if uploaded_file is not None:
    try:
        # Extraire le texte du PDF
        logging.info(f"Traitement de {uploaded_file.name}")
        with pdfplumber.open(uploaded_file) as pdf:
            cv_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        
        # Afficher le texte extrait
        st.subheader("Texte extrait du CV")
        st.text_area("Texte brut", cv_text, height=200)

        # Extraire les informations avec Groq
        query = "Extract information from this CV"
        extracted_info = extract_info_with_groq(cv_text, query, embedding_model)

        # Afficher les résultats
        st.subheader("Informations extraites")
        if "Erreur" in extracted_info:
            st.error(f"Erreur lors de l'extraction : {extracted_info['Erreur']}")
            if "Repaired" in extracted_info:
                st.write("Données réparées :")
                st.json(extracted_info["Repaired"])
        else:
            st.json(extracted_info)

    except Exception as e:
        logging.error(f"Erreur lors du traitement du CV : {e}")
        st.error(f"Une erreur est survenue : {e}")

# Pied de page
st.write("Développé pour JESA - Juin 2025")