#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_master.py — Reconstruit le panel maître (23 pays, mensuel) depuis les
données brutes Finaeon + WTI (FRED) + facteurs Fama-French, et le valide."""

import os
import re
import datetime as dt
from collections import defaultdict

import numpy as np
import pandas as pd
import openpyxl
from python_calamine import CalamineWorkbook

# ==============================================================================
# CONFIG — À AJUSTER SELON TON ARBORESCENCE
# ==============================================================================
# Chemins relatifs à la racine du dépôt (les données brutes ne sont pas incluses : voir README)
NEW_DIR    = os.path.join("data", "raw")
WTI_FILE   = os.path.join("data", "raw", "WTISPLC.xlsx")
FF_FILE    = os.path.join("data", "raw", "F-F_Research_Data_Factors.csv")
OLD_MASTER = os.path.join("data", "MatsterFilePanel.xlsx")   # optionnel : ancien panel pour validation
OUT_FILE   = os.path.join("data", "MasterFilePanel_rebuilt.xlsx")
END_YM     = 202606                                # dernier mois inclus (AAAAMM)

# Nom de fichier attendu pour chaque variable dans NEW_DIR
FILES = {
    "Returns": "RETURNS.xlsx", "Tbill": "TBILL.xlsx", "DY": "DY.xlsx",
    "GovBond": "GOVBOND.xlsx", "CorpBond": "CORPBOND.xlsx", "FX": "FX.xlsx",
    "Unemployment": "UNEMPLOYEMENT.xlsx", "PE": "PE.xlsx", "GDP": "GDP.xlsx",
    "CPI": "CPI.xlsx",
}

# Colonnes du master final (dans l'ordre)
COL_ORDER = ["Year", "Month", "Country", "Returns", "Tbill", "DY", "GovBond",
             "Corpbond", "FX", "Unemployment", "PE", "GDP", "Inflation", "CPI",
             "WTI", "Mkt-RF", "SMB", "HML"]

# Nom de pays (colonne "Country" des exports GFD) -> code ISO
NAME2ISO = {
    "Australia": "AUS", "Austria": "AUT", "Belgium": "BEL", "Canada": "CAN",
    "Switzerland": "CHE", "Germany": "DEU", "Denmark": "DNK", "Spain": "ESP",
    "Finland": "FIN", "France": "FRA", "United Kingdom": "GBR", "Hong Kong": "HKG",
    "Ireland": "IRL", "Israel": "ISR", "Italy": "ITA", "Japan": "JPN",
    "Netherlands": "NLD", "Norway": "NOR", "New Zealand": "NZL", "Portugal": "PRT",
    "Singapore": "SGP", "Sweden": "SWE", "United States": "USA",
}

# FX : la colonne "Country" des exports vaut toujours "United States", donc on
# mappe explicitement le ticker de taux de change -> pays.
FX_TICKER2ISO = {
    "USDAUD": "AUS", "USDATS": "AUT", "USDBEF": "BEL", "USDCAD": "CAN",
    "USDDKK": "DNK", "USDFIM": "FIN", "USDFRF": "FRA", "USDDEM": "DEU",
    "USDHKD": "HKG", "USDIEP": "IRL", "USDILS": "ISR", "USDITL": "ITA",
    "USDJPY": "JPN", "USDNLG": "NLD", "USDNZD": "NZL", "USDNOK": "NOR",
    "USDPTE": "PRT", "USDSGD": "SGP", "USDESP": "ESP", "USDSEK": "SWE",
    "USDCHF": "CHE", "USDGBP": "GBR",
}


# ==============================================================================
# UTILITAIRES
# ==============================================================================
def parse_date(d):
    """Convertit une date GFD (str MM/JJ/AAAA ou objet date) en datetime.date."""
    if isinstance(d, (dt.datetime, dt.date)):
        return dt.date(d.year, d.month, d.day)
    if isinstance(d, str):
        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                return dt.datetime.strptime(d.strip(), fmt).date()
            except ValueError:
                pass
    return None


def ym(d):
    """date -> entier AAAAMM."""
    return d.year * 100 + d.month


def monthly_range(start_ym, end_ym):
    """Liste des AAAAMM mensuels de start_ym à end_ym inclus."""
    y, m = divmod(start_ym, 100)
    out = []
    while y * 100 + m <= end_ym:
        out.append(y * 100 + m)
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def prev_year_same_month(yyyymm):
    """AAAAMM -> même mois, année précédente (pour le glissement annuel)."""
    return yyyymm - 100


def ffill_over_grid(valdict, grid):
    """Reporte vers l'avant les valeurs de valdict sur toute la grille mensuelle."""
    out, last = {}, None
    for g in grid:
        if g in valdict and valdict[g] is not None:
            last = valdict[g]
        out[g] = last
    return out


