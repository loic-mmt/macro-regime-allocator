from MRPA import (
    SERIES,
    get_macro_data,
    data_optimization,
    analyze_inflation_data,
    detect_macro_regime,
    analyze_growth_data,
    precision_macro_regime,
)
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from rich.console import Console
from rich.table  import Table
from rich.panel  import Panel

# Get data
# Get last infl level and growth level
# Def current regime
# While iloc-1 regime == current regime: iloc -= 1
# Once regime changes, compute the duration of the previous regime
# Repeat until the end of the data


def get_long_macro_data():
    """
    Fetches long-term macroeconomic data for France and returns each series.
    """
    cpi, gdp, pol, unrt = get_macro_data(region="FR", start=datetime(2000, 1, 1))
    return cpi, gdp, pol, unrt


def long_data_optimization():
    """
    Optimizes long-term macroeconomic data for France.
    """
    cpi, gdp, pol, unrt = get_long_macro_data()
    latest_infl, latest_gdp, *_ = data_optimization(cpi, gdp, pol, unrt)

    
    inflation_list = []
    gdp_list = []

    

    for i in range(13, len(cpi)):
        inflation_list.append(((cpi.iloc[i - 1].item() / cpi.iloc[i - 13].item()) - 1) * 100)
       
        
    for i in range(4, len(gdp)):
        gdp_list.append(((gdp.iloc[i - 1].item() / gdp.iloc[i - 4].item()) - 1) * 100)

    gdp_m = gdp.resample("ME").ffill()
    gdp_m_list = []
    for i in range(13, len(gdp_m)):
        gdp_m_list.append(((gdp_m.iloc[i - 1].item() / gdp_m.iloc[i - 13].item()) - 1) * 100)
    
    unrt_m = unrt.resample("ME").ffill()
    unrt_m_list = []
    for i in range(13, len(unrt_m)):
        unrt_m_list.append(((unrt_m.iloc[i - 1].item() / unrt_m.iloc[i - 13].item()) - 1) * 100)
    unrt_chg = unrt_m.diff(3)

    return latest_infl, latest_gdp, inflation_list, gdp_list, gdp_m_list, gdp_m, unrt_m_list, unrt_chg



def detect_inflation_level(latest_inflation):
    """
    Analyzes the inflation data and returns the latest inflation level.
    """
    infl_lvl = analyze_inflation_data(latest_inflation)
    return infl_lvl



def detect_growth_level(latest_gdp):
    """
    Analyzes the growth data and returns the latest growth level.
    """
    gdp_lvl = analyze_growth_data(latest_gdp)
    return gdp_lvl



def detect_curent_regime(inflation_level, growth_level):
    current_regime = detect_macro_regime(inflation_level, growth_level)
    return current_regime



