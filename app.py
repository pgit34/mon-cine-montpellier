import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Ciné Montpellier", page_icon="🎬")

st.title("🎬 Séances du jour")

# Lecture du fichier généré par le scraping automatique
file_path = "allocine_scraping_results.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    
    # Filtres
    liste_films = sorted(df["Film"].unique().tolist())
    selected_film = st.sidebar.selectbox("🔍 Choisir un film", ["Tous les films"] + liste_films)
    
    liste_cines = sorted(df["Cinéma"].unique().tolist())
    selected_cines = st.sidebar.multiselect("📍 Cinémas", liste_cines, default=liste_cines)

    # Filtrage
    df_filtered = df.copy()
    if selected_film != "Tous les films":
        df_filtered = df_filtered[df_filtered["Film"] == selected_film]
    if selected_cines:
        df_filtered = df_filtered[df_filtered["Cinéma"].isin(selected_cines)]

    st.dataframe(df_filtered.sort_values("Heure"), use_container_width=True, hide_index=True)
    
    # Date de dernière modif du fichier
    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%H:%M')
    st.caption(f"Dernière mise à jour automatique : {mod_time}")
else:
    st.error("Le fichier de données n'a pas encore été généré par le robot.")