# ==============================================================================
# LECTURE DES EXPORTS
# ==============================================================================
def resolve_ticker_map(cwb, var):
    """Construit {ticker: ISO} à partir de la feuille 'Data Information'."""
    di = cwb.get_sheet_by_name("Data Information").to_python()
    hdr = di[0]
    ti = hdr.index("Ticker")
    ci = hdr.index("Country") if "Country" in hdr else None
    tmap = {}
    for r in di[1:]:
        t = r[ti]
        if not t:
            continue
        if var == "FX":                       # cas spécial FX
            iso = FX_TICKER2ISO.get(t)
        else:
            iso = NAME2ISO.get(r[ci]) if ci is not None else None
        if iso:
            tmap[t] = iso
    return tmap


def load_long(var, path):
    """Retourne un DataFrame [ISO, ym, val] pour une variable, dédupliqué au mois."""
    cwb = CalamineWorkbook.from_path(path)
    rows = cwb.get_sheet_by_name("Price Data").to_python()
    hdr = rows[0]
    ic, vc = hdr.index("Ticker"), hdr.index("Close")
    tmap = resolve_ticker_map(cwb, var)

    recs, unmapped = [], set()
    for r in rows[1:]:
        t, d, v = r[ic], parse_date(r[0]), r[vc]
        if t is None or d is None or v is None:
            continue
        iso = tmap.get(t)
        if iso is None:
            unmapped.add(t)
            continue
        recs.append((iso, ym(d), v))

    df = (pd.DataFrame(recs, columns=["ISO", "ym", "val"])
            .sort_values(["ISO", "ym"])
            .drop_duplicates(["ISO", "ym"], keep="last"))
    return df, unmapped


