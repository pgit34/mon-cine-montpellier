import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Ciné Montpellier", page_icon="🎬")

st.title("🎬 Séances du jour")

file_path = "allocine_scraping_results.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    
    # Nettoyage des noms de cinémas pour gagner de la place sur mobile
    df["Cinema"] = df["Cinema"].str.replace("Pathé", "P.").str.replace("Gaumont", "G.")

    # Filtres
    liste_films = sorted(df["Titre"].unique().tolist())
    selected_film = st.sidebar.selectbox("🔍 Choisir un film", ["Tous les films"] + liste_films)
    
    liste_cines = sorted(df["Cinema"].unique().tolist())
    selected_cines = st.sidebar.multiselect("📍 Cinémas", liste_cines, default=liste_cines)

    # Filtrage
    df_filtered = df.copy()
    if selected_film != "Tous les films":
        df_filtered = df_filtered[df_filtered["Titre"] == selected_film]
    if selected_cines:
        df_filtered = df_filtered[df_filtered["Cinema"].isin(selected_cines)]

    # Affichage simplifié
    st.dataframe(
        df_filtered[["Heure", "Titre", "Cinema", "Langue"]].sort_values("Heure"), 
        use_container_width=True, 
        hide_index=True
    )
    
    st.caption(f"Mise à jour auto à 6h du matin.")
else:
    st.info("Le robot prépare les données... Relancez le workflow sur GitHub.")
