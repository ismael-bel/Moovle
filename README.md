# 🎬 Moovle

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red) ![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-orange)

> 🔗 **[Try th app](https://moovle-76549270860.europe-west9.run.app)**




# What is Moovle?

Moovle is an ultra-personalized movie recommendation engine.
Forget generic suggestions: tell the app which movies you love (and the ones you don't), and our AI will handpick 3 hidden gems tailored just for you, complete with their official posters.

---

## Features

The application offers two distinct approaches:

**Classic Search:** Highly targeted recommendations based on your exact cinematic tastes.

**"Surprise Me!" Mode:** A "discovery" mode designed to push you out of your comfort zone (different genres, eras, or foreign cinema) while still respecting your emotional DNA.

**AI Explanations:** The AI generates a brief summary explaining why each movie was specifically recommended for you.

**Where to Watch:** The app identifies which streaming platforms currently host the movie in France (Netflix, Prime Video, Disney+, etc.).

**Smart Memory:** Already seen one of the suggestions? Rate it (from 0 to 10), and the AI will instantly refine its future recommendations.

---

## Stack

**Google Gemini 2.0 Flash** — Recommendation engine logic.   
**TMDB API** — Movie posters, cinematic metadata, and streaming provider data.  
**Streamlit** — Web interface.  
**Docker + GCP Cloud Run** — Deployment and hosting.  

---

## Project Structure
```
├── app.py              # Streamlit interface
├── services.py         # API integration (Gemini + TMDB)
├── requirements.txt    # Dependencies
└── .env                # API keys (not versioned)
```





















