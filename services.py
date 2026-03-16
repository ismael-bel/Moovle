import os
import json
import logging
import requests
from typing import List, Dict, Any
from google import genai
from dotenv import load_dotenv

# Logs pour débugger plus facilement
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Clés API chargées depuis .env, jamais hardcodées dans le code
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TMDB_KEY   = os.getenv("TMDB_API_KEY")

# Client Gemini
client = genai.Client(api_key=GEMINI_KEY)


def get_movie_poster(titre_film: str) -> str:
    """Récupère l'affiche d'un film via TMDB, retourne un placeholder si introuvable."""
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={titre_film}&language=fr-FR"
    try:
        response = requests.get(url, timeout=5).json()
        if response.get('results') and response['results'][0].get('poster_path'):
            path = response['results'][0]['poster_path']
            return f"https://image.tmdb.org/t/p/w500{path}"
    except Exception as e:
        logging.error(f"Erreur affiche '{titre_film}': {e}")
    return "https://via.placeholder.com/500x750?text=Image+Non+Disponible"


def get_streaming_logos(titre_film: str) -> List[Dict[str, str]]:
    """Retourne les plateformes de streaming dispo en France pour un film (données JustWatch via TMDB)."""
    try:
        # D'abord on récupère l'id TMDB du film
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={titre_film}&language=fr-FR"
        search_res = requests.get(search_url, timeout=5).json()

        if not search_res.get('results'):
            return []

        movie_id = search_res['results'][0]['id']

        # Ensuite on récupère les providers pour la France
        prov_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_KEY}"
        prov_res = requests.get(prov_url, timeout=5).json()

        # On garde uniquement les abonnements flatrate (Netflix, Prime, etc.)
        if 'FR' in prov_res.get('results', {}) and 'flatrate' in prov_res['results']['FR']:
            plateformes = prov_res['results']['FR']['flatrate']
            return [
                {"url": f"https://image.tmdb.org/t/p/w45{p['logo_path']}", "nom": p['provider_name']}
                for p in plateformes
            ]
    except Exception as e:
        logging.error(f"Erreur plateformes '{titre_film}': {e}")
    return []


def recommander_films(likes: List[str], dislikes: List[str], mode: str = "classique") -> Dict[str, Any]:
    """
    Génère 3 recommandations via Gemini.
    Le paramètre mode permet de basculer en mode 'surprise' pour sortir de la zone de confort.
    """
    # Instruction supplémentaire selon le mode choisi
    instruction_mode = ""
    if mode == "surprise":
        instruction_mode = "3. Ignore les genres des films cités. Recommande des films de genres, époques ou pays COMPLÈTEMENT différents. Explique brièvement pourquoi ce choix inattendu va quand même plaire à l'utilisateur."

    prompt = f"""
    RÔLE : Tu es un expert en cinéma. Ton but est de recommander 3 excellents films selon les goûts de l'utilisateur.

    PROFIL :
    - Aime       : {", ".join(likes) if likes else "Aucun"}
    - N'aime pas : {", ".join(dislikes) if dislikes else "Aucun"}

    CONTRAINTES :
    1. Ne recommande JAMAIS un film déjà présent dans les listes ci-dessus.
    2. Choisis des films de très grande qualité (critique ou public).
    {instruction_mode}

    FORMAT STRICT :
    Génère UNIQUEMENT un objet JSON valide avec cette structure (et rien d'autre) :
    {{
      "recommandations": [
        {{"titre": "Nom du film", "resume": "Un petit résumé accrocheur de l'histoire en 1 ou 2 phrases max."}}
      ]
    }}
    """
    try:
        # response_mime_type force Gemini à répondre en JSON valide
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(response.text)
    except Exception as e:
        logging.error(f"Erreur Gemini: {e}")
        # On vérifie si l'erreur est liée au quota (429)
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            return {"error": "quota"}
        return {"error": "inconnue"}
