"""
MRPA – Macro-Regime Portfolio Allocator
======================================

Analyse la conjoncture (inflation & croissance) pour les États-Unis et la France,
puis propose une allocation d’actifs à la manière des travaux de Charles Gave.

Fonctionnement
--------------
1. Télécharge les séries macro via FRED :
   • CPI YoY, PIB réel, taux directeur, chômage  
   • Codes définis dans le dict SERIES (US, FR ; EZ en cours de dev)  
2. Calcule :
   • niveaux d’inflation & croissance (levels 0-5)  
   • position relative dans chaque niveau (0-100 %)  
   • régime macro (Inflation +/– Croissance)  
3. Affiche un tableau « dashboard » coloré (bibliothèque *rich*) et
   une recommandation d’allocation (Actions, Obligations, Or, Cash).

Dépendances
-----------
pandas_datareader · numpy · rich

Installation rapide :
    pip install pandas_datareader numpy rich

Usage
-----
    python MRPA.py [REGION] [YYYY-MM-DD]

Exemples :
    python MRPA.py US 2023-10-01   # marché américain
    python MRPA.py FR              # marché français, start par défaut

Limites connues
---------------
• Zone euro (EZ) : CPI et PIB OK mais les autres séries sont en validation.  
• Pas de gestion des devises ni des effets de couverture FX.  
• Aucune garantie de performance financière – outil pédagogique.

Auteur : Loïc (2025)
"""


import pandas_datareader as pdr
from datetime import datetime
from math import tanh
import numpy as np

from rich.console import Console
from rich.table  import Table
from rich.panel  import Panel

SERIES = {
    "US": {
        "cpi": "CPIAUCNS",
        "gdp": "GDP",
        "policy": "FEDFUNDS",
        "unemp": "UNRATE",
    },
    "EU": {
        "cpi": "CP0000EZ19M086NEST",
        "gdp": "CLVMNACSCAB1GQEA19",
        "policy": "ECBMRRFR",
        "unemp": "LRHUTTTTEZM156S",
    },
    "FR": {
        "cpi": "FRACPIALLMINMEI",
        "gdp": "CLVMNACSCAB1GQFR",
        "policy": "ECBMRRFR",          # taux BCE – même pour la France
        "unemp": "LRHUTTTTFRM156S",
    },
    "DE": {   # Germany
        "cpi": "DEUCPIALLMINMEI",
        "gdp": "CLVMNACSCAB1GQDE",
        "policy": "ECBMRRFR",          # ECB main refi rate applies
        "unemp": "LRHUTTTTDEM156S",
    },
    "IT": {   # Italy
        "cpi": "ITACPIALLMINMEI",
        "gdp": "CLVMNACSCAB1GQIT",
        "policy": "ECBMRRFR",
        "unemp": "LRHUTTTTITM156S",
    },
    "GR": {   # Greece
        "cpi": "GRCPIALLMINMEI",
        "gdp": "CLVMNACSCAB1GQGR",
        "policy": "ECBMRRFR",
        "unemp": "LRHUTTTTGRM156S",
    },
    "CH": {   # Switzerland
        "cpi": "CHECPIALLMINMEI",
        "gdp": "CLVMNACSCAB1GQCH",
        "policy": "IR3TIB01CHM156N",    # 3‑month Swiss interbank rate
        "unemp": "LRHUTTTTCHM156S",
    },
    "JP": {   # Japan
        "cpi": "JPNCPIALLMINMEI",
        "gdp": "CLVMNACSCAB1GQJP",
        "policy": "IR3TIB01JPM156N",    # 3‑month Tokyo interbank rate
        "unemp": "LRHUTTTTJPM156S",
    },
}

def get_macro_data(region="FR", start=datetime(2023, 10, 1)):
    codes = SERIES[region]
    end = datetime.now()

    cpi  = pdr.get_data_fred(codes["cpi"],  start, end)
    if cpi.empty:
        raise ValueError(f"Data retrieval failed for CPI in {region}. Please check the data source or the date range.")
    gdp  = pdr.get_data_fred(codes["gdp"],  start, end)
    if gdp.empty:
        raise ValueError(f"Data retrieval failed for GDP in {region}. Please check the data source or the date range.")
    pol  = pdr.get_data_fred(codes["policy"], start, end)
    if pol.empty:
        raise ValueError(f"Data retrieval failed for Policy Rate in {region}. Please check the data source or the date range.")
    unrt = pdr.get_data_fred(codes["unemp"], start, end)
    if unrt.empty:
        raise ValueError(f"Data retrieval failed for Unemployment Rate in {region}. Please check the data source or the date range.")

    print()
    return cpi, gdp, pol, unrt


