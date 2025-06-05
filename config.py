import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")

# Secteurs similaires à JESA
SIMILAR_SECTORS = ["Acids", "Buildings", "Energy", "Fertilizer & Chemical", "Ports", "Transport", "Water", "Mining"]

# Grades définis chez JESA
GRADES = [
    "administrative assistant", "Constructability Engineer", "construction Supervisor",
    "construction Superintendent", "construction engineer", "Quality Control Inspector",
    "Completions & Commissioning technician", "Completions & Commissioning Specialist",
    "construction manager", "quality control manager", "Completions & Commissioning manager"
]

# Disciplines couvertes par JESA
DISCIPLINES = [
    "HVAC", "Mechanical", "Process", "Electrical", "AWP", "Field Leadership", "Corporate",
    "Instrumentation & Control", "Piping", "Civil", "Structural Steel", "Administrative Assistance",
    "Civil & Structural Steel", "Electrical & Instrumentation", "Mechanical & Piping", "Welding", "data et ia"
]

# Diplômes possibles
DIPLOMAS = ["bac+2", "bac+3", "bac+4", "bac+5", "bac+6", "doctorat"]

# Options pour l'expérience globale
EXPERIENCE_GLOBALE = [
    "inférieur à 2 ans", "entre 2 et 6 ans", "entre 6 et 10 ans", "entre 10 et 15 ans", "+15 ans"
]

CV_PROMPT_TEMPLATE = """
Contexte récupéré : {retrieved_context}
Texte du CV :
---
{cv_text}
---

Extraire les informations suivantes sous forme de JSON strictement structuré. Si une information n'est pas trouvée, utilisez "null" ou une liste vide pour les champs complexes. Le format doit être exact :

{
  "nom": "Nom de famille (string|null)",
  "prenom": "Prénom (string|null)",
  "email": "Adresse email principale (string|null)",
  "telephone": "Numéro de téléphone principal (string|null)",
  "age": "Âge explicite si mentionné (integer|null). Si non mentionné mais date de naissance présente, calcule l’âge en années complètes à 2025.",
  "date_naissance": "Date de naissance (string 'YYYY-MM-DD' ou 'YYYY'|null)",
  "genre": "Genre ('Masculin' ou 'Féminin') uniquement si explicitement mentionné ou certain via prénom. Sinon ''",
  "nationalite": "Nationalité (string|null) uniquement si explicitement mentionnée",
  "grade": "Grade ('administrative assistant', 'Constructability Engineer', etc.) basé sur expérience. Sinon ''",
  "discipline": "Domaine principal des études (string|null, ex. 'BigData')",
  "diplomes": [{"nom_diplome": "string|null", "etablissement": "string|null", "annee_obtention": "string|null", "statut": "string|null"}],
  "stages": [{"entreprise": "string|null", "poste": "string|null", "duree": "string|null", "emplacement": "string|null", "description": "string|null"}],
  "experiences_professionnelles": [{"entreprise": "string|null", "poste": "string|null", "date_debut": "string|null", "date_fin": "string|null", "emplacement": "string|null", "description": "string|null"}],
  "competences_cles": ["string|null"],
  "soft_skills": ["string|null"],
  "profil": "string|null"
}

Retourne UNIQUEMENT le JSON, sans texte supplémentaire.
"""