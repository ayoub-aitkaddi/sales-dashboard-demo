"""Calculs du tableau de bord, séparés de l’interface pour pouvoir être testés."""
import pandas as pd


def filtrer(df: pd.DataFrame, debut, fin, regions=None, canaux=None, categories=None) -> pd.DataFrame:
    """Filtre par période (bornes incluses) et, si fournies, par listes de valeurs."""
    masque = (df["date"] >= pd.Timestamp(debut)) & (df["date"] <= pd.Timestamp(fin))
    for col, valeurs in (("region", regions), ("canal", canaux), ("categorie", categories)):
        if valeurs:
            masque &= df[col].isin(valeurs)
    return df[masque]


def periode_precedente(debut, fin):
    """Période de même durée juste avant [debut, fin]."""
    debut, fin = pd.Timestamp(debut), pd.Timestamp(fin)
    duree = fin - debut
    return debut - duree - pd.Timedelta(days=1), debut - pd.Timedelta(days=1)


def kpis(df: pd.DataFrame) -> dict:
    """CA et marge sur les commandes livrées ; taux de retour sur toutes les commandes."""
    livrees = df[df["statut"] == "Livrée"]
    ca = float((livrees["prix"] * livrees["quantite"]).sum())
    marge = float(((livrees["prix"] - livrees["cout"]) * livrees["quantite"]).sum())
    return {
        "CA": ca,
        "Marge": marge,
        "Panier moyen": ca / len(livrees) if len(livrees) else 0.0,
        "Taux de retour": (df["statut"] == "Retournée").mean() if len(df) else 0.0,
        "Clients": int(df["client_id"].nunique()),
    }


def variation(actuel: float, precedent: float):
    """Variation relative en %, ou None si la période précédente est vide."""
    return None if not precedent else (actuel - precedent) / precedent * 100


def ca_lignes(df: pd.DataFrame) -> pd.DataFrame:
    """Commandes livrées avec une colonne CA et une colonne marge."""
    d = df[df["statut"] == "Livrée"].copy()
    d["ca"] = d["prix"] * d["quantite"]
    d["marge"] = (d["prix"] - d["cout"]) * d["quantite"]
    return d


def ca_mensuel(df: pd.DataFrame) -> pd.DataFrame:
    d = ca_lignes(df)
    return (d.groupby(d["date"].dt.to_period("M").dt.to_timestamp())["ca"].sum()
              .rename_axis("mois").reset_index())


def ca_par(df: pd.DataFrame, colonne: str) -> pd.DataFrame:
    return (ca_lignes(df).groupby(colonne, as_index=False)["ca"].sum()
              .sort_values("ca", ascending=False))


def top_produits(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    d = ca_lignes(df)
    return (d.groupby(["produit", "categorie"], as_index=False)
              .agg(quantite=("quantite", "sum"), ca=("ca", "sum"), marge=("marge", "sum"))
              .sort_values("ca", ascending=False).head(n).reset_index(drop=True))