def data_optimization(cpi, gdp, pol, unrt):
    latest_inflation = ((cpi.iloc[-1].item() / cpi.iloc[-13].item()) - 1) * 100
    latest_gdp = ((gdp.iloc[-1].item() / gdp.iloc[-5].item()) - 1) * 100
    pol_mean = pol.rolling(3).mean()
    unrt_mean = unrt.rolling(3).mean()

    z_unrate = (unrt_mean.iloc[-1] - unrt_mean.mean()) / unrt_mean.std()
    z_fed = (pol_mean.iloc[-1] - pol_mean.mean()) / pol_mean.std()

    inflation_pressure = z_fed
    growth_pressure = -z_unrate

    inflation_adj = np.tanh(inflation_pressure)
    growth_adj = np.tanh(growth_pressure)

    return latest_inflation, latest_gdp, pol_mean, unrt_mean, z_unrate, z_fed, inflation_adj, growth_adj


def analyze_inflation_data(latest_inflation):
    inflation_level = 0
    print("Inflation Analysis:")

    if latest_inflation < 0:
        inflation_level += 0
        print("Risque déflationniste")
    elif 0 < latest_inflation < 1:
        inflation_level += 1
        print("Très faible dynamique des prix")
    elif 1 < latest_inflation < 2.5:
        inflation_level += 2
        print("Dynamique des prix faible")
    elif 2.5 < latest_inflation < 3.5:
        inflation_level += 3
        print("Dynamique des prix modérée")
    elif 3.5 < latest_inflation < 4.5:
        inflation_level += 4
        print("Dynamique des prix forte")
    else:
        inflation_level += 5
        print("Risque d'hyperinflation")

    print()
    return inflation_level


def analyze_growth_data(latest_gdp):
    growth_level = 0
    print("Growth Analysis:")

    if latest_gdp < -2:
        growth_level += 0
        print("Risque de récession")
    elif -2 <= latest_gdp < 0:
        growth_level += 1
        print("Croissance négative")
    elif 0 <= latest_gdp < 1:
        growth_level += 2
        print("Croissance faible")
    elif 1 <= latest_gdp < 2.5:
        growth_level += 3
        print("Croissance modérée")
    elif 2.5 <= latest_gdp < 4:
        growth_level += 4
        print("Croissance forte")
    else:
        growth_level += 5
        print("Risque de surchauffe économique")

    print()
    return growth_level


def unemployment_score(unemployment_mean):
    if unemployment_mean < 3.5:
        return 1
    elif 3.5 <= unemployment_mean < 5:
        return 0
    elif 5 <= unemployment_mean < 7:
        return -1
    else:
        return -2
    

def fed_rate_score(fed_rate_mean):
    if fed_rate_mean < 0:
        return 1
    elif 0 <= fed_rate_mean < 1.5:
        return 0
    elif 1.5 <= fed_rate_mean < 3:
        return -1
    else:
        return -2
    

def detect_macro_regime(inflation_level, gdp_level):

    if inflation_level >= 2 and gdp_level >= 2:
        return "Inflation + Croissance"
    elif inflation_level >= 2 and gdp_level <= 1:
        return "Inflation + Récession"
    elif inflation_level <= 1 and gdp_level >= 2:
        return "Déflation + Croissance"
    elif inflation_level <= 1 and gdp_level <= 1:
        return "Déflation + Récession"
    else:
        return "Zone grise / Indéterminée"

    

