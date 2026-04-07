import os
import json
import logging
import requests
from typing import List, Dict, Any
from google import genai
from dotenv import load_dotenv

# Logs for easier debugging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# API keys loaded from .env, never hardcoded in the source
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TMDB_KEY   = os.getenv("TMDB_API_KEY")

# Gemini Client
client = genai.Client(api_key=GEMINI_KEY)


def get_movie_poster(titre_film: str) -> str:
    """Fetches a movie poster via TMDB; returns a placeholder if not found."""
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={titre_film}&language=en-US"
    try:
        response = requests.get(url, timeout=5).json()
        if response.get('results') and response['results'][0].get('poster_path'):
            path = response['results'][0]['poster_path']
            return f"https://image.tmdb.org/t/p/w500{path}"
    except Exception as e:
        logging.error(f"Error fetching poster for '{titre_film}': {e}")
    return "https://via.placeholder.com/500x750?text=Image+Not+Available"


def get_streaming_logos(titre_film: str) -> List[Dict[str, str]]:
    """Returns streaming platforms available in France for a movie (JustWatch data via TMDB)."""
    try:
        # First, retrieve the TMDB movie ID
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={titre_film}&language=en-US"
        search_res = requests.get(search_url, timeout=5).json()

        if not search_res.get('results'):
            return []

        movie_id = search_res['results'][0]['id']

        # Next, retrieve the providers for France
        prov_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_KEY}"
        prov_res = requests.get(prov_url, timeout=5).json()

        # Only keep 'flatrate' subscriptions (Netflix, Prime, etc.)
        if 'FR' in prov_res.get('results', {}) and 'flatrate' in prov_res['results']['FR']:
            plateformes = prov_res['results']['FR']['flatrate']
            return [
                {"url": f"https://image.tmdb.org/t/p/w45{p['logo_path']}", "nom": p['provider_name']}
                for p in plateformes
            ]
    except Exception as e:
        logging.error(f"Error fetching platforms for '{titre_film}': {e}")
    return []


def recommander_films(likes: List[str], dislikes: List[str], mode: str = "classique") -> Dict[str, Any]:
    """
    Generates 3 recommendations via Gemini.
    The 'mode' parameter allows switching to 'surprise' mode to step out of the user's comfort zone.
    """
    # Additional instructions based on the chosen mode
    instruction_mode = ""
    if mode == "surprise":
        instruction_mode = "3. Ignore the genres of the mentioned movies. Recommend movies from COMPLETELY different genres, eras, or countries. Briefly explain why this unexpected choice will still appeal to the user."

    prompt = f"""
    ROLE: You are a cinema expert. Your goal is to recommend 3 excellent movies based on the user's tastes.

    PROFILE:
    - Likes    : {", ".join(likes) if likes else "None"}
    - Dislikes : {", ".join(dislikes) if dislikes else "None"}

    CONSTRAINTS:
    1. NEVER recommend a movie already present in the lists above.
    2. Choose high-quality movies (critically acclaimed or audience favorites).
    {instruction_mode}

    STRICT FORMAT:
    ONLY generate a valid JSON object with this structure (and nothing else):
    {{
      "recommandations": [
        {{"titre": "Movie Title", "resume": "A catchy short summary of the story in 1 or 2 sentences max."}}
      ]
    }}
    """
    try:
        # response_mime_type forces Gemini to respond with valid JSON
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(response.text)
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        # Check if the error is related to quota (429)
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            return {"error": "quota"}
        return {"error": "unknown"}
