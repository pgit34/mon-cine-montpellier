import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Ciné Montpellier", page_icon="🎬", layout="wide")

# Liste des URLs (votre liste complète pour couvrir toutes les salles)
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

@st.cache_data(ttl=1800) # Mise à jour toutes les 30 min
def get_seances_du_jour():
    all_data = []
    
    for url in START_URLS:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Nom du Cinéma
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
    
    if not all_data:
        return pd.DataFrame(columns=["Heure", "Film", "Cinéma", "Langue"])
    
    return pd.DataFrame(all_data).drop_duplicates()

# --- INTERFACE ---
st.title("🎬 Séances du jour à Montpellier")

with st.spinner('Récupération des séances...'):
    df = get_seances_du_jour()

if df.empty:
    st.error("Aucune donnée disponible. Réessayez plus tard.")
else:
    # --- FILTRES BARRE LATÉRALE ---
    st.sidebar.header("Options")
    
    # 1. Recherche par film avec auto-complétion
    liste_films = sorted(df["Film"].unique())
    selected_film = st.sidebar.selectbox("🔍 Chercher un film", ["Tous les films"] + liste_films)

    # 2. Filtre par cinéma
    liste_cines = sorted(df["Cinéma"].unique())
    selected_cines = st.sidebar.multiselect("📍 Filtrer par cinéma", liste_cines, default=liste_cines)

    # --- LOGIQUE DE FILTRAGE ---
    mask = pd.Series([True] * len(df))
    
    if selected_film != "Tous les films":
        mask &= (df["Film"] == selected_film)
    
    if selected_cines:
        mask &= (df["Cinéma"].isin(selected_cines))

    filtered_df = df[mask].sort_values("Heure")

    # --- AFFICHAGE ---
    st.subheader(f"Trouvé : {len(filtered_df)} séance(s)")
    st.dataframe(
        filtered_df[["Heure", "Film", "Cinéma", "Langue"]], 
        use_container_width=True, 
        hide_index=True
    )

st.sidebar.markdown("---")
st.sidebar.caption(f"Dernière mise à jour : {datetime.now().strftime('%H:%M')}")
