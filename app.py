import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Ciné Montpellier", page_icon="🎬", layout="wide")

# --- FONCTIONS DE SCRAPING (VOTRE CODE) ---
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."}

@st.cache_data(ttl=3600)  # Mise en cache pendant 1h pour éviter de bloquer votre IP
def get_all_seances():
    urls = [
        "https://www.allocine.fr/seance/salle_gen_csalle=P0702.html",
        "https://www.allocine.fr/seance/salle_gen_csalle=P0076.html",
        "https://www.allocine.fr/seance/salle_gen_csalle=P7647.html",
        "https://www.allocine.fr/seance/salle_gen_csalle=P0187.html",
        "https://www.allocine.fr/seance/salle_gen_csalle=W3408.html"
    ]
    
    all_data = []
    for url in urls:
        response = requests.get(url, headers=headers)
        if response.status_code != 200: continue
        
        soup = BeautifulSoup(response.content, 'html.parser')
        cinema_elem = soup.select_one("div.header-theater-title")
        cinema_name = cinema_elem.get_text(strip=True).replace(" Montpellier", "").replace(" - IMAX", "") if cinema_elem else "Inconnu"

        for seance in soup.select("div.entity-card"):
            titre = seance.select_one("a.meta-title-link").get_text(strip=True)
            for version in seance.select("div.showtimes-version"):
                v_raw = version.select_one("div.text").get_text(strip=True) if version.select_one("div.text") else "N/A"
                # Nettoyage rapide de la langue
                langue = v_raw[3:] if len(v_raw) > 3 else v_raw
                if "-" in langue: langue = langue.split("-")[-1].strip()

                for horaire in version.select("div.showtimes-hour-block"):
                    heure = horaire.get_text(strip=True)[:5] # Format HH:MM
                    all_data.append({
                        "Heure": heure,
                        "Film": titre,
                        "Cinéma": cinema_name,
                        "Langue": langue
                    })
    
    df = pd.DataFrame(all_data)
    return df.sort_values("Heure")

# --- INTERFACE UTILISATEUR ---
st.title("🎬 Séances Ciné Montpellier")

with st.spinner('Mise à jour des séances...'):
    df = get_all_seances()

# --- FILTRES ---
col1, col2 = st.columns(2)
with col1:
    search_film = st.text_input("🔍 Rechercher un film", "")
with col2:
    selected_cine = st.multiselect("📍 Filtrer par cinéma", options=sorted(df["Cinéma"].unique()))

# Application des filtres
mask = df["Film"].str.contains(search_film, case=False)
if selected_cine:
    mask = mask & df["Cinéma"].isin(selected_cine)

filtered_df = df[mask]

# --- AFFICHAGE ---
if not filtered_df.empty:
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
else:
    st.warning("Aucune séance ne correspond à votre recherche.")

st.caption(f"Dernière mise à jour : {datetime.now().strftime('%H:%M')}")
