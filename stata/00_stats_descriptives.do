*==============================================================================
*  stats_descriptives.do  —  Statistiques descriptives du panel (Rapach 2013)
*==============================================================================
*  Calcule 8 statistiques (moyenne, écart-type, min, P25, médiane, max,
*  Sharpe, autocorrélation d'ordre 1) pour les 11 variables spécifiques
*  par pays, sur deux périodes :
*        Période 1 : 1980.01 – 2010.12   (fenêtre Rapach originale)
*        Période 2 : 1980.01 – 2026.06   (version étendue)
*
*  Entrée  : MasterFilePanel_rebuilt.xlsx  (la sortie de ton rebuild Python)
*  Sortie  : Stats_descriptives_stata.xlsx (tableau poolé, 2 périodes)
*
*  Conventions (identiques à la version Python) :
*     - écart-type d'échantillon
*     - Sharpe = moyenne / écart-type (MENSUEL ; annualisé = ×sqrt(12))
*     - autocorrélation d'ordre 1 : opérateur L. rendu conscient du panel
*       par xtset (pas de lien entre la fin d'un pays et le début du suivant)
*
*  UTILISATION : ajuste les 2 chemins ci-dessous, puis  do stats_descriptives.do
*==============================================================================

version 18
clear all
set more off

*------------------------------------------------------------------ CONFIG ----
* ⚠ Mets tes propres chemins (garde les barres obliques / , acceptées par Stata)
local infile  "data/MasterFilePanel_rebuilt.xlsx"
local outfile "data/Stats_descriptives_stata.xlsx"

*------------------------------------------------------------------ IMPORT ----
import excel using "`infile'", firstrow clear

* Panel : identifiant pays numérique + index temporel mensuel
encode Country, gen(cid)
gen t = ym(Year, Month)
format t %tm
xtset cid t

* Les 11 variables principales (spécifiques par pays)
local vars Returns Tbill DY GovBond Corpbond FX Unemployment PE GDP Inflation CPI

*------------------------------------- Stockage des résultats (postfile) -------
tempname pf
tempfile res
postfile `pf' str12 periode str14 variable ///
    double(moyenne ecarttype min p25 mediane max sharpe autocorr) using "`res'", replace

foreach per in 1 2 {
    if `per' == 1 {
        local lab  "1980-2010"
        local cond "t>=ym(1980,1) & t<=ym(2010,12)"
    }
    else {
        local lab  "1980-2026"
        local cond "t>=ym(1980,1) & t<=ym(2026,6)"
    }

    foreach v of local vars {
        * 6 stats de base via summarize, detail
        quietly summarize `v' if `cond', detail
        local m   = r(mean)
        local sd  = r(sd)
        local mn  = r(min)
        local p25 = r(p25)
        local p50 = r(p50)
        local mx  = r(max)

        * Sharpe mensuel
        local sh = cond(`sd' != 0 & `sd' < ., `m'/`sd', .)

        * Autocorrélation d'ordre 1 (L. conscient du panel grâce à xtset)
        capture correlate `v' L.`v' if `cond'
        if _rc == 0  local ac = r(rho)
        else         local ac = .

        post `pf' ("`lab'") ("`v'") (`m') (`sd') (`mn') (`p25') (`p50') (`mx') (`sh') (`ac')
    }
}
postclose `pf'

*------------------------------------------------- Affichage + export Excel ----
use "`res'", clear

* arrondi lisible
foreach var of varlist moyenne-autocorr {
    replace `var' = round(`var', 0.0001)
}

list, sepby(periode) noobs
export excel using "`outfile'", firstrow(variables) replace
display as result "✓ Écrit : `outfile'"

*==============================================================================
*  NOTES
*   - Pour l'annualisation du Sharpe : multiplier la colonne 'sharpe' par sqrt(12).
*   - Les lignes Inflation / CPI sont PROVISOIRES tant que le CPI de 11 pays
*     n'est pas homogénéisé (voir le rebuild : certains pays arrivent en TAUX).
*   - Pour un détail PAR PAYS, ajouter 'by cid:' ou remplacer le postfile par
*     une boucle sur les pays (me demander si besoin).
*==============================================================================
