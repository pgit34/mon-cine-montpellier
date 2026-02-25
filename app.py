import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Ciné Montpellier 7J", page_icon="🎬", layout="wide")

THEATERS = {
    "Gaumont Comédie": "P0702",
    "Gaumont Multiplexe": "P0076",
    "CGR Lattes": "P7647",
    "Le Royal": "P0187",
    "Diagonal": "W3408"
}

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

@st.cache_data(ttl=3600)
def get_seances_7_jours():
    all_data = []
    today = datetime.now()
    
    for i in range(7):
        date_target = today + timedelta(days=i)
        date_str = date_target.strftime("%Y-%m-%d")
        display_date = date_target.strftime("%A %d %b")
        
        for cine_name, cine_id in THEATERS.items():
            url = f"https://www.allocine.fr/seance/salle_gen_csalle={cine_id}/?date={date_str}"
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200: continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                cards = soup.select("div.entity-card")
                
                for card in cards:
                    titre_elem = card.select_one("a.meta-title-link")
                    if not titre_elem: continue
                    titre = titre_elem.get_text(strip=True)
                    
                    for version in card.select("div.showtimes-version"):
                        v_raw = version.select_one("div.text").get_text(strip=True) if version.select_one("div.text") else "VF"
                        langue = "VOST" if "VOST" in v_raw.upper() else "VF"
                        
                        for horaire in version.select(".showtimes-hour-block"):
                            # Extraction robuste de l'heure
                            h_val = horaire.get_text(strip=True)[:5]
                            if ":" in h_val:
                                all_data.append({
                                    "Jour": display_date,
                                    "Heure": h_val,
                                    "Film": titre,
                                    "Cinéma": cine_name,
                                    "Langue": langue
                                })
                time.sleep(0.1) # Petite pause pour la courtoisie
            except Exception as e:
                continue
    
    # Création du DataFrame avec colonnes par défaut si vide
    if not all_data:
        return pd.DataFrame(columns=["Jour", "Heure", "Film", "Cinéma", "Langue"])
    
    return pd.DataFrame(all_data)

# --- INTERFACE ---
st.title("🎬 Mon Programme Ciné (7 jours)")

with st.spinner('Chargement des séances...'):
    df_global = get_seances_7_jours()

if df_global.empty:
    st.error("Impossible de récupérer les données. Réessayez dans quelques instants.")
else:
    # --- FILTRES ---
    jours_dispo = df_global["Jour"].unique()
    selected_day = st.sidebar.selectbox("📅 Choisir le jour", jours_dispo)

    # Filtrage par jour d'abord pour l'auto-complétion des films
    df_day = df_global[df_global["Jour"] == selected_day]
    
    films_dispo = sorted(df_day["Film"].unique())
    selected_film = st.sidebar.selectbox("🔍 Chercher un film", ["Tous les films"] + films_dispo)

    selected_cines = st.sidebar.multiselect("📍 Cinémas", sorted(df_global["Cinéma"].unique()), default=list(THEATERS.keys()))

    # --- LOGIQUE DE FILTRE FINAL ---
    mask = (df_global["Jour"] == selected_day)
    if selected_film != "Tous THEATERS":
        if selected_film != "Tous les films":
            mask &= (df_global["Film"] == selected_film)
    if selected_cines:
        mask &= (df_global["Cinéma"].isin(selected_cines))

    filtered_df = df_global[mask].sort_values("Heure")

    # --- AFFICHAGE ---
    st.subheader(f"Séances du {selected_day}")
    if not filtered_df.empty:
        st.dataframe(filtered_df[["Heure", "Film", "Cinéma", "Langue"]], use_container_width=True, hide_index=True)
    else:
        st.info("Aucune séance trouvée pour ces critères.")

st.sidebar.caption(f"Dernière mise à jour : {datetime.now().strftime('%H:%M')}")
