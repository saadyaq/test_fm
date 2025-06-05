import json
import logging
import re
from groq import Groq
import config
import json_repair
import httpx
from httpx import Timeout
from pinecone import Pinecone, ServerlessSpec
from vector_store import retrieve_relevant_segments, initialize_vector_store

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

groq_client = None
pc = None
index = None

try:
    if not config.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY non défini dans les variables d'environnement.")
    groq_client = Groq(api_key=config.GROQ_API_KEY, timeout=Timeout(30.0))
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    index = initialize_vector_store()
except NameError:
    logging.error("Modules manquants. Installez via 'pip install -r requirements.txt'.")
    raise
except Exception as e:
    logging.error(f"Erreur lors de l'initialisation des dépendances : {e}")
    raise

def clean_json(json_str: str) -> str:
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
    json_str = re.sub(r'\s+', ' ', json_str).strip()
    json_str = re.sub(r'(\"[^\"]*\"|null)(\s*\"[^\"]*\":)', r'\1,\2', json_str)
    return json_str

def generate_embedding(text: str, embedding_model) -> list:
    return embedding_model.encode(text).tolist()

def index_cv_segments(file_name: str, cv_text: str, embedding_model):
    segments = re.split(r'\n\s*\n', cv_text)
    vectors = [(f"{file_name}_{i}", generate_embedding(seg, embedding_model), {"file_name": file_name, "segment": i, "segment_text": seg}) for i, seg in enumerate(segments) if seg.strip()]
    index.upsert(vectors)

def retrieve_context(query: str) -> str:
    return retrieve_relevant_segments(query, index)

def extract_info_with_groq(cv_text: str, query: str, embedding_model) -> dict:
    try:
        index_cv_segments("temp_cv", cv_text, embedding_model)
        retrieved_context = retrieve_context(query)
        # Assure-toi que retrieved_context et cv_text sont bien des chaînes
        print(f"Retrieved Context: {retrieved_context}")
        print(f"CV Text: {cv_text}")
        prompt = config.CV_PROMPT_TEMPLATE.format(
            retrieved_context=str(retrieved_context),
            cv_text=str(cv_text)
        )
        print(f"Prompt envoyé à Groq : {prompt}")
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        # Tente de réparer le JSON avant parsing
        repaired_json = json_repair.loads(response.choices[0].message.content)
        return repaired_json
    except json.JSONDecodeError as e:
        logging.error(f"Erreur lors du parsing JSON : {e}")
        repaired_json = json_repair.loads(response.choices[0].message.content) if response.choices[0].message.content else {}
        return {"Erreur": str(e), "Repaired": repaired_json}
    except httpx.TimeoutException as e:
        logging.error(f"Timeout lors de la requête à Groq : {e}")
        return {"Erreur": "Requête à Groq a expiré"}
    except Exception as e:
        logging.error(f"Erreur inattendue : {e}")
        return {"Erreur": str(e)}