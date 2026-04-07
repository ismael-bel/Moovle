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

# Session state initialization
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

# Main interface layout
_, col_centre, _ = st.columns([1, 2, 1])

with col_centre:
    likes = st.text_input(
        "Your favorite movies (comma separated):",
        placeholder="e.g., Inception, Interstellar, The Dark Knight..."
    )
    dislikes = st.text_input(
        "Movies you dislike (optional):",
        placeholder="e.g., Twilight, Cats..."
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        recherche_classique = st.button("🎯 Match my taste!", use_container_width=True)
    with col_btn2:
        recherche_surprise = st.button("🎲 Surprise me!", use_container_width=True)

    # Logic for Classic Recommendation
    if recherche_classique:
        if likes:
            with st.spinner("AI is analyzing your preferences..."):
                likes_list    = [f.strip() for f in likes.split(',') if f.strip()]
                dislikes_list = [f.strip() for f in dislikes.split(',') if f.strip()]
                
                res = recommander_films(likes_list, dislikes_list)
                
                if "error" in res:
                    if res["error"] == "quota":
                        st.error("⚠️ AI is overloaded (rate limit reached). Please wait a minute and try again!")
                    else:
                        st.error("⚠️ An unknown error occurred. Please check the system logs.")
                else:
                    st.session_state.recos = res.get("recommandations", [])
                    st.session_state.historique_notes = []
        else:
            st.warning("Please enter at least one movie you like!")

    # Logic for Surprise Mode
    if recherche_surprise:
        if likes:
            with st.spinner("AI is looking for an unexpected hidden gem..."):
                likes_list    = [f.strip() for f in likes.split(',') if f.strip()]
                dislikes_list = [f.strip() for f in dislikes.split(',') if f.strip()]
                
                res = recommander_films(likes_list, dislikes_list, mode="surprise")
                
                if "error" in res:
                    if res["error"] == "quota":
                        st.error("⚠️ AI is overloaded. Please wait a minute!")
                    else:
                        st.error("⚠️ An error occurred. Please check the logs.")
                else:
                    st.session_state.recos = res.get("recommandations", [])
                    st.session_state.historique_notes = []
        else:
            st.warning("I need your favorites to find a good surprise for you!")

# Display Results
if st.session_state.recos:
    st.write("---")
    st.subheader("🍿 Handpicked for you")
    st.write("")

    cols = st.columns(3)
    notes_actuelles = {}

    for i, film in enumerate(st.session_state.recos):
        with cols[i]:
            # Fetch poster
            url = get_movie_poster(film["titre"])
            st.image(url, use_container_width=True)

            st.markdown(f"### {film['titre']}")
            st.caption(f"📝 {film.get('resume', 'No summary available.')}")

            # Streaming availability
            logos_plateformes = get_streaming_logos(film["titre"])
            if logos_plateformes:
                st.write("**Watch on:**")
                logo_cols = st.columns(len(logos_plateformes) + 5)
                for idx, logo in enumerate(logos_plateformes):
                    with logo_cols[idx]:
                        st.image(logo["url"], width=40)

            st.write("")

            # User feedback widgets
            deja_vu = st.checkbox("Seen it", key=f"vu_{film['titre']}_{i}")
            if deja_vu:
                note = st.slider("Your rating:", 0, 10, 5, key=f"note_{film['titre']}")
                notes_actuelles[film["titre"]] = note

    st.divider()

    # Relaunch with ratings context
    if st.button("🔄 Refine recommendations based on my ratings"):
        for titre, note in notes_actuelles.items():
            feedback = f"The user watched '{titre}' and rated it {note}/10."
            st.session_state.historique_notes.append(feedback)

        likes_list    = [f.strip() for f in likes.split(',') if f.strip()]
        dislikes_list = [f.strip() for f in dislikes.split(',') if f.strip()]
        nouveaux_likes = likes_list + st.session_state.historique_notes

        with st.spinner("Refining your profile..."):
            res = recommander_films(nouveaux_likes, dislikes_list)
            
            if "error" in res:
                st.error("⚠️ Could not refresh. Please try again later.")
            else:
                st.session_state.recos = res.get("recommandations", [])
                st.rerun()

# History Expander
if st.session_state.historique_notes:
    with st.expander("📝 View AI Context (History)"):
        for h in st.session_state.historique_notes:
            st.write(f"- {h}")
