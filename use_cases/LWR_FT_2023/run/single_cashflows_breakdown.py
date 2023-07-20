import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os, argparse, glob
from plot_sweep import get_baseline_NPV

""" The goal of this script is to produce csv and png files showing the yearly and total 
    cashflows breakdown for a given NPP"""

CASHFLOWS = ['htseCAPEX', 'htseFOM', 'htseVOM','htseELEC_CAP_MARKET','htse_amortize_htseCAPEX', 'htse_depreciate_htseCAPEX',\
              'ftCAPEX', 'ftFOM', 'ftVOM', 'co2_shipping', 'h2_ptc', 'ft_amortize_ftCAPEX', 'ft_depreciate_ftCAPEX',\
                'ftELEC_CAP_MARKET', 'e_sales', 'naphtha_sales','diesel_sales', 'jet_fuel_sales','storageCAPEX']
DISCOUNT_RATE = 0.1 #10% used 
cashflows_names = {'h2_ptc':r'$H_2 \; PTC$', 
                    'jet_fuel_sales':'Jet Fuel', 
                    'e_sales':'Electricity', 
                    'diesel_sales':'Diesel', 
                    'naphtha_sales':'Naphtha', 
                    'elec_cap_market':'Capacity\nMarket',
                    'om': 'O&M', 
                    'co2_shipping': r'$CO_2$',
                    'capex': 'CAPEX'}
NPP_CAPACITIES = {'braidwood':1193, 'cooper':769, 'davis_besse':894, 'prairie_island':522, 'stp':1280}


def get_yearly_cashflows(plant, final_out):
  with open(final_out) as fp:
    lines = fp.readlines()
  npv = 0.0
  base_year = 2020
  df = pd.DataFrame(columns=['year'])
  df['year'] = [2020+i for i in range(21)]
  df.set_index(['year'], inplace=True)
  for c in CASHFLOWS: 
    list_rows =[]
    for l in lines:
      if ("CashFlow INFO (proj comp): Project Cashflow" in l) and (c in l):
        cashflow_name = l.split(" ")[-1][1:-3]
        if c == cashflow_name:
          ind = lines.index(l)
          for i in range(2,23):
            year = base_year+i-2
            value = float(lines[ind+i].split(" ")[-1])
            #print("Computing Cashflow {} for year {}: {}.".format(c,year, value))
            new_row = pd.DataFrame.from_dict({ 'year':[year], c:[value]})
            list_rows.append(new_row)
    df_c = pd.concat(list_rows, ignore_index=True)
    df_c.drop_duplicates(inplace=True)
    df_c.set_index(['year'], inplace=True)
    df = df.join(df_c, how='left')
  return df

def get_yearly_fcff(plant, final_out):
  with open(final_out) as fp:
    lines = fp.readlines()
  list_rows = []
  for l in lines: 
    if ("CashFlow INFO (FCFF): FCFF yearly (not discounted):" in l):
      ind = lines.index(l)
      # Get the next 6 lines
      to_split = ""
      for i in range(1,7):
        to_split+=lines[ind+i]
      # Remove first and last characters
      to_split = to_split[2:-2]
      fcff_list = to_split.split("  ")
      fcff_list = [float(f) for f in fcff_list]
  for i in range(len(fcff_list)):
    new_row = pd.DataFrame.from_dict({"year":[2020+i],"fcff":[fcff_list[i]]})
    list_rows.append(new_row)
  df = pd.concat(list_rows, ignore_index=True)
  df.set_index(['year'], inplace=True)
  return df


