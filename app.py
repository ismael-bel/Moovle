import streamlit as st
from services import recommander_films, get_movie_poster, get_streaming_logos

# Base configuration
st.set_page_config(page_title="Moovle", layout="wide")

# Custom CSS for Google-like styling
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

# Streamlit reloads the script on every action; session_state keeps data in memory
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

# Center content using 3 columns (the middle column contains everything)
_, col_centre, _ = st.columns([1, 2, 1])

with col_centre:
    likes = st.text_input(
        "Your favorite movies (separated by commas):",
        placeholder="E.g.: Inception, Interstellar..."
    )
    dislikes = st.text_input(
        "Movies you dislike (optional):",
        placeholder="E.g.: Twilight..."
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        recherche_classique = st.button("🎯 Based on your tastes!", use_container_width=True)
    with col_btn2:
        recherche_surprise = st.button("🎲 Surprise me!", use_container_width=True)

    # Classic recommendation based on tastes
    if recherche_classique:
        if likes:
            with st.spinner("AI is thinking about your tastes..."):
                likes_list    = [f.strip() for f in likes.split(',') if f.strip()]
                dislikes_list = [f.strip() for f in dislikes.split(',') if f.strip()]
                
                res = recommander_films(likes_list, dislikes_list)
                
                # Error handling
                if "error" in res:
                    if res["error"] == "quota":
                        st.error("⚠️ The AI is overloaded (request limit reached). Please wait 1 minute before trying again!")
                    else:
                        st.error("⚠️ An unknown error occurred with the AI. Please check the logs.")
                else:
                    st.session_state.recos = res.get("recommandations", [])
                    st.session_state.historique_notes = []
        else:
            st.warning("Please enter at least one favorite movie!")

    # Surprise mode: requesting AI to step out of the user's comfort zone
    if recherche_surprise:
        if likes:
            with st.spinner("AI is searching for an unexpected gem..."):
                likes_list    = [f.strip() for f in likes.split(',') if f.strip()]
                dislikes_list = [f.strip() for f in dislikes.split(',') if f.strip()]
                
                res = recommander_films(likes_list, dislikes_list, mode="surprise")
                
                # Error handling
                if "error" in res:
                    if res["error"] == "quota":
                        st.error("⚠️ The AI is overloaded (request limit reached). Please wait 1 minute before trying again!")
                    else:
                        st.error("⚠️ An unknown error occurred with the AI. Please check the logs.")
                else:
                    st.session_state.recos = res.get("recommandations", [])
                    st.session_state.historique_notes = []
        else:
            st.warning("I need your favorite movies to be able to surprise you!")

# Displaying results in 3 columns
if st.session_state.recos:
    st.write("---")
    st.subheader("🍿 Suggestions for you")
    st.write("")

    cols = st.columns(3)
    notes_actuelles = {}

    for i, film in enumerate(st.session_state.recos):
        with cols[i]:
            # Poster via TMDB
            url = get_movie_poster(film["titre"])
            st.image(url, use_container_width=True)

            st.markdown(f"### {film['titre']}")
            st.caption(f"📝 {film.get('resume', 'Summary unavailable.')}")

            # Platforms available in France (JustWatch data via TMDB)
            logos_plateformes = get_streaming_logos(film["titre"])
            if logos_plateformes:
                st.write("**Available on:**")
                logo_cols = st.columns(len(logos_plateformes) + 5)
                for idx, logo in enumerate(logos_plateformes):
                    with logo_cols[idx]:
                        st.image(logo["url"], width=40)

            st.write("")

            # Unique key per movie to avoid Streamlit widget conflicts
            deja_vu = st.checkbox("I've seen it", key=f"vu_{film['titre']}_{i}")
            if deja_vu:
                note = st.slider("Your rating:", 0, 10, 5, key=f"note_{film['titre']}")
                notes_actuelles[film["titre"]] = note

    st.divider()

    # Relaunch AI passing ratings as additional context
    if st.button("🔄 Relaunch AI taking my ratings into account"):
        for titre, note in notes_actuelles.items():
            feedback = f"The user watched '{titre}' and rated it {note}/10."
            st.session_state.historique_notes.append(feedback)

        likes_list    = [f.strip() for f in likes.split(',') if f.strip()]
        dislikes_list = [f.strip() for f in dislikes.split(',') if f.strip()]
        nouveaux_likes = likes_list + st.session_state.historique_notes

        with st.spinner("AI is refining your profile based on your ratings..."):
            res = recommander_films(nouveaux_likes, dislikes_list)
            
            # Error handling
            if "error" in res:
                if res["error"] == "quota":
                    st.error("⚠️ The AI is overloaded (request limit reached). Please wait 1 minute before trying again!")
                else:
                    st.error("⚠️ An unknown error occurred with the AI. Please check the logs.")
            else:
                st.session_state.recos = res.get("recommandations", [])
                st.rerun()

# Rating history (collapsible expander)
if st.session_state.historique_notes:
    with st.expander("📝 View AI Memory (History)"):
        for h in st.session_state.historique_notes:
            st.write(f"- {h}")
