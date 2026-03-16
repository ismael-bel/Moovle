import streamlit as st
from services import recommander_films, get_movie_poster, get_streaming_logos

# Config de base
st.set_page_config(page_title="Moovle", layout="wide")

# CSS custom pour le style Google
st.markdown("""
    <style>
    @import url('https://fonts.cdnfonts.com/css/product-sans');

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    .google-logo {
        font-family: 'Product Sans', sans-serif;
        font-size: 75px;
        font-weight: bold;
        text-align: center;
        margin-top: 30px;
        margin-bottom: 30px;
        letter-spacing: -2px;
    }
    .blue { color: #4285F4; } .red { color: #EA4335; }
    .yellow { color: #FBBC05; } .green { color: #34A853; }

    div[data-baseweb="input"] {
        border-radius: 50px !important;
        border: 1px solid #dfe1e5 !important;
        box-shadow: 0 1px 6px rgba(32,33,36,0.18) !important;
        padding: 5px 15px !important;
    }

    .stButton { text-align: center; }
    .stButton>button {
        border-radius: 4px; background-color: #f8f9fa; color: #3c4043;
        border: 1px solid #f8f9fa; padding: 10px 20px; margin-top: 15px;
    }
    .stButton>button:hover { border: 1px solid #dadce0; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# Streamlit recharge le script à chaque action, session_state permet de garder les données en mémoire
if 'recos' not in st.session_state:
    st.session_state.recos = []
if 'historique_notes' not in st.session_state:
    st.session_state.historique_notes = []

# Logo
st.markdown("""
    <div class="google-logo">
        <span class="blue">M</span><span class="red">o</span><span class="yellow">o</span><span class="blue">v</span><span class="green">l</span><span class="red">e</span>
    </div>
""", unsafe_allow_html=True)

# Centrer le contenu avec 3 colonnes (la colonne du milieu contient tout)
_, col_centre, _ = st.columns([1, 2, 1])

with col_centre:
    likes = st.text_input(
        "Vos films préférés (séparés par des virgules) :",
        placeholder="Ex: Inception, Interstellar..."
    )
    dislikes = st.text_input(
        "Films que vous n'aimez pas (optionnel) :",
        placeholder="Ex: Twilight..."
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        recherche_classique = st.button("🎯Selon vos goûts !", use_container_width=True)
    with col_btn2:
        recherche_surprise = st.button("🎲 Surprenez-moi !", use_container_width=True)

    # Recommandation classique basée sur les goûts
    if recherche_classique:
        if likes:
            with st.spinner("L'IA réfléchit à vos goûts..."):
                likes_list    = [f.strip() for f in likes.split(',') if f.strip()]
                dislikes_list = [f.strip() for f in dislikes.split(',') if f.strip()]
                
                res = recommander_films(likes_list, dislikes_list)
                
                # Gestion de l'erreur
                if "error" in res:
                    if res["error"] == "quota":
                        st.error("⚠️ L'IA est surchargée (limite de requêtes atteinte). Veuillez patienter 1 minute avant de réessayer !")
                    else:
                        st.error("⚠️ Une erreur inconnue est survenue avec l'IA. Consultez les logs.")
                else:
                    st.session_state.recos = res.get("recommandations", [])
                    st.session_state.historique_notes = []
        else:
            st.warning("Veuillez entrer au moins un film préféré !")

    # Mode surprise : on demande à l'IA de sortir de la zone de confort de l'utilisateur
    if recherche_surprise:
        if likes:
            with st.spinner("L'IA cherche une pépite inattendue..."):
                likes_list    = [f.strip() for f in likes.split(',') if f.strip()]
                dislikes_list = [f.strip() for f in dislikes.split(',') if f.strip()]
                
                res = recommander_films(likes_list, dislikes_list, mode="surprise")
                
                # Gestion de l'erreur
                if "error" in res:
                    if res["error"] == "quota":
                        st.error("⚠️ L'IA est surchargée (limite de requêtes atteinte). Veuillez patienter 1 minute avant de réessayer !")
                    else:
                        st.error("⚠️ Une erreur inconnue est survenue avec l'IA. Consultez les logs.")
                else:
                    st.session_state.recos = res.get("recommandations", [])
                    st.session_state.historique_notes = []
        else:
            st.warning("J'ai besoin de vos films préférés pour pouvoir vous surprendre !")

# Affichage des résultats en 3 colonnes
if st.session_state.recos:
    st.write("---")
    st.subheader("🍿 Suggestions pour vous")
    st.write("")

    cols = st.columns(3)
    notes_actuelles = {}

    for i, film in enumerate(st.session_state.recos):
        with cols[i]:
            # Affiche via TMDB
            url = get_movie_poster(film["titre"])
            st.image(url, use_container_width=True)

            st.markdown(f"### {film['titre']}")
            st.caption(f"📝 {film.get('resume', 'Résumé indisponible.')}")

            # Plateformes dispo en France (données JustWatch via TMDB)
            logos_plateformes = get_streaming_logos(film["titre"])
            if logos_plateformes:
                st.write("**Disponible sur :**")
                logo_cols = st.columns(len(logos_plateformes) + 5)
                for idx, logo in enumerate(logos_plateformes):
                    with logo_cols[idx]:
                        st.image(logo["url"], width=40)

            st.write("")

            # Clé unique par film pour éviter les conflits de widgets Streamlit
            deja_vu = st.checkbox("Je l'ai vu", key=f"vu_{film['titre']}_{i}")
            if deja_vu:
                note = st.slider("Votre note :", 0, 10, 5, key=f"note_{film['titre']}")
                notes_actuelles[film["titre"]] = note

    st.divider()

    # Relance l'IA en lui passant les notes comme contexte supplémentaire
    if st.button("🔄 Relancer l'IA en prenant en compte mes notes"):
        for titre, note in notes_actuelles.items():
            feedback = f"The user watched '{titre}' and rated it {note}/10."
            st.session_state.historique_notes.append(feedback)

        likes_list    = [f.strip() for f in likes.split(',') if f.strip()]
        dislikes_list = [f.strip() for f in dislikes.split(',') if f.strip()]
        nouveaux_likes = likes_list + st.session_state.historique_notes

        with st.spinner("L'IA affine votre profil selon vos notes..."):
            res = recommander_films(nouveaux_likes, dislikes_list)
            
            # Gestion de l'erreur
            if "error" in res:
                if res["error"] == "quota":
                    st.error("⚠️ L'IA est surchargée (limite de requêtes atteinte). Veuillez patienter 1 minute avant de réessayer !")
                else:
                    st.error("⚠️ Une erreur inconnue est survenue avec l'IA. Consultez les logs.")
            else:
                st.session_state.recos = res.get("recommandations", [])
                st.rerun()

# Historique des notes (panneau rétractable)
if st.session_state.historique_notes:
    with st.expander("📝 Voir la mémoire de l'IA (Historique)"):
        for h in st.session_state.historique_notes:
            st.write(f"- {h}")