def plot_yearly_cashflow(yearly_df, plant_dir, plant, tag): 
  """
  Plot the yearly cashflows from the discounted cashflows
    @ In, yearly_df, pd.DataFrame, dataframe with the discounted cashflows
    @ In, plant_dir, str, path to the case directory
    @ In, plant, str, name of the case
    @ In, tag, str, indicates either the case number for a sweep run or "opt" for an optimization run
    @ Out, None
  """
  plt.rc('font', size=14)
  result_df = yearly_df.copy()
  # Combine for better visibility
  years = result_df.index
  # Compute total capex, o&m, elec cap market from more detailed costs
  # capex
  capex_cashflows = [c for c in CASHFLOWS if 'CAPEX' in c]
  result_df['capex'] = result_df[capex_cashflows].sum(axis=1)
  result_df.drop(columns = capex_cashflows, inplace = True)
  # om
  om_cashflows = [c for c in CASHFLOWS if ('OM' in c)]# or ('co2' in c)]
  result_df['om'] = result_df[om_cashflows].sum(axis=1)
  result_df.drop(columns = om_cashflows, inplace=True)
  # capacity market
  cap_cashflows = [c for c in CASHFLOWS if 'ELEC_CAP_MARKET' in c]
  result_df['elec_cap_market'] = result_df[cap_cashflows].sum(axis=1)
  result_df.drop(columns = cap_cashflows, inplace=True)
  # Divide by 1e6 for results in M$ 
  for c in list(result_df.columns):
    if 'year' not in str(c):
      result_df[c] /=1e6
  # Rename columns 
  result_df.rename(lambda x: " ".join(x.split("_")).upper(), axis='columns', inplace=True)
  # Colors
  color_mapping ={
    'JET FUEL SALES':'blue',
    'DIESEL SALES':'green',
    'NAPHTHA SALES':'yellow',
    'H2 PTC':'grey',
    'E SALES':'black',
    'CAPEX':'orange',
    'OM':'pink',
    'CO2 SHIPPING':'red',
    'ELEC CAP MARKET':'brown',
  }
  fig, ax = plt.subplots()
  result_df.plot.bar(ax=ax, y=color_mapping.keys(), stacked=True, color=color_mapping.values())
  ax.set_ylabel('Cashflows (M$(2020))')
  ax.yaxis.grid(which='major',color='gray', linestyle='dashed', alpha=0.7)
  plt.legend(ncol = 1, bbox_to_anchor=(1.05,1.0), frameon = False, loc="upper left")
  plt.gcf().set_size_inches(11, 6)
  plt.tight_layout()
  plt.subplots_adjust(bottom=0.1)
  plt.savefig(os.path.join(plant_dir, plant+"_"+tag+"_yearly_cashflow_breakdown.png"))

def plot_lifetime_cashflow(plant, plant_dir, lifetime_df, tag):
  """
  Plot the lifetime cashflows from the aggregated discounted cashflows
    @ In, plant, str, name of the case
    @ In, plant_dir, str, path to the case directory
    @ In, lifetime_df, pd.DataFrame, dataframe with the total discounted cashflows
    @ In, tag, str, indicates either the case number for a sweep run or "opt" for an optimization run
    @ Out, None
  """
  plt.rc('font', size=14)
  result_df = lifetime_df.copy()
  npv = result_df['npv']
  print('NPV {}'.format(npv))
  result_df.drop(columns={'npv'}, inplace=True)
  # Compute total capex, o&m, elec cap market from more detailed costs
  # capacity market
  cap_cashflows = [c for c in CASHFLOWS if 'ELEC_CAP_MARKET' in c]
  result_df['elec_cap_market'] = result_df[cap_cashflows].sum(axis=1)
  result_df.drop(columns = cap_cashflows, inplace=True)
  # capex
  capex_cashflows = [c for c in CASHFLOWS if 'CAPEX' in c]
  result_df['capex'] = result_df[capex_cashflows].sum(axis=1)
  result_df.drop(columns = capex_cashflows, inplace = True)
  # om
  om_cashflows = [c for c in CASHFLOWS if ('OM' in c)]# or ('co2' in c)]
  result_df['om'] = result_df[om_cashflows].sum(axis=1)
  result_df.drop(columns = om_cashflows, inplace=True)
  # TRanspose for plotting
  df = result_df.transpose()
  df.reset_index(inplace=True)
  df.rename(columns={'index':'category', 0:'value'}, inplace=True)
  df = df.sort_values(by=['value'], ascending=False)
  df.reset_index(inplace=True)

  print(plant)
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
  plt.savefig(os.path.join(plant_dir, plant+"_"+tag+"_total_cashflow_breakdown.png"))
  return None

