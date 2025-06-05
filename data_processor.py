import logging
import re
from typing import Dict, Any, List
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        logging.warning(f"Texte non-valide reçu pour nettoyage : {text}")
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,;:-]', '', text)
    return text.strip()

def parse_date(date_str: str, date_format: str = None) -> int:
    if not date_str or date_str.lower() == 'présent':
        return datetime.now().year
    try:
        if '/' in date_str or '-' in date_str:
            separator = '/' if '/' in date_str else '-'
            parts = date_str.split(separator)
            if len(parts) == 3:
                return int(parts[2])
            elif len(parts) == 2:
                return int(parts[0])
        if date_str.isdigit() and len(date_str) == 4:
            return int(date_str)
        if date_str.isdigit() and len(date_str) == 8:
            return int(date_str[4:])
        logging.warning(f"Format de date non reconnu : {date_str}")
        return None
    except (ValueError, IndexError) as e:
        logging.warning(f"Erreur lors du parsing de la date '{date_str}' : {e}")
        return None

def calculate_experience_duration(experiences: List[Dict[str, Any]]) -> int:
    total_years = 0
    current_year = datetime.now().year
    if not isinstance(experiences, list):
        logging.warning(f"Experiences n'est pas une liste : {experiences}")
        return total_years
    for exp in experiences:
        if not isinstance(exp, dict):
            logging.warning(f"Entrée d'expérience invalide : {exp}")
            continue
        date_debut = exp.get('date_debut', '')
        date_fin = exp.get('date_fin', str(current_year))
        start_year = parse_date(date_debut)
        end_year = parse_date(date_fin)
        if start_year is None or end_year is None:
            logging.warning(f"Impossible de calculer la durée pour l'expérience {exp}")
            continue
        duration = end_year - start_year
        if duration > 0:
            total_years += duration
            logging.info(f"Expérience {exp.get('poste', 'inconnue')} : {duration} ans")
        else:
            logging.warning(f"Durée négative ou nulle pour l'expérience {exp}")
    logging.info(f"Durée totale calculée : {total_years} ans")
    return total_years