def detect_previous_regime(inflation_list, gdp_list, gdp_m_list, unrt_chg):

    infl_lvl_list = []
    gdp_lvl_list= []
    gdp_m_lvl_list = []

    for i in range(len(inflation_list)):
        
        if (inflation_list[i]) < 0:
            infl_lvl_list.append(0)
        elif 0 <= (inflation_list[i]) < 0.5:
            infl_lvl_list.append(0.5) 
        elif 0.5 <= (inflation_list[i]) < 1:
            infl_lvl_list.append(1)
        elif 1 <= (inflation_list[i]) < 1.5:
            infl_lvl_list.append(1.5)  
        elif 1.5 <= (inflation_list[i]) < 2:
            infl_lvl_list.append(2)
        elif 2 <= (inflation_list[i]) < 2.5:
            infl_lvl_list.append(2.5)   
        elif 2.5 <= (inflation_list[i]) < 3:
            infl_lvl_list.append(3)
        elif 3 <= (inflation_list[i]) < 3.5:
            infl_lvl_list.append(3.5)
        elif 3.5 <= (inflation_list[i]) < 4:
            infl_lvl_list.append(4)  
        elif 4 <= (inflation_list[i]) < 4.5:
            infl_lvl_list.append(4.5)   
        else:
            infl_lvl_list.append(5)


    for i in range(len(gdp_m_list)):
        if gdp_m_list[i] < -2:
            gdp_m_lvl_list.append(-2)
        elif -1 <= gdp_m_list[i] < 0:
            gdp_m_lvl_list.append(0)
        elif 0 <= gdp_m_list[i] < 0.5:
            gdp_m_lvl_list.append(0.5)
        elif 0.5 <= gdp_m_list[i] < 1:
            gdp_m_lvl_list.append(1)
        elif 1 <= gdp_m_list[i] < 1.5:
            gdp_m_lvl_list.append(1.5)    
        elif 1.5 <= gdp_m_list[i] < 2:
            gdp_m_lvl_list.append(2)
        elif 2 <= gdp_m_list[i] < 2.5:
            gdp_m_lvl_list.append(2.5)
        elif 2.5 <= gdp_m_list[i] < 3:
            gdp_m_lvl_list.append(3)
        elif 3 <= gdp_m_list[i] < 3.5:
            gdp_m_lvl_list.append(3.5)  
        elif 3.5 <= gdp_m_list[i] < 4:
            gdp_m_lvl_list.append(4)  
        else:
            gdp_m_lvl_list.append(5)


    s_infl = pd.Series(infl_lvl_list)          # index par défaut 0…n-1
    s_gdp  = pd.Series(gdp_m_lvl_list)

    min_len = min(len(s_infl), len(s_gdp))     # tronque la série la plus longue
    infl = s_infl.iloc[-min_len:].values
    gdp  = s_gdp.iloc[-min_len:].values

    
    # 1) Vectorise les bandes
    infl_band = np.digitize(infl, [-np.inf, 0, 1, 2, 3, 4, np.inf]) - 1
    gdp_band  = np.digitize(gdp, [-np.inf, -2, 0, 2, 4, np.inf]) - 1

    # 2) Code unique
    regime_code = infl_band*10 + gdp_band        # 00, 01, …, 55

    # 3) Détection de rupture / ETA
    change_idx = np.flatnonzero(np.diff(regime_code)) + 1
    durations  = np.diff(np.append([0], change_idx))
    avg_dur    = durations.mean()
    if durations[-1] > avg_dur :
        predi = -(avg_dur - durations[-1])
    else :predi = avg_dur - durations[-1]
    pct_avg_duration = durations[-1] * 100 / avg_dur

    
    cond_infl_down = inflation_list[-1] < inflation_list[-2]
    cond_infl_down_plus = inflation_list[-1] < inflation_list[-3]
    cond_infl_up = inflation_list[-1] > inflation_list[-2]
    cond_infl_up_plus = inflation_list[-1] > inflation_list[-3]

    cond_gdp_down = gdp_m_list[-1] < gdp_m_list[-2]
    cond_gdp_down_plus = gdp_m_list[-1] < gdp_m_list[-3]
    cond_gdp_up = gdp_m_list[-1] > gdp_m_list[-2]
    cond_gdp_up_plus = gdp_m_list[-1] > gdp_m_list[-3]

    si1 = cond_infl_down
    si2 = cond_infl_up
    si3 = cond_infl_down & cond_infl_down_plus
    si4 = cond_infl_up & cond_infl_up_plus

    sg1 = cond_infl_down
    sg2 = cond_gdp_up
    sg3 = cond_gdp_down & cond_gdp_down_plus
    sg4 = cond_gdp_up & cond_gdp_up_plus

    seasonality_infl_codes = np.select([si1, si2, si3, si4],
                           ['Inflation moving down', 'Inflation moving up', 'Inflation moving down ++', 'Inflation moving up ++'],
                           default='No seasonality')
    seasonality_gdp_codes = np.select([sg1, sg2, sg3, sg4],
                           ['GDP moving down', 'GDP moving up', 'GDP moving down ++', 'GDP moving up ++'],
                           default='No seasonality')
    
    if pct_avg_duration > 100 :
        prediction = (f"Regime should have changed {predi:.2f} months ago, incoming change anytime soon.")
    else :
        prediction = (f"Still have : {predi:.2f} months to go.")

    su1 = (unrt_chg.iloc[-1] < 0) & (unrt_chg.iloc[-2] < 0)
    su2 = (unrt_chg.iloc[-1] > 0) & (unrt_chg.iloc[-2] > 0)
    seasonality_unrt_codes = np.select([su1, su2],
        ['Unemployment falling', 'Unemployment rising'],
        default='No trend')
    unrt_trend = np.where(unrt_chg < 0, "Unemp ↓", "Unemp ↑")

    
    return infl_lvl_list, gdp_m_lvl_list, regime_code, change_idx, durations, avg_dur, predi, pct_avg_duration, seasonality_infl_codes, seasonality_gdp_codes, infl, prediction, seasonality_unrt_codes, unrt_trend



