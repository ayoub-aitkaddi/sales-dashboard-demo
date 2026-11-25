"""Tableau de bord des ventes d’un e-commerce fictif (Streamlit).

Lancer en local : streamlit run app.py
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from data import generer_commandes
from metrics import (ca_mensuel, ca_par, filtrer, kpis, periode_precedente,
                     top_produits, variation)

st.set_page_config(page_title="Tableau de bord des ventes", page_icon="📊", layout="wide")

BLEU = "#1F3A5F"
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
GABARIT = dict(template="simple_white", margin=dict(l=10, r=10, t=40, b=10), height=340)


@st.cache_data
def charger() -> pd.DataFrame:
    return generer_commandes()


def euros(x: float) -> str:
    return f"{x:,.0f} €".replace(",", " ")


df = charger()

# --- Barre latérale : filtres ---------------------------------------------
st.sidebar.header("Filtres")
dmin, dmax = df["date"].min().date(), df["date"].max().date()
periode = st.sidebar.date_input("Période", value=(pd.Timestamp("2026-01-01").date(), dmax),
                                min_value=dmin, max_value=dmax, format="DD/MM/YYYY")
debut, fin = periode if isinstance(periode, tuple) and len(periode) == 2 else (dmin, dmax)
regions = st.sidebar.multiselect("Région", sorted(df["region"].unique()), placeholder="Toutes")
canaux = st.sidebar.multiselect("Canal", sorted(df["canal"].unique()), placeholder="Tous")
categories = st.sidebar.multiselect("Catégorie", sorted(df["categorie"].unique()), placeholder="Toutes")
st.sidebar.caption("Aucune sélection = tout inclure.")

courant = filtrer(df, debut, fin, regions, canaux, categories)
avant = filtrer(df, *periode_precedente(debut, fin), regions, canaux, categories)

# --- En-tête et KPI --------------------------------------------------------
st.title("Tableau de bord des ventes")
st.caption(f"Du {debut:%d/%m/%Y} au {fin:%d/%m/%Y} · {len(courant):,} commandes · "
           "variations par rapport à la période précédente de même durée".replace(",", " "))

if courant.empty:
    st.warning("Aucune commande pour ces filtres.")
    st.stop()

k, kp = kpis(courant), kpis(avant)
cols = st.columns(5)
for col, (nom, fmt) in zip(cols, [("CA", euros), ("Marge", euros), ("Panier moyen", euros),
                                  ("Taux de retour", lambda v: f"{v * 100:.1f} %".replace(".", ",")),
                                  ("Clients", lambda v: f"{v:,}".replace(",", " "))]):
    v = variation(k[nom], kp[nom])
    if nom == "Taux de retour":  # en points, et une baisse est une bonne nouvelle
        delta = None if not kp[nom] else f"{(k[nom] - kp[nom]) * 100:+.1f} pt".replace(".", ",")
        col.metric(nom, fmt(k[nom]), delta, delta_color="inverse")
    else:
        col.metric(nom, fmt(k[nom]), None if v is None else f"{v:+.1f} %".replace(".", ","))

# --- Graphiques ------------------------------------------------------------
gauche, droite = st.columns([3, 2])
with gauche:
    mensuel = ca_mensuel(courant)
    mensuel["mois"] = [f"{MOIS[d.month - 1]} {d:%y}" for d in mensuel["mois"]]
    fig = px.line(mensuel, x="mois", y="ca", markers=True,
                  labels={"mois": "", "ca": "CA (€)"}, title="Chiffre d’affaires mensuel")
    fig.update_traces(line_color=BLEU)
    st.plotly_chart(fig.update_layout(**GABARIT), width="stretch")
with droite:
    fig = px.bar(ca_par(courant, "categorie"), x="ca", y="categorie", orientation="h",
                 labels={"ca": "CA (€)", "categorie": ""}, title="CA par catégorie")
    fig.update_traces(marker_color=BLEU)
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig.update_layout(**GABARIT), width="stretch")

gauche, droite = st.columns([2, 3])
with gauche:
    fig = px.bar(ca_par(courant, "region"), x="ca", y="region", orientation="h",
                 labels={"ca": "CA (€)", "region": ""}, title="CA par région")
    fig.update_traces(marker_color=BLEU)
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig.update_layout(**{**GABARIT, "height": 420}), width="stretch")
with droite:
    st.markdown("**Top 10 produits**")
    top = top_produits(courant).rename(columns={"produit": "Produit", "categorie": "Catégorie",
                                                "quantite": "Unités", "ca": "CA", "marge": "Marge"})
    for c in ("CA", "Marge"):  # format français : espace fine comme séparateur de milliers
        top[c] = top[c].map(euros)
    st.dataframe(top, hide_index=True, width="stretch", height=380)

# --- Export ----------------------------------------------------------------
st.download_button("Télécharger les données filtrées (CSV)",
                   courant.to_csv(index=False, sep=";").encode("utf-8-sig"),
                   file_name=f"ventes_{debut:%Y%m%d}_{fin:%Y%m%d}.csv", mime="text/csv")
st.caption("Données fictives générées pour la démonstration · "
           "Réalisé par Ayoub Ait Kaddi, étudiant ingénieur à Télécom SudParis · Automatisation Python & data")
