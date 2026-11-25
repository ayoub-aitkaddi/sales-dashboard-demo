"""Vérifie les calculs du tableau de bord sur les données générées."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data import generer_commandes  # noqa: E402
from metrics import (ca_mensuel, filtrer, kpis, periode_precedente,  # noqa: E402
                     top_produits, variation)


@pytest.fixture(scope="module")
def df():
    return generer_commandes()


def test_volume_et_reproductibilite(df):
    assert len(df) == 10_000
    assert df.equals(generer_commandes())
    assert df["date"].min() >= pd.Timestamp("2025-01-01")
    assert df["date"].max() <= pd.Timestamp("2026-12-31")


def test_kpis_coherents(df):
    k = kpis(df)
    livrees = df[df["statut"] == "Livrée"]
    assert k["CA"] == pytest.approx((livrees["prix"] * livrees["quantite"]).sum())
    assert 0 < k["Marge"] < k["CA"]
    assert k["Panier moyen"] == pytest.approx(k["CA"] / len(livrees))
    assert 0.03 < k["Taux de retour"] < 0.12
    assert k["Clients"] == df["client_id"].nunique()


def test_ca_mensuel_somme_au_ca(df):
    assert ca_mensuel(df)["ca"].sum() == pytest.approx(kpis(df)["CA"])
    assert len(ca_mensuel(df)) == 24


def test_filtres_et_periode_precedente(df):
    sous = filtrer(df, "2026-01-01", "2026-03-31", regions=["Grand Est"], canaux=["Site"])
    assert set(sous["region"]) == {"Grand Est"} and set(sous["canal"]) == {"Site"}
    assert sous["date"].between("2026-01-01", "2026-03-31").all()
    debut, fin = periode_precedente("2026-01-11", "2026-01-20")
    assert (debut, fin) == (pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-10"))


def test_variation_et_top(df):
    assert variation(110, 100) == pytest.approx(10)
    assert variation(5, 0) is None
    top = top_produits(df)
    assert len(top) == 10 and top["ca"].is_monotonic_decreasing
