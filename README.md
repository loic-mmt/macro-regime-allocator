# macro-regime-allocator
Detect macro regimes (inflation/growth) and output simple portfolio allocations. Python + FRED.

Implémentation inspirée des travaux de Charles Gave : détection de régime macro
(Inflation ±, Croissance ±) et allocation indicielle simple.

## Installation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FRED_API_KEY="votre_cle"

## Usage
python MRPA.py --country US --start 1990-01
python regime_duration.py --country FR --start 2000-01

## Données
FRED (CPI YoY, PIB réel, taux directeur, chômage).

## Sorties
- Console (rich): niveaux d’inflation/croissance, régime courant
- Tableau d’allocation (% actions/or/obligations/cash)
- (Optionnel) graphiques matplotlib

## Avertissement
Projet éducatif. Pas un conseil d’investissement.
