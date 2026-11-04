#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 descriptive_stats.py  —  Statistiques descriptives du panel (Rapach 2013)
================================================================================
 Calcule 8 statistiques (moyenne, écart-type, min, P25, médiane, max, Sharpe,
 autocorrélation d'ordre 1) pour les 11 variables spécifiques par pays, sur
 deux périodes :
     Période 1 : 1980.01 – 2010.12  (fenêtre Rapach originale)
     Période 2 : 1980.01 – 2026.06  (version étendue)

 Sorties (un classeur Excel, plusieurs onglets) :
     - "Poolé 1980-2010" / "Poolé 1980-2026" : tableau 11 × 8 (23 pays empilés)
     - "Par pays 1980-2010" / "Par pays 1980-2026" : détail pays par variable

 Conventions :
     - écart-type d'échantillon (ddof = 1)
     - Sharpe = moyenne / écart-type (MENSUEL ; annualisé = ×√12)
     - autocorrélation = corrélation d'ordre 1 calculée PAR PAYS puis moyennée
       (évite de relier la fin d'un pays au début du suivant)

 DÉPENDANCES : pandas, numpy, openpyxl
 UTILISATION : régler MASTER_FILE ci-dessous, puis  python descriptive_stats.py
================================================================================
"""

import numpy as np
import pandas as pd

# ------------------------------------------------------------------ CONFIG ----
MASTER_FILE = "data/MasterFilePanel_rebuilt.xlsx"
OUT_FILE    = "Stats_descriptives.xlsx"

VARIABLES = ["Returns", "Tbill", "DY", "GovBond", "Corpbond", "FX",
             "Unemployment", "PE", "GDP", "Inflation", "CPI"]

PERIODS = {
    "1980-2010": (198001, 201012),
    "1980-2026": (198001, 202606),
}

STAT_COLS = ["Moyenne", "Écart-type", "Min", "P25", "Médiane", "Max",
             "Sharpe (mens.)", "Autocorr(1)"]


# --------------------------------------------------------------- UTILITAIRES --
def in_period(df, lo, hi):
    ym = df["Year"] * 100 + df["Month"]
    return df[(ym >= lo) & (ym <= hi)]


def lag1_autocorr(series):
    """Autocorrélation d'ordre 1 d'une série (ordonnée), NaN si trop courte."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 3:
        return np.nan
    return s.autocorr(lag=1)


def pooled_stats(sub, var):
    """8 statistiques sur la variable, tous pays empilés."""
    x = pd.to_numeric(sub[var], errors="coerce").dropna()
    if x.empty:
        return {c: np.nan for c in STAT_COLS}
    mean, std = x.mean(), x.std(ddof=1)
    # autocorrélation : par pays puis moyenne
    acs = [lag1_autocorr(g.sort_values(["Year", "Month"])[var])
           for _, g in sub.groupby("Country")]
    acs = [a for a in acs if pd.notna(a)]
    return {
        "Moyenne": mean, "Écart-type": std,
        "Min": x.min(), "P25": x.quantile(0.25), "Médiane": x.median(), "Max": x.max(),
        "Sharpe (mens.)": mean / std if std else np.nan,
        "Autocorr(1)": np.mean(acs) if acs else np.nan,
    }


def per_country_stats(sub, var):
    """8 statistiques par pays pour une variable -> DataFrame (pays en lignes)."""
    rows = {}
    for iso, g in sub.groupby("Country"):
        x = pd.to_numeric(g[var], errors="coerce").dropna()
        if x.empty:
            continue
        mean, std = x.mean(), x.std(ddof=1)
        rows[iso] = {
            "Moyenne": mean, "Écart-type": std,
            "Min": x.min(), "P25": x.quantile(0.25), "Médiane": x.median(), "Max": x.max(),
            "Sharpe (mens.)": mean / std if std else np.nan,
            "Autocorr(1)": lag1_autocorr(g.sort_values(["Year", "Month"])[var]),
        }
    return pd.DataFrame(rows).T[STAT_COLS] if rows else pd.DataFrame(columns=STAT_COLS)


# ---------------------------------------------------------------------- MAIN --
def main():
    df = pd.read_excel(MASTER_FILE)
    print(f"Chargé: {df.shape[0]} lignes, {df['Country'].nunique()} pays")

    with pd.ExcelWriter(OUT_FILE, engine="openpyxl") as xl:
        for label, (lo, hi) in PERIODS.items():
            sub = in_period(df, lo, hi)

            # --- tableau poolé (11 x 8) ---
            pooled = pd.DataFrame(
                {v: pooled_stats(sub, v) for v in VARIABLES}
            ).T[STAT_COLS].round(4)
            pooled.index.name = "Variable"
            pooled.to_excel(xl, sheet_name=f"Poolé {label}")
            print(f"\n=== Poolé {label} ({in_period(df, lo, hi).shape[0]} lignes) ===")
            print(pooled.to_string())

            # --- détail par pays (empilé : variable puis pays) ---
            blocks = []
            for v in VARIABLES:
                pc = per_country_stats(sub, v).round(4)
                pc.insert(0, "Variable", v)
                pc.index.name = "Pays"
                blocks.append(pc.reset_index())
            per_country = pd.concat(blocks, ignore_index=True)
            per_country.to_excel(xl, sheet_name=f"Par pays {label}", index=False)

    print(f"\n✓ Écrit: {OUT_FILE}")


if __name__ == "__main__":
    main()
