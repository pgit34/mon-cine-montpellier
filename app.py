import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Ciné Montpellier 7J", page_icon="🎬", layout="wide")

# Liste des cinémas (IDs Allociné)
THEATERS = {
    "Gaumont Comédie": "P0702",
    "Gaumont Multiplexe": "P0076",
    "CGR Lattes": "P7647",
    "Le Royal": "P0187",
    "Diagonal": "W3408"
}

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."}

# --- LOGIQUE DE SCRAPING ---
@st.cache_data(ttl=3600)
def get_seances_7_jours():
    all_data = []
    today = datetime.now()
    
    # On boucle sur les 7 prochains jours
    for i in range(7):
        date_target = today + timedelta(days=i)
        date_str = date_target.strftime("%Y-%m-%d")
        display_date = date_target.strftime("%A %d %b") # Ex: Lundi 25 Oct
        
        for cine_name, cine_id in THEATERS.items():
            # URL formatée pour la date spécifique
            url = f"https://www.allocine.fr/seance/salle_gen_csalle={cine_id}/?date={date_str}"
            
            response = requests.get(url, headers=headers)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for card in soup.select("div.entity-card"):
                titre = card.select_one("a.meta-title-link").get_text(strip=True)
                
                for version in card.select("div.showtimes-version"):
                    v_raw = version.select_one("div.text").get_text(strip=True) if version.select_one("div.text") else "VF"
                    langue = "VOST" if "VOST" in v_raw.upper() else "VF"
                    
                    for horaire in version.select("div.showtimes-hour-block"):
                        heure = horaire.get_text(strip=True)[:5]
                        all_data.append({
                            "Jour": display_date,
                            "Heure": heure,
                            "Film": titre,
                            "Cinéma": cine_name,
                            "Langue": langue,
                            "Sortie": date_str # Pour le tri technique
                        })
    
    return pd.DataFrame(all_data)

# --- INTERFACE ---
st.title("🎬 Mon Programme Ciné (7 jours)")

with st.spinner('Récupération des séances de la semaine...'):
    df_global = get_seances_7_jours()

# --- FILTRES DANS LA BARRE LATÉRALE ---
st.sidebar.header("Options de recherche")

# 1. Filtre par Jour
jours_disponibles = df_global["Jour"].unique()
selected_day = st.sidebar.selectbox("📅 Choisir le jour", jours_disponibles)

# 2. Recherche de Film (Auto-complétion)
films_dispo = sorted(df_global[df_global["Jour"] == selected_day]["Film"].unique())
selected_film = st.sidebar.selectbox("🔍 Chercher un film", ["Tous les films"] + films_dispo)

# 3. Filtre par Cinéma
cines_dispo = sorted(df_global["Cinéma"].unique())
selected_cines = st.sidebar.multiselect("📍 Cinémas", cines_dispo, default=cines_dispo)

# --- FILTRAGE DES DONNÉES ---
df_filtered = df_global[df_global["Jour"] == selected_day]

if selected_film != "Tous les films":
    df_filtered = df_filtered[df_filtered["Film"] == selected_film]

if selected_cines:
    df_filtered = df_filtered[df_filtered["Cinéma"].isin(selected_cines)]

# --- AFFICHAGE ---
if not df_filtered.empty:
    # On affiche un résumé sympa
    st.subheader(f"Séances pour le {selected_day}")
    
    # Mise en forme du tableau pour mobile
    st.dataframe(
        df_filtered[["Heure", "Film", "Cinéma", "Langue"]].sort_values("Heure"),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Aucune séance trouvée avec ces filtres.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Dernière mise à jour : {datetime.now().strftime('%H:%M')}")