def advanced_portfolio_allocation(infl_lvl_list, gdp_m_lvl_list, latest_infl, latest_gdp):

    Actions = 0
    Or = 0
    Cash =0
    Obligations = 0

    # --- alignement des tableaux pour qu’ils aient la même longueur ---
    s_infl = pd.Series(infl_lvl_list)          # index par défaut 0…n-1
    s_gdp  = pd.Series(gdp_m_lvl_list)

    min_len = min(len(s_infl), len(s_gdp))     # tronque la série la plus longue
    infl = s_infl.iloc[-min_len:].values
    gdp  = s_gdp.iloc[-min_len:].values
    
    cond_infl_plus  = infl >= 2
    cond_infl_minus = infl <= 1.9999
    cond_gdp_plus   = gdp  >= 2
    cond_gdp_minus  = gdp  <= 1.9999

    q1 =  cond_infl_plus  & cond_gdp_plus
    q2 =  cond_infl_plus  & cond_gdp_minus
    q3 =  cond_infl_minus & cond_gdp_plus
    q4 =  cond_infl_minus & cond_gdp_minus 

    quadrant_codes = np.select([q1, q2, q3, q4],
                           ['Inflation + / Croissance +', 'Inflation + / Croissance -', 'Deflation + / Croissance +', 'Deflation + /Croissance -'],
                           default='Zone grise')
    current_quad = quadrant_codes[-1]

    if current_quad == 'Inflation + / Croissance +' :
        #print("Actions, Or, Cash")
        Actions, Or, Cash = 33, 33, 33
    elif current_quad == 'Inflation + / Croissance -' :
        #print("Or, Cash")
        Or, Cash = 50, 50
    elif current_quad == 'Deflation + / Croissance +' :
        #print("Actions, Obligations")
        Actions, Obligations = 50, 50
    elif current_quad ==  'Deflation + /Croissance -' :
        #print("Cash, Obligations")
        Cash, Obligations = 50, 50

   # infl_pos_pct, gdp_pos_pct = precision_macro_regime(infl_lvl, gdp_lvl)

    return quadrant_codes, current_quad, Or, Cash, Actions, Obligations


if __name__ == "__main__":
    
    cpi, gdp, pol, unrt = get_long_macro_data()
    latest_infl, latest_gdp, inflation_list, gdp_list, gdp_m_list, gdp_m, unrt_m_list, unrt_chg = long_data_optimization()
    infl_lvl, gdp_lvl = detect_inflation_level(latest_infl), detect_growth_level(latest_gdp)
    current_regime = detect_curent_regime(infl_lvl, gdp_lvl)
    infl_lvl_list, gdp_m_lvl_list, regime_code, change_idx, durations, avg_dur, predi, pct_avg_duration, seasonality_infl_codes, seasonality_gdp_codes, infl, prediction, seasonality_unrt_codes, unrt_trend = detect_previous_regime(inflation_list, gdp_list, gdp_m_list, unrt_chg)
    quadrant_codes, current_quad, Or, Cash, Actions, Obligations = advanced_portfolio_allocation(infl_lvl_list, gdp_m_lvl_list, latest_infl, latest_gdp )
    
    #plt.plot(inflation_list)
    #plt.ylabel('Regime List')
    #plt.show()

    console = Console()

    table = Table(title="Macro Dashboard", show_header=True, header_style="bold magenta")
    table.add_column("Metric",  justify="left")
    table.add_column("Value",   justify="right")
    table.add_row("Latest CPI YoY",  f"{latest_infl:,.2f} %")
    table.add_row("Inflation level", str(infl_lvl))
    table.add_row("Latest GDP YoY",  f"{latest_gdp:,.2f} %")
    table.add_row("Growth level",    str(gdp_lvl))
    table.add_row("AVG Regime Time",    str(avg_dur))
    table.add_row("Since Last Regime Change",    str(durations[-1]))

    console.print(table)
    console.print(Panel(f"[bold yellow]Macro Regime[/bold yellow]\n{current_quad}", expand=False))
    console.print(Panel(f"[bold yellow]Current % of the avg duration[/bold yellow]\nWe're at {pct_avg_duration:.2f}% of the average duration.", expand=True))
    console.print(Panel(f"[bold yellow]Prediction[/bold yellow]\n{prediction}", expand=True))
    console.print(Panel(f"[bold yellow]Seasonality Inflation[/bold yellow]\n{seasonality_infl_codes}", expand=False))
    console.print(Panel(f"[bold yellow]Seasonality GDP[/bold yellow]\n{seasonality_gdp_codes}", expand=False))
    console.print(Panel(f"[bold yellow]Seasonality Unemployment[/bold yellow]\n{seasonality_unrt_codes}", expand=False))

    table = Table(title="Recommended Portfolio", show_header=True, header_style="bold green")
    table.add_column("Type",  justify="left")
    table.add_column("% Allocation",   justify="right")
    table.add_row("Actions :",  f"{Actions:,.2f} %")
    table.add_row("Gold :", f"{Or:,.2f} %")
    table.add_row("Obligations :",  f"{Obligations:,.2f} %")
    table.add_row("Cash :",    f"{Cash:,.2f} %")
    console.print(table)
    
    