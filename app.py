import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Ciné Montpellier", page_icon="🎬", layout="wide")

# Liste exhaustive de vos URLs
START_URLS = [
    "https://www.allocine.fr/seance/salle_gen_csalle=P0702.html",
    "https://www.allocine.fr/seance/salle_gen_csalle=P0076.html",
    "https://www.allocine.fr/seance/salle_gen_csalle=P7647.html",
    "https://www.allocine.fr/seance/salle_gen_csalle=P0187.html",
    "https://www.allocine.fr/seance/salle_gen_csalle=P7647.html#&page=2",
    "https://www.allocine.fr/seance/salle_gen_csalle=P0076.html#&page=2",
    "https://www.allocine.fr/seance/salle_gen_csalle=P0702.html#&page=2",
    "https://www.allocine.fr/seance/salle_gen_csalle=W3408.html",
    "https://www.allocine.fr/seance/salle_gen_csalle=P3408.html",
    "https://www.allocine.fr/seance/salle_gen_csalle=P0187.html#&page=2"
]

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

@st.cache_data(ttl=1800) # Mise à jour toutes les 30 minutes
def scrape_all_cinemas():
    all_data = []
    for url in START_URLS:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraction du nom du cinéma
            cinema_elem = soup.select_one("div.header-theater-title")
            cinema_name = cinema_elem.get_text(strip=True).replace(" Montpellier", "").replace(" - IMAX", "") if cinema_elem else "Inconnu"

            for card in soup.select("div.entity-card"):
                titre_elem = card.select_one("a.meta-title-link")
                if not titre_elem: continue
                titre = titre_elem.get_text(strip=True)

                for version in card.select("div.showtimes-version"):
                    v_raw = version.select_one("div.text").get_text(strip=True) if version.select_one("div.text") else "VF"
                    langue = "VOST" if "VOST" in v_raw.upper() else "VF"

                    for horaire in version.select(".showtimes-hour-block"):
                        h_val = horaire.get_text(strip=True)[:5]
                        if ":" in h_val:
                            all_data.append({
                                "Heure": h_val,
                                "Film": titre,
                                "Cinéma": cinema_name,
                                "Langue": langue
                            })
        except:
            continue
    
    return pd.DataFrame(all_data).drop_duplicates() if all_data else pd.DataFrame(columns=["Heure", "Film", "Cinéma", "Langue"])

# --- INTERFACE ---
st.title("🎬 Séances du jour à Montpellier")

with st.spinner('Chargement des séances...'):
    df = scrape_all_cinemas()

if df.empty:
    st.warning("Aucune séance trouvée ou erreur de connexion avec Allociné.")
else:
    # --- BARRE LATÉRALE (FILTRES) ---
    st.sidebar.header("Filtres")
    
    # 1. Recherche prédictive par film
    liste_films = sorted(df["Film"].unique().tolist())
    selected_film = st.sidebar.selectbox("🔍 Choisir un film", ["Tous les films"] + liste_films)

    # 2. Multi-sélection des cinémas
    liste_cines = sorted(df["Cinéma"].unique().tolist())
    selected_cines = st.sidebar.multiselect("📍 Cinémas", liste_cines, default=liste_cines)

    # --- FILTRAGE DES DONNÉES ---
    # On crée une copie pour ne pas corrompre le DataFrame original
    df_display = df.copy()
    
    if selected_film != "Tous les films":
        df_display = df_display[df_display["Film"] == selected_film]
    
    if selected_cines:
        df_display = df_display[df_display["Cinéma"].isin(selected_cines)]

    # Tri final par heure
    df_display = df_display.sort_values("Heure")

    # --- AFFICHAGE ---
    st.subheader(f"{len(df_display)} séances disponibles")
    
    if not df_display.empty:
        st.dataframe(
            df_display, 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("Aucun résultat pour ces filtres.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Mise à jour : {datetime.now().strftime('%H:%M')}")
