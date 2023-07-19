import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os, argparse


DISCOUNT_RATE = 0.1
BASE_YEAR = 2020

cashflows_names = {'h2_ptc':r'$H_2 \; PTC$', 
                    'jet_fuel':'Jet Fuel', 
                    'electricity_market':'Electricity', 
                    'diesel_market':'Diesel', 
                    'naphtha_market':'Naphtha', 
                    'elec_cap':'Capacity\nMarket',
                    'om': 'O&M', 
                    'co2_shipping': r'$CO_2$',
                    'capex': 'CAPEX'}

NPP_CAPACITIES = {'braidwood':1193, 'cooper':769, 'davis_besse':894, 'prairie_island':522, 'stp':1280}

def get_baseline_NPV(case):
  baseline_case = case+'_baseline'
  print("Baseline case :{}".format(baseline_case))
  baseline_file = os.path.join(baseline_case, 'gold', 'sweep.csv')
  if os.path.isfile(baseline_file):
    df = pd.read_csv(baseline_file)
    # Assume the right case is printed on the first line
    mean_NPV = float(df.iloc[0,:].mean_NPV)
    print('Baseline case mean NPV: {}'.format(mean_NPV))
    std_NPV = float(df.iloc[0,:].std_NPV)
    print('Baseline case std NPV: {}'.format(std_NPV))
  else:
    raise FileNotFoundError("Baseline results not found")
  return mean_NPV, std_NPV

def discount_cashflows(cashflows_file, discount_rate = 0.1):
  yearly_df = pd.read_csv(cashflows_file)
  yearly_df.reset_index(inplace=True)
  new_df = pd.DataFrame()
  new_df['year'] = yearly_df['cfYears']+BASE_YEAR
  for c in yearly_df.columns: 
    if 'year' not in c:
      new_df[c] = yearly_df[c]/(np.power(1+discount_rate,yearly_df.index))
  return new_df

def create_final_cashflows(yearly_discounted_cashflows):
  new = yearly_discounted_cashflows.drop(columns=['index', 'cfYears', 'year'])
  # compute useful cashflows
  cashflow_names = list(new.columns)
  # CAPEX
  capex_c = [c for c in cashflow_names if 'CAPEX' in c]
  print(capex_c)
  new['capex'] = new[capex_c].sum(axis=1)
  new.drop(columns= capex_c, inplace =True)

  # O&M
  om_cashflows = [c for c in cashflow_names if ('OM' in c)]# or ('co2' in c)]
  new['om'] = new[om_cashflows].sum(axis=1)
  new.drop(columns = om_cashflows, inplace=True)

  # Capacity market
  cap_cashflows = [c for c in cashflow_names if 'ELEC_CAP_MARKET' in c]
  new['elec_cap_market'] = new[cap_cashflows].sum(axis=1)
  new.drop(columns = cap_cashflows, inplace=True)
  
  # Rename remaining columns

  for c in list(new.columns): 
    if 'market' in c: 
      new_cash_name = '_'.join(c.split('_')[0:2])
      new[new_cash_name] = new[c]
      new.drop(columns=c, inplace=True)
    if 'import' in c: 
      new.drop(columns=c, inplace=True)
    if 'export' in c:
      new.drop(columns=c, inplace=True)
    if 'co2' in c:
      new['co2_shipping'] = new[c]
      new.drop(columns=c, inplace=True)
    if 'ptc' in c: 
      new['h2_ptc'] = new[c]
      new.drop(columns=c, inplace=True)
  
  lifetime_cashflows = new.sum().to_frame()
  return lifetime_cashflows


def plot_lifetime_cashflows(lifetime_cashflows, plant, dispatch_dir): 
  df = lifetime_cashflows.reset_index()
  #df.rename({0:'value'}, axis='rows', inplace=True)
  df.rename(columns={'index':'category', 0:'value'}, inplace=True)
  print(df)
  df = df.sort_values(by='value', axis=0, ascending=False)
  df.reset_index(inplace=True)

  # In $M/NPP capacity (MWe)
  df['value'] = df['value'].div(1e6*NPP_CAPACITIES[plant])

  # Waterfall calculations
  # calculate running totals
  y='value'
  x='category'
  df['tot'] = df[y].cumsum()
  df['tot1']=df['tot'].shift(1).fillna(0)
  # lower and upper points for the bar charts
  lower = df[['tot','tot1']].min(axis=1)
  upper = df[['tot','tot1']].max(axis=1)
  # mid-point for label position
  mid = upper+0.03
  # positive number shows green, negative number shows red
  df.loc[df[y] >= 0, 'color'] = 'green'
  df.loc[df[y] < 0, 'color'] = 'red'
  # calculate connection points
  connect= df['tot1'].repeat(3).shift(-1)
  connect[1::3] = np.nan

  # Names
  df['name'] = df['category'].map(cashflows_names)
  print(df)

  #Plot
  fig,ax = plt.subplots()
  # plot first bar with colors
  bars = ax.bar(x=df[x],height=upper, color =df['color'])
  ax.yaxis.grid(which='major',color='gray', linestyle='dashed', alpha=0.7)
  # plot second bar - invisible
  ax.bar(x=df[x], height=lower,color='white')
  ax.set_ylabel('M$(2020(USD)) / MWe')
  # plot connectors
  ax.plot(connect.index,connect.values, 'k' )
  # plot bar labels
  for i, v in enumerate(upper):
      ax.text(i-.15, mid[i], f"{df[y][i]:,.3f}")
  # Baseline case as horizontal line
  baseline_NPV, std_NPV = get_baseline_NPV(plant)
  baseline_NPV /=1e6
  baseline_NPV /= NPP_CAPACITIES[plant]
  ax.axhline(baseline_NPV, color='b', linewidth=2)
  bau_text = 'BAU NPV: '+str(np.round(baseline_NPV,3))+" M$/MWe"
  ax.text(5, baseline_NPV+0.1, bau_text, color='b')

  # Rename cashflows
  ax.set_xticklabels(df['name'])

  ax.grid(axis='y',color='black', linestyle='--', alpha=0.7,linewidth=0.8)

  #plt.xticks(rotation=70)
  plt.gcf().set_size_inches(12, 7)
  #fig.tight_layout()
  plt.savefig(os.path.join(dispatch_dir, plant+"_total_cashflow_breakdown.png"))
  return None

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('case_name', type=str, help="Case name to get the cashflows from")
  args = parser.parse_args()
  dir = os.path.dirname(os.path.abspath(__file__))
  dispatch_dir = os.path.join(dir, args.case_name+'_dispatch')
  print('Looking in dispatch directory for case {} : {}'.format(args.case_name, dispatch_dir))
  cashflows_file = os.path.join(dispatch_dir, 'gold', 'cashflows_0.csv')
  if os.path.isfile(cashflows_file):
    discounted_cashflows = discount_cashflows(cashflows_file, discount_rate = DISCOUNT_RATE)
    discounted_cashflows.to_csv(os.path.join(dir, dispatch_dir, 'yearly_discounted_cashflows.csv'))
    #print(discounted_cashflows['ft_h2_ptc_CashFlow'])
    lifetime_cashflows = create_final_cashflows(discounted_cashflows)
    lifetime_cashflows.to_csv(os.path.join(dir,dispatch_dir, 'lifetime_cashflows.csv'))
    plot_lifetime_cashflows(lifetime_cashflows, plant=args.case_name, dispatch_dir=dispatch_dir)
  else: 
    print('No cashflows from dispatch run in {}'.format(cashflows_file))
    exit()