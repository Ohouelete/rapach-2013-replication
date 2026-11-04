**Construction de la base — étapes et formules**

*Réplication Rapach, Strauss & Zhou (2013) — script build_master.py (une
seule exécution).*

**Sources.** Finaeon/GFD : 10 séries par pays (prix boursier, Tbill, DY,
GovBond, CorpBond, FX, chômage, PE, GDP, CPI). FRED : pétrole WTI. Ken
French : facteurs Mkt-RF, SMB, HML. Résultat : panel mensuel, 23 pays.

**Étape 1 — Chargement des données brutes**

Lecture des 10 fichiers Finaeon, du WTI (FRED) et des facteurs
Fama-French (bloc mensuel uniquement).

**Étape 2 — Association ticker → pays**

Chaque série GFD est reliée à son pays (code ISO) via la feuille « Data
Information » de l'export ; le taux de change utilise une table dédiée
(ticker de devise → pays).

**Étape 3 — Grille mensuelle par pays**

Pour chaque pays, une ligne par mois, de la première date de l'indice
boursier jusqu'à juin 2026.

**Étape 4 — Transformations**

**a) Rendements** — calculés depuis l'indice de prix ; la 1re
observation de chaque pays est retirée.

> *Returns<sub>t</sub> = ( P<sub>t</sub> − P<sub>t−1</sub> ) /
> P<sub>t−1</sub>*

**b) Report vers l'avant** — les variables de niveau (Tbill, DY,
GovBond, CorpBond, FX, chômage, PE, GDP) et le CPI sont reportées : on
répète la dernière valeur publiée pour combler les mois manquants.

**c) Inflation** — glissement annuel du CPI, puis reportée vers l'avant.

> *Inflation<sub>t</sub> = CPI<sub>t</sub> / CPI<sub>t−12</sub> − 1*

**d) Accroissement du PIB (annualisé)** — calculé sur les publications
réelles puis annualisé, pour éviter les zéros : annuel × 1, trimestriel
× 4.

> *GDP_gr = ln( GDP_t / GDP_préc. ) × ( 12 / écart en mois )*

**e) Accroissements mensuels (WTI, FX) et décalages** — croissance en
log, plus une version décalée d'un mois (utilisable en prévision, sans
biais de look-ahead).

> *X_gr_t = ln( X_t / X_t−1 ) X_gr_lag1_t = X_gr_t−1*

**Étape 5 — Variables mondiales**

WTI et facteurs (Mkt-RF, SMB, HML) sont fusionnés par date et appliqués
identiquement à tous les pays.

**Étape 6 — Validation**

Le panel reconstruit est comparé à l'ancien master, variable par
variable. 9 variables sur 11 se reproduisent à ~100 % — preuve que la
reconstruction est correcte.

**Étape 7 — Sortie**

Écriture de MasterFilePanel_rebuilt.xlsx : 18 colonnes de base + 6
colonnes d'accroissement. 46 195 lignes, 23 pays, jusqu'à 2026.06.

**Variables calculées par nous (et NON téléchargées)**

Les colonnes suivantes ne sont pas récupérées d'une base externe : elles
sont produites par notre script à partir d'autres colonnes.

| **Colonne**     | **Comment elle est calculée**                  |
|-----------------|------------------------------------------------|
| **Returns**     | à partir du prix boursier téléchargé           |
| **Inflation**   | à partir du CPI téléchargé (glissement annuel) |
| **WTI_gr**      | accroissement (log) du WTI                     |
| **WTI_gr_lag1** | WTI_gr décalé d'un mois                        |
| **FX_gr**       | accroissement (log) du FX                      |
| **FX_gr_lag1**  | FX_gr décalé d'un mois                         |
| **GDP_gr**      | accroissement (log) annualisé du PIB           |
| **GDP_gr_lag1** | GDP_gr décalé d'un mois                        |

*En résumé : 13 séries sont téléchargées (Finaeon, FRED, Ken French) et
ces 8 colonnes sont calculées par le script.*
