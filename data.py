"""Génère un jeu de commandes e-commerce fictif, reproductible (graine fixe).

Environ 10 000 commandes sur 2025-2026, avec saisonnalité (pic en fin d’année)
et une croissance progressive, pour que le tableau de bord ait quelque chose à raconter.
"""
import numpy as np
import pandas as pd

GRAINE = 2026

REGIONS = {  # région : poids dans les ventes
    "Île-de-France": 0.28, "Auvergne-Rhône-Alpes": 0.13, "Provence-Alpes-Côte d’Azur": 0.10,
    "Occitanie": 0.09, "Nouvelle-Aquitaine": 0.09, "Hauts-de-France": 0.08,
    "Grand Est": 0.08, "Pays de la Loire": 0.06, "Bretagne": 0.05, "Normandie": 0.04,
}
CANAUX = {"Site": 0.55, "Marketplace": 0.30, "Boutique": 0.15}
CATALOGUE = {  # catégorie : [(produit, prix, coût), ...]
    "Informatique": [("Ordinateur portable 14\"", 799, 610), ("Écran 27\"", 249, 175),
                     ("Clavier mécanique", 89, 48), ("Souris sans fil", 35, 16)],
    "Audio": [("Casque à réduction de bruit", 199, 120), ("Enceinte Bluetooth", 79, 41),
              ("Écouteurs sans fil", 59, 27)],
    "Maison connectée": [("Ampoule connectée (x2)", 29, 12), ("Caméra de surveillance", 69, 38),
                         ("Thermostat connecté", 149, 92)],
    "Accessoires": [("Chargeur USB-C 65 W", 39, 15), ("Câble USB-C 2 m", 15, 4),
                    ("Housse ordinateur", 25, 9), ("Batterie externe", 45, 22)],
}
TAUX_RETOUR = {"Informatique": 0.06, "Audio": 0.09, "Maison connectée": 0.07, "Accessoires": 0.04}


def generer_commandes(n: int = 10_000, graine: int = GRAINE) -> pd.DataFrame:
    """Renvoie un DataFrame d’une ligne par commande."""
    rng = np.random.default_rng(graine)

    # Dates : croissance de ~25 % sur deux ans + pic en novembre-décembre
    jours = pd.date_range("2025-01-01", "2026-12-31", freq="D")
    t = np.arange(len(jours)) / len(jours)
    saison = 1 + 0.6 * np.isin(jours.month, [11, 12]) + 0.15 * np.isin(jours.month, [6, 7])
    poids = (1 + 0.25 * t) * saison
    dates = rng.choice(jours.values, size=n, p=poids / poids.sum())

    produits = [(cat, nom, prix, cout) for cat, liste in CATALOGUE.items() for nom, prix, cout in liste]
    # Les petits accessoires se vendent plus souvent que les ordinateurs
    freq = np.array([1 / np.sqrt(p[2]) for p in produits])
    idx = rng.choice(len(produits), size=n, p=freq / freq.sum())
    choisis = [produits[i] for i in idx]

    df = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "region": rng.choice(list(REGIONS), size=n, p=list(REGIONS.values())),
        "canal": rng.choice(list(CANAUX), size=n, p=list(CANAUX.values())),
        "categorie": [c[0] for c in choisis],
        "produit": [c[1] for c in choisis],
        "quantite": rng.choice([1, 1, 1, 1, 2, 2, 3], size=n),
        "prix": [c[2] for c in choisis],
        "cout": [c[3] for c in choisis],
        "client_id": rng.integers(1, 4_200, size=n),
    })
    df["prix"] = (df["prix"] * np.where(df["canal"] == "Marketplace", 0.95, 1.0)).round(2)
    df["statut"] = np.where(rng.random(n) < df["categorie"].map(TAUX_RETOUR), "Retournée", "Livrée")
    df.insert(0, "commande_id", [f"CMD-{i:05d}" for i in range(1, n + 1)])
    return df.sort_values("date").reset_index(drop=True)


if __name__ == "__main__":
    d = generer_commandes()
    print(d.head(), f"\n{len(d)} commandes du {d['date'].min():%d/%m/%Y} au {d['date'].max():%d/%m/%Y}")