def precision_macro_regime(inflation_level, gdp_level, latest_inflation, latest_gdp):

    if inflation_level == 0:
        infl_pos_pct = ((latest_inflation + 4 ) / ( 4 )) * 100
    elif inflation_level == 1:
        infl_pos_pct = ((latest_inflation - 0 ) / (1 - 0)) * 100
    elif inflation_level == 2:
        infl_pos_pct = ((latest_inflation - 1 ) / (2.5 - 1)) * 100
    elif inflation_level == 3:
        infl_pos_pct = ((latest_inflation - 2.5 ) / (3.5 - 2.5)) * 100
    elif inflation_level == 4:
        infl_pos_pct = ((latest_inflation - 3.5 ) / (4.5 - 3.5)) * 100
    else:
        infl_pos_pct = ((latest_inflation - 4.5 ) / (8 - 4.5)) * 100

    if gdp_level == 0:
        gdp_pos_pct = ((latest_gdp + 6 ) / (-2 + 6 )) * 100
    elif gdp_level == 1:
        gdp_pos_pct = ((latest_gdp - 2 ) / (0 + 2)) * 100
    elif gdp_level == 2:
        gdp_pos_pct = ((latest_gdp - 0 ) / (1 - 0)) * 100
    elif gdp_level == 3:
        gdp_pos_pct = ((latest_gdp - 1 ) / (2.5 - 1)) * 100
    elif gdp_level == 4:
        gdp_pos_pct = ((latest_gdp - 2.5 ) / (4 - 2.5)) * 100
    else:
        gdp_pos_pct = ((latest_gdp - 4 ) / (8 - 4)) * 100

    if infl_pos_pct < 0 or gdp_pos_pct < 0:
        print("Warning: Negative position percentage detected. Please check the data.")
    if infl_pos_pct > 100 or gdp_pos_pct > 100:
        print("Warning: Position percentage exceeds 100%. Please check the data.")
    
    return infl_pos_pct, gdp_pos_pct


def portflio_macro_alocation(inflation_level, gdp_level):
    if inflation_level >= 2 and gdp_level >= 2:
        return "Allouer vers des Actions, de l'Or et du Cash"
    elif inflation_level >= 2 and gdp_level <= 1:
        return "Allouer vers de l'Or et du Cash"
    elif inflation_level <= 1 and gdp_level >= 2:
        return "Allouer vers des Actions et Obligations"
    elif inflation_level <= 1 and gdp_level <= 1:
        return "Allouer vers des Cash et Obligations"
    else:
        return "Stratégie d'allocation indéterminée"
    
def compute_latest_snapshot(region="FR", start=datetime(2023, 10, 1)):
    cpi, gdp, pol, unrt = get_macro_data(region, start)
    latest_inflation, latest_gdp, *_ = data_optimization(cpi, gdp, pol, unrt)
    infl_lvl = analyze_inflation_data(latest_inflation)
    gdp_lvl  = analyze_growth_data(latest_gdp)
    regime   = detect_macro_regime(infl_lvl, gdp_lvl)
    return {
        "date": cpi.index[-1],             # ou datetime.today()
        "inflation": latest_inflation,
        "growth": latest_gdp,
        "infl_lvl": infl_lvl,
        "gdp_lvl": gdp_lvl,
        "regime": regime,
    }
    
def main():
    cpi, gdp, pol, unrt = get_macro_data("FR", datetime(2023, 10, 1))
    latest_inflation, latest_gdp, pol_mean, unrt_mean, z_unrate, z_fed, inflation_adj, growth_adj = data_optimization(cpi, gdp, pol, unrt)
    inflation_level = analyze_inflation_data(latest_inflation)
    growth_level = analyze_growth_data(latest_gdp)
    macro_regime = detect_macro_regime(inflation_level, growth_level)
    infl_pos_pct, gdp_pos_pct = precision_macro_regime(inflation_level, growth_level, latest_inflation, latest_gdp)


    console = Console()

    table = Table(title="Macro Dashboard", show_header=True, header_style="bold magenta")
    table.add_column("Metric",  justify="left")
    table.add_column("Value",   justify="right")

    table.add_row("Latest CPI YoY",  f"{latest_inflation:,.2f} %")
    table.add_row("Inflation level", str(inflation_level))
    table.add_row("Infl pos %",      f"{infl_pos_pct:.1f} %")
    table.add_row("Latest GDP YoY",  f"{latest_gdp:,.2f} %")
    table.add_row("Growth level",    str(growth_level))
    table.add_row("GDP pos %",       f"{gdp_pos_pct:.1f} %")

    console.print(table)
    console.print(Panel(f"[bold yellow]Macro Regime[/bold yellow]\n{macro_regime}", expand=False))
    console.print(Panel(f"[bold blue]Macro Portfolio[/bold blue]\n{portflio_macro_alocation(inflation_level, growth_level)}", expand=False))

if __name__ == "__main__":
    main()