def partial_match(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    common_words = words1.intersection(words2)
    total_unique_words = len(words1.union(words2))
    return len(common_words) / total_unique_words if total_unique_words > 0 else 0.0

def structure_candidate_data(groq_data: Dict[str, Any], criteria: Dict[str, Any], file_name: str) -> Dict[str, Any]:
    try:
        if not isinstance(groq_data, dict):
            logging.error(f"Données Groq invalides pour {file_name}: {groq_data}")
            return {"Erreur": "Données Groq invalides"}

        nom = groq_data.get("nom", "").strip().upper()
        prenom = groq_data.get("prenom", "").strip().capitalize()
        full_name = f"{nom} {prenom}" if nom and prenom else nom or prenom or "Inconnu"
        
        poste_vise = groq_data.get("profil", "") or groq_data.get("grade", "") or groq_data.get("discipline", "Non spécifié")
        if not poste_vise or poste_vise.lower() == "data et ia":
            for exp in groq_data.get("experiences_professionnelles", []) + groq_data.get("stages", []):
                if exp.get("poste"):
                    poste_vise = exp.get("poste")
                    break
            else:
                poste_vise = "Non spécifié"

        introduction = {
            "Nom et Prénom": full_name,
            "Âge": groq_data.get("age", None),
            "Genre": groq_data.get("genre", ""),
            "Localisation": ", ".join(set(exp.get("emplacement", "") for exp in groq_data.get("experiences_professionnelles", []) + groq_data.get("stages", []) if exp.get("emplacement")))
        }

        formations = []
        for diplome in groq_data.get("diplomes", []):
            if not isinstance(diplome, dict):
                logging.warning(f"Diplôme invalide : {diplome}")
                continue
            formations.append({
                "Établissement": diplome.get("etablissement", ""),
                "Diplôme": diplome.get("nom_diplome", ""),
                "Période": diplome.get("annee_obtention", ""),
                "Statut": diplome.get("statut", "")
            })

        score_details = {}
        total_score = 0
        max_score = 0

        if criteria.get("grade_active", False):
            candidate_grade = groq_data.get("grade", "").lower()
            required_grade = criteria.get("grade_requirement", "").lower()
            match_score = partial_match(candidate_grade, required_grade)
            score_details["Grade"] = 15 if match_score == 1.0 else int(15 * match_score)
            total_score += score_details["Grade"]
            max_score += 15

        if criteria.get("experience_globale_active", False):
            years = calculate_experience_duration(groq_data.get("experiences_professionnelles", []))
            experience_map = {"inférieur à 2 ans": (0, 2), "entre 2 et 6 ans": (2, 6), "entre 6 et 10 ans": (6, 10), "entre 10 et 15 ans": (10, 15), "+15 ans": (15, float('inf'))}
            req_range = experience_map.get(criteria.get("experience_globale_requirement", ""), (0, 2))
            if req_range[0] <= years <= req_range[1]:
                score_details["Expérience globale"] = 30
            elif years < req_range[0] and years >= req_range[0] - 2:
                score_details["Expérience globale"] = 15
            elif years > req_range[1] and years <= req_range[1] + 2:
                score_details["Expérience globale"] = 20
            else:
                score_details["Expérience globale"] = 0
            total_score += score_details["Expérience globale"]
            max_score += 30

        if criteria.get("niveau_etudes_active", False):
            highest_diploma = max((d.get("nom_diplome", "") for d in groq_data.get("diplomes", [])), default="")
            required_diploma = criteria.get("niveau_etudes_requirement", "").lower()
            diploma_mapping = {"licence professionnelle en génie électrique et énergies renouvelables": "bac+3", "diplôme de technicien en électricité de maintenance industrielle": "bac+2", "diplôme de spécialisation en électricité de bâtiment": "bac+2", "baccalauréat en sciences physiques et chimiques": "bac"}
            normalized_diploma = diploma_mapping.get(highest_diploma.lower(), highest_diploma.lower())
            diploma_levels = {"bac": 0, "bac+1": 1, "bac+2": 2, "bac+3": 3, "licence": 3, "bac+4": 4, "bac+5": 5, "master": 5, "doctorat": 8}
            candidate_level = diploma_levels.get(normalized_diploma)
            required_level = diploma_levels.get(required_diploma)
            if candidate_level is None: candidate_level = 0
            if required_level is None: required_level = 0
            level_difference = candidate_level - required_level
            if level_difference == 0:
                score_details["Niveau d'études"] = 20
            elif level_difference > 0:
                score_details["Niveau d'études"] = 15 if level_difference == 1 else 10 if level_difference == 2 else 5
            else:
                level_difference = abs(level_difference)
                score_details["Niveau d'études"] = 10 if level_difference == 1 else 5 if level_difference == 2 else 0
            total_score += score_details["Niveau d'études"]
            max_score += 20

        if criteria.get("discipline_active", False):
            discipline = groq_data.get("discipline", "").lower()
            required_discipline = criteria.get("discipline_requirement", "").lower()
            discipline_mapping = {"génie électrique et énergies renouvelables": "electrical"}
            normalized_discipline = discipline_mapping.get(discipline, discipline)
            match_score = partial_match(normalized_discipline, required_discipline)
            score_details["Discipline"] = 15 if match_score == 1.0 else int(15 * match_score)
            total_score += score_details["Discipline"]
            max_score += 15

        if criteria.get("secteur_experience_active", False):
            sectors = [exp.get("description", "").lower() for exp in groq_data.get("experiences_professionnelles", [])]
            sectors.extend([skill.lower() for skill in groq_data.get("competences_cles", [])])
            sectors.append(groq_data.get("profil", "").lower())
            required_sector = criteria.get("secteur_experience_requirement", "").lower()
            sector_keywords = {"energy": ["électrique", "énergie", "renewable", "électricité"], "construction": ["chantier", "construction"], "it": ["informatique", "data"], "manufacturing": ["industriel", "maintenance"]}
            required_keywords = sector_keywords.get(required_sector, [required_sector])
            match_found = any(any(keyword in s for keyword in required_keywords) for s in sectors)
            score_details["Secteur d'expérience"] = 20 if match_found else 0
            total_score += score_details["Secteur d'expérience"]
            max_score += 20

        normalized_score = total_score
        logging.info(f"Score total : {normalized_score}/100")

        badges = []
        remark = ""

        if criteria.get("localisation_active", False):
            locations = [(exp.get("emplacement", "") or "").lower() for exp in (groq_data.get("experiences_professionnelles", []) + groq_data.get("stages", []))]
            required_location = criteria.get("localisation_requirement", "").lower()
            matched_locations = [loc for loc in locations if required_location in loc]
            if matched_locations:
                badges.append({"name": "🌍 Location Match", "description": f"Based in {', '.join(set(matched_locations))}"})
                remark += f"Location aligns with job requirement ({required_location}). "
            elif required_location == "mobilité internationale" and locations:
                badges.append({"name": "🌍 Location Match", "description": "Shows mobility potential"})
                remark += "Candidate shows mobility potential. "

        if criteria.get("competences_active", False):
            candidate_skills = [skill.lower() for skill in groq_data.get("competences_cles", [])]
            required_skills = [skill.strip().lower() for skill in criteria.get("competences_requirement", "").split(",")]
            matched_skills = [skill for skill in candidate_skills if skill in required_skills]
            if matched_skills:
                badges.append({"name": "🛠️ Skill Fit", "description": f"Skills: {', '.join(matched_skills)}"})
                remark += f"Skills such as {', '.join(matched_skills)} are present. "

        if not badges:
            remark += "No specific location or skill alignment noted."

        score_data = {"total": normalized_score, "scores": score_details, "badges": badges, "poste_visé": poste_vise, "remarque": remark if remark else "Aucune remarque."}

        candidate_summary = {
            "Introduction": introduction,
            "Formations": formations,
            "Compétences Clés": groq_data.get("competences_cles", []),
            "Soft Skills": groq_data.get("soft_skills", []),
            "Stages": groq_data.get("stages", []),
            "Expériences Professionnelles": groq_data.get("experiences_professionnelles", []),
            "Email": groq_data.get("email", ""),
            "Téléphone": groq_data.get("telephone", ""),
            "Date de Naissance": groq_data.get("date_naissance", ""),
            "Score": score_data
        }

        return candidate_summary
    except Exception as e:
        logging.error(f"Erreur lors de la structuration des données pour {file_name} : {e}", exc_info=True)
        return {"Erreur": f"Structuration échouée : {str(e)}"}