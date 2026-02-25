import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

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

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."}

def main():
    all_data = []
    for url in START_URLS:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            cinema_elem = soup.select_one("div.header-theater-title")
            cinema_name = cinema_elem.get_text(strip=True).replace(" Montpellier", "").replace(" - IMAX", "") if cinema_elem else "Inconnu"

            for card in soup.select("div.entity-card"):
                titre = card.select_one("a.meta-title-link").get_text(strip=True)
                for version in card.select("div.showtimes-version"):
                    v_raw = version.select_one("div.text").get_text(strip=True) if version.select_one("div.text") else "VF"
                    langue = "VOST" if "VOST" in v_raw.upper() else "VF"
                    for horaire in version.select(".showtimes-hour-block"):
                        heure = horaire.get_text(strip=True)[:5]
                        if ":" in heure:
                            all_data.append({
                                "Heure": heure,
                                "Film": titre,
                                "Cinéma": cinema_name,
                                "Langue": langue
                            })
        except: continue

    df = pd.DataFrame(all_data)
    # --- SUPPRESSION DES DOUBLONS ---
    df = df.drop_duplicates(subset=["Heure", "Film", "Cinéma", "Langue"])
    df = df.sort_values("Heure")
    
    # Sauvegarde pour Streamlit
    df.to_csv("allocine_scraping_results.csv", index=False, encoding="utf-8")
    print(f"Mise à jour réussie : {len(df)} séances trouvées.")

if __name__ == "__main__":
    main()