def discount_yearly_cashflow(yearly_df, discount_rate):
  """ Discount the values for the yearly cashflows i.e. divide by (1+r)^y
    @ In, yearly_df, pd.DataFrame, dataframe with cashflow (columns) values per year (rows)
    @ Out, new_df, pd.DataFrame, dataframe with discounted cashflow (columns) values per year (rows)
  """
  yearly_df.reset_index(inplace=True)
  base_year = yearly_df['year'].min()
  new_df = pd.DataFrame()
  new_df['year'] = yearly_df['year']
  for c in yearly_df.columns: 
    if 'year' not in c:
      new_df[c] = yearly_df[c]/(np.power(1+discount_rate,yearly_df.index))
  return new_df

def create_final_cashflows(yearly_df):
  """
  From the discounted yearly cashflows create the lifetime total cashflow dataframe
    @ In, yearly_df, pd.DataFrame, dataframe containing the yearly discounted cashflows
    @ Out, lifetime_df, pd.DataFrame, dataframe with the total lifetime cashflows
  """
  new = yearly_df.drop(columns={'year'}).rename(columns={'fcff':'npv'})
  lifetime_df = new.sum().to_frame().transpose()
  return lifetime_df


def test(plant, final_out, plant_dir, total=True, tag=None, case_number = None): 
  fcff = get_yearly_fcff(plant,final_out)
  yearly = get_yearly_cashflows(plant, final_out)
  yearly_df = fcff.join(yearly, how='left')
  yearly_df = discount_yearly_cashflow(yearly_df, DISCOUNT_RATE)
  lifetime_df = create_final_cashflows(yearly_df)
  if tag == "sweep": 
    new_tag = tag+str(case_number)
    yearly_df.to_csv(os.path.join(plant_dir, plant+"_"+new_tag+"_yearly_cashflow.csv"))
    lifetime_df.to_csv(os.path.join(plant_dir, plant+"_"+new_tag+"_total_cashflows.csv"))
    plot_yearly_cashflow(yearly_df, plant_dir=plant_dir, plant=plant, tag=new_tag)
    plot_lifetime_cashflow(plant, plant_dir,lifetime_df, tag=new_tag)
  elif tag == "opt" or tag=="baseline":
    yearly_df.to_csv(os.path.join(plant_dir, plant+"_"+tag+"_yearly_cashflow.csv"))
    lifetime_df.to_csv(os.path.join(plant_dir, plant+"_"+tag+"_total_cashflows.csv"))
    plot_yearly_cashflow(yearly_df, plant_dir=plant_dir, plant=plant, tag=tag)
    plot_lifetime_cashflow(plant, plant_dir,lifetime_df, tag=tag)
  else: 
    raise TypeError("Tag not recognized : {}".format(tag))


def main(plant, final_out, plant_dir, total=True):
  if total: 
    plot_lifetime_cashflow(plant,plant_dir,final_out)
  else:
    fcff = get_yearly_fcff(plant,final_out)
    yearly = get_yearly_cashflows(plant, final_out) 
    yearly_df = fcff.join(yearly, how='left')
    yearly_df.to_csv(os.path.join(plant_dir, "yearly_cashflow.csv"))
    plot_yearly_cashflow(yearly_df, plant_dir=plant_dir, plant=plant)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('case_name', type=str, help="Case folder name in the run directory")
  args = parser.parse_args()
  dir = os.path.dirname(os.path.abspath(__file__))
  os.chdir(dir)
  print("Current Directory: {}".format(os.getcwd()))
  plant_dir = os.path.join(dir, args.case_name)
  print("Case directory : {}".format(plant_dir))
  for final_out in glob.glob(plant_dir+'/gold/out~inner*'):
    plant = args.case_name.split('_')[0]
    print("Breaking down cashflows for plant {}".format(plant))
    tag = args.case_name.split("_")[-1]

    case_n = None
    if tag == "opt":
      print("Optimization case")
    elif tag == "sweep":
      case_n = final_out.split("/")[-1].split("_")[0][-1]
      print("Case # {} in sweep results ".format(case_n))
    elif tag == "baseline":
      print("Baseline case")
    else:
      case_n = final_out.split("/")[-1].split("_")[0][-1]
      print("Case # {} in sweep results ".format(case_n))
    test(plant, final_out, plant_dir, tag=tag, case_number=case_n)
