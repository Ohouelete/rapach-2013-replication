# Réplication et extension de Rapach, Strauss et Zhou (2013)

Les rendements passés du marché américain aident-ils à prévoir ceux des autres grands marchés boursiers ? Ce dépôt reproduit l'article de référence de Rapach, Strauss et Zhou (*Journal of Finance*, 2013), « International Stock Return Predictability: What Is the Role of the United States? », puis prolonge l'analyse sur la période récente.

Travail réalisé comme assistant de recherche du professeur Fu (Université Laval), mai à août 2026.

## Ce que fait le projet

1. **Base de données** (`python/build_master.py`) : reconstruction d'un panel mensuel de 23 pays à partir des exports Finaeon/GFD, du WTI (FRED) et des facteurs Fama-French. Le script associe les tickers aux pays, calcule les rendements, reporte les variables de niveau, calcule l'inflation et la croissance du PIB, puis valide le résultat contre l'ancien panel. Détail : [docs/methodologie_base_de_donnees.md](docs/methodologie_base_de_donnees.md) et [docs/description_des_variables.md](docs/description_des_variables.md).
2. **Statistiques descriptives**, calculées en Python et en Stata pour recouper les deux chaînes de calcul (`python/descriptive_stats.py`, `stata/00_stats_descriptives.do`).
3. **Analyses en échantillon**, pour 11 marchés développés : régressions prédictives sur le taux sans risque et le ratio dividende-prix, puis matrice de causalité de Granger par paires et score de « leadership », avec erreurs types robustes HC2.
4. **Analyses hors échantillon** : R² hors échantillon (R²OS) face à la moyenne historique et test de Clark-West, pour trois modèles (univarié, avec autocorrélation, macro) estimés pays par pays et en panel poolé.
5. **Deux périodes** : reproduction (1980:02–2010:12, `stata/01_reproduction_1980_2010.do`) et extension (2010:01–2024:12, `stata/02_extension_2010_2024.do`).

Le rapport complet se trouve dans [rapport/Rapach2013_reproduction_extension.pdf](rapport/Rapach2013_reproduction_extension.pdf).

## Principaux résultats

- **La reproduction confirme l'article.** Sur 1980–2010, les États-Unis et la Suède prédisent significativement les 10 autres marchés (score de leadership 10/10). Les États-Unis ont le coefficient moyen le plus élevé (0,199).
- **Le gain de prévision est réel hors échantillon.** Avec le modèle univarié, le rendement américain améliore la prévision par rapport à la moyenne historique : R²OS moyen de 1,92 %, positif pour 9 marchés sur 10.
- **Ajouter des variables n'aide pas.** Les modèles avec autocorrélation et macro font moins bien que le modèle univarié en estimation pays par pays. L'estimation poolée réduit nettement ce problème.
- **Le rôle des États-Unis disparaît sur 2010–2024.** Aucun pays n'a un score de leadership supérieur à zéro, et les performances hors échantillon s'effondrent en estimation pays par pays. Ces résultats sont à interpréter avec prudence à cause de la qualité de certaines séries récentes, comme l'explique le rapport.

## Exécuter le code

```bash
pip install pandas numpy openpyxl python-calamine
python python/build_master.py        # crée data/MasterFilePanel_rebuilt.xlsx
python python/descriptive_stats.py
```

Puis, dans Stata 17 ou 18, depuis la racine du dépôt : `do stata/01_reproduction_1980_2010.do` et `do stata/02_extension_2010_2024.do`.

> ⚠️ Les données Finaeon/GFD sont sous licence : elles ne sont pas incluses. Voir [data/README.md](data/README.md).

## Outils

Python (pandas, NumPy), Stata 17/18, LaTeX.