def load_wti(path):
    """WTI mensuel (FRED) -> {ym: prix}.

    L'export Excel de FRED contient un onglet 'README' puis un onglet de données
    ('Monthly'). On repère la feuille dont l'en-tête contient 'observation_date'.
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = None
    for name in wb.sheetnames:
        first = next(wb[name].iter_rows(values_only=True), (None,))
        if first and isinstance(first[0], str) and "observation_date" in first[0].lower():
            ws = wb[name]
            break
    if ws is None:                       # repli : dernière feuille (souvent les données)
        ws = wb[wb.sheetnames[-1]]

    wti = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        d = parse_date(r[0])
        if d and r[1] is not None:
            wti[ym(d)] = float(r[1])
    return wti


def load_ff(path):
    """Facteurs Fama-French mensuels -> {ym: {Mkt-RF, SMB, HML}} (bloc mensuel only)."""
    ff = {}
    pat = re.compile(r'^\s*(\d{6}),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)')
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = pat.match(line)
            if m:
                yyyymm = int(m.group(1))
                if 190000 < yyyymm < 210000:      # ignore le bloc annuel (ex. 1927)
                    ff[yyyymm] = {"Mkt-RF": float(m.group(2)),
                                  "SMB": float(m.group(3)),
                                  "HML": float(m.group(4))}
    return ff


# ==============================================================================
# CONSTRUCTION DU PANEL
# ==============================================================================
def build_panel(longs, wti, ff, end_ym):
    """Assemble le panel long à partir des séries chargées."""
    level_vars = ["Tbill", "DY", "GovBond", "CorpBond", "FX",
                  "Unemployment", "PE", "GDP"]

    # dictionnaires {ISO: {ym: val}}
    def to_map(v):
        return {iso: dict(zip(g.ym, g.val)) for iso, g in longs[v].groupby("ISO")}
    level_maps = {v: to_map(v) for v in level_vars}
    price_map  = to_map("Returns")
    cpi_map    = to_map("CPI")

    isos = sorted(set().union(*[set(longs[v]["ISO"]) for v in longs]))

    rows, anomalies = [], []
    for iso in isos:
        start = int(longs["Returns"].loc[longs["Returns"].ISO == iso, "ym"].min())
        grid = monthly_range(start, end_ym)

        # --- Returns : variation de l'indice de prix ---
        ret, prev = {}, None
        for g in grid:
            p = price_map[iso].get(g)
            if p is not None and prev not in (None, 0):
                ret[g] = p / prev - 1
            if p is not None:
                prev = p

        # --- variables de niveau : report avant ---
        lf = {v: ffill_over_grid(level_maps[v].get(iso, {}), grid) for v in level_vars}

        # --- CPI : reporté (comblé) + détection des ruptures ---
        # NB : Inflation et GDP_gr ne sont PLUS calculés ici. Ils sont dérivés
        # APRÈS l'assemblage, directement des colonnes du fichier (CPI, GDP),
        # pour garantir qu'aucun calcul n'utilise de donnée hors du fichier.
        cpi_native = cpi_map.get(iso, {})
        pubs = sorted(cpi_native)
        for a, b in zip(pubs, pubs[1:]):
            va, vb = cpi_native[a], cpi_native[b]
            if va and vb and abs(vb / va - 1) > 0.15:
                anomalies.append(("CPI rupture", iso,
                                  f"{a}->{b}: {va}->{vb} ({(vb/va-1)*100:+.0f}%)"))
        cpi_ff = ffill_over_grid(cpi_native, grid)   # CPI comblé (répétition) — demande prof

        for g in grid:
            y, mth = divmod(g, 100)
            rows.append({
                "Year": y, "Month": mth, "Country": iso,
                "Returns": ret.get(g),
                "Tbill": lf["Tbill"][g], "DY": lf["DY"][g], "GovBond": lf["GovBond"][g],
                "Corpbond": lf["CorpBond"][g], "FX": lf["FX"][g],
                "Unemployment": lf["Unemployment"][g], "PE": lf["PE"][g], "GDP": lf["GDP"][g],
                "CPI": cpi_ff[g],
                "WTI": wti.get(g),
                "Mkt-RF": ff.get(g, {}).get("Mkt-RF"),
                "SMB": ff.get(g, {}).get("SMB"), "HML": ff.get(g, {}).get("HML"),
            })
    panel = pd.DataFrame(rows).sort_values(["Country", "Year", "Month"]).reset_index(drop=True)

    # ------------------------------------------------------------------
    # Colonnes DÉRIVÉES — calculées UNIQUEMENT à partir des colonnes du
    # fichier (par pays). Aucun recours à des données hors du panel.
    # ------------------------------------------------------------------
    # Inflation = glissement annuel du CPI visible : CPI_t / CPI_{t-12} - 1
    panel["Inflation"] = panel.groupby("Country")["CPI"].transform(
        lambda s: pd.to_numeric(s, errors="coerce") /
                  pd.to_numeric(s, errors="coerce").shift(12) - 1)
    # GDP_gr = accroissement annualisé, calculé sur les CHANGEMENTS de la colonne GDP
    panel["GDP_gr"] = panel.groupby("Country", group_keys=False).apply(_gdp_growth_from_column)
    return panel, anomalies, isos


def _gdp_growth_from_column(sub):
    """Accroissement annualisé du PIB à partir de la SEULE colonne GDP du fichier.
    Croissance calculée entre deux valeurs distinctes consécutives (les publications),
    annualisée × (12 / écart en mois), puis reportée. Aucune donnée hors fichier."""
    vals = pd.to_numeric(sub["GDP"], errors="coerce").values
    ymv = (sub["Year"] * 100 + sub["Month"]).values
    out = np.full(len(sub), np.nan)
    last_v = last_y = None
    for i in range(len(vals)):
        v = vals[i]
        if np.isnan(v):
            continue
        if last_v is None:
            last_v, last_y = v, ymv[i]
        elif v != last_v:
            gap = (ymv[i] // 100 - last_y // 100) * 12 + (ymv[i] % 100 - last_y % 100)
            if last_v > 0 and v > 0 and gap > 0:
                out[i] = np.log(v / last_v) * (12.0 / gap)
            last_v, last_y = v, ymv[i]
    return pd.Series(out, index=sub.index).ffill()


# ==============================================================================
# ACCROISSEMENTS (log) ET DÉCALAGES
# ==============================================================================
def add_growth_and_lags(panel, variables=("WTI", "FX", "GDP")):
    """Ajoute, par pays : X_gr = log(X_t / X_{t-1})  et  X_gr_lag1 = X_gr décalé d'un mois.

    - Calcul PAR PAYS (on ne mélange pas la fin d'un pays avec le début du suivant).
    - X_gr    : taux de croissance logarithmique du mois t (formule de la prof).
    - X_gr_lag1 : le même, décalé d'une période -> utilisable en prévision (pas de look-ahead).
    """
    panel = panel.sort_values(["Country", "Year", "Month"]).copy()
    for v in variables:
        s = pd.to_numeric(panel[v], errors="coerce")
        # log(X_t / X_{t-1}) par pays ; ratio <= 0 -> NaN (log non défini)
        def _logret(x):
            r = x / x.shift(1)
            return np.log(r.where(r > 0))
        panel[f"{v}_gr"] = s.groupby(panel["Country"]).transform(_logret)
        panel[f"{v}_gr_lag1"] = panel.groupby("Country")[f"{v}_gr"].shift(1)
    return panel


# ==============================================================================
# DIAGNOSTICS
# ==============================================================================
def classify_cpi(longs):
    """Signale les pays dont le CPI est déjà un TAUX (médiane < 10) et non un niveau."""
    med = longs["CPI"].groupby("ISO")["val"].apply(lambda s: np.median(np.abs(s)))
    rates  = sorted(med[med < 10].index)
    levels = sorted(med[med >= 10].index)
    return levels, rates


def validate(new, old_path):
    """Compare le panel reconstruit à l'ancien master, variable par variable."""
    wb = openpyxl.load_workbook(old_path, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    it = ws.iter_rows(values_only=True)
    h = list(next(it))
    ix = {k: i for i, k in enumerate(h)}
    keep = ["Returns", "Tbill", "DY", "GovBond", "Corpbond", "FX",
            "Unemployment", "PE", "GDP", "Inflation", "CPI"]
    recs = []
    for r in it:
        c = r[ix["Country"]]
        if c in (None, "Non trouvé"):
            continue
        recs.append({"Year": r[ix["Year"]], "Month": r[ix["Month"]], "Country": c,
                     **{v: r[ix[v]] for v in keep}})
    old = pd.DataFrame(recs)
    merged = new.merge(old, on=["Year", "Month", "Country"], suffixes=("_new", "_old"))

    print(f"\nValidation ({len(merged)} lignes communes)")
    print(f"{'Variable':13}{'n':>8}{'% match':>10}{'corr':>8}{'max|Δ|':>12}")
    for v in keep:
        a = pd.to_numeric(merged[f"{v}_new"], errors="coerce")
        b = pd.to_numeric(merged[f"{v}_old"], errors="coerce")
        ok = a.notna() & b.notna()
        n = int(ok.sum())
        if n == 0:
            print(f"{v:13}{0:>8}")
            continue
        diff = (a[ok] - b[ok]).abs()
        match = (diff <= 1e-4).mean() * 100
        corr = np.corrcoef(a[ok], b[ok])[0, 1] if n > 1 else float("nan")
        print(f"{v:13}{n:>8}{match:>9.1f}%{corr:>8.3f}{diff.max():>12.4g}")


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    print("Chargement des 10 variables Finaeon...")
    longs = {}
    for v, fn in FILES.items():
        df, unmapped = load_long(v, os.path.join(NEW_DIR, fn))
        longs[v] = df
        flag = f"  ⚠ non mappés: {sorted(unmapped)}" if unmapped else ""
        print(f"  {v:13} {df['ISO'].nunique():>2} pays, dernier {int(df['ym'].max())}{flag}")

    # Diagnostic CPI niveaux vs taux
    levels, rates = classify_cpi(longs)
    print(f"\nCPI  —  NIVEAUX ({len(levels)}): {levels}")
    if rates:
        print(f"CPI  —  ⚠ DÉJÀ DES TAUX ({len(rates)}): {rates}")
        print("     (glissement annuel non valable pour ces pays -> standardiser les tickers)")

    wti = load_wti(WTI_FILE)
    ff  = load_ff(FF_FILE)
    print(f"\nWTI: {len(wti)} mois (dernier {max(wti)})   FF: {len(ff)} mois (dernier {max(ff)})")

    panel, anomalies, isos = build_panel(longs, wti, ff, END_YM)

    # Accroissements mensuels (log) + décalés, pour WTI et FX
    # (GDP_gr est déjà calculé dans build_panel, en version ANNUALISÉE)
    panel = add_growth_and_lags(panel, variables=("WTI", "FX"))
    panel = panel.sort_values(["Country", "Year", "Month"])
    panel["GDP_gr_lag1"] = panel.groupby("Country")["GDP_gr"].shift(1)
    growth_cols = ["WTI_gr", "WTI_gr_lag1", "FX_gr", "FX_gr_lag1", "GDP_gr", "GDP_gr_lag1"]
    panel = panel[COL_ORDER + growth_cols].sort_values(["Country", "Year", "Month"])
    print(f"\nPanel reconstruit: {panel.shape[0]} lignes, {len(isos)} pays, "
          f"jusqu'à {END_YM}")
    print(f"Colonnes d'accroissement ajoutées: {growth_cols}")

    if anomalies:
        print(f"\n{len(anomalies)} ruptures CPI détectées (échantillon):")
        for a in anomalies[:8]:
            print(f"   {a[1]}  {a[2]}")

    if OLD_MASTER and os.path.exists(OLD_MASTER):
        validate(panel, OLD_MASTER)

    panel.to_excel(OUT_FILE, index=False)
    print(f"\n✓ Écrit: {OUT_FILE}")


if __name__ == "__main__":
    main()
