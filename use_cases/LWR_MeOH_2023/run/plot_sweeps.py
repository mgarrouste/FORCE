import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import seaborn as sns
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

locations_names = {'braidwood':'Braidwood', 'cooper':'Cooper', 'davis_besse':'Davis-Besse', 'prairie_island':'Prairie Island', 
                    'stp':'South Texas Project'}


def plot_hist(sweep_df):

  plt.style.use('seaborn-paper')
  fig, ax = plt.subplots()

  # Results in M$
  sweep_df['delta_NPV'] /=1e6
  sweep_df['2std_dNPV'] /=1e6

  sweep_df.plot(ax = ax, kind = "bar", y ='delta_NPV', yerr='2std_dNPV' ,legend = False) 
  ax.set_xticks(np.arange(len(list(locations_names.keys()))))
  ax.set_xticklabels(locations_names.values(), rotation=0)
  ax.set_ylabel(r'$\Delta(NPV) \;\$M \;USD(2020)$')

  ax.yaxis.set_major_locator(MultipleLocator(100))
  sns.despine(ax=ax, trim=True)

  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sweep_results.png"))
  return None


def get_results():
  """
  Post processing of the sweep results: keep opt variables mean NPV and std NPV*2
  Sort values % mean NPV and keep the top 4:
    @ In, sweep_file, str, path to csv file results of sweep run
    @ In, mean_NPV_baseline, float, value for the mean NPV of the baseline (elec) case
    @ In, std_NPV_baseline, float, value for the std NPV of the baseline (elec) case
    @ Out, sweep_df, pd.DataFrame, sorted dataframe of results
  """
  sweep_df = pd.DataFrame(columns=['location', 'name', 'mean_NPV', 'std_NPV', 'baseline_NPV', 'std_baseline_NPV', \
    'npp_capacity','htse_capacity','ft_capacity', 'h2_storage_capacity'])
  for location, location_name in locations_names.items():
    s_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), location+'_sweep', 'gold', 'sweep.csv')
    if os.path.isfile(s_file):
      s_df = pd.read_csv(s_file)
      baseline_NPV, std_baseline_NPV = get_baseline_NPV(location)
      to_add = {'location': [location], 
                'name': [location_name],
                'mean_NPV': [s_df.loc[0,'mean_NPV']], 
                'std_NPV': [s_df.loc[0, 'std_NPV']],
                'baseline_NPV': [baseline_NPV], 
                'std_baseline_NPV': [std_baseline_NPV], 
                'htse_capacity': [s_df.loc[0, 'htse_capacity']],
                'h2_storage_capacity': [s_df.loc[0, 'h2_storage_capacity']],
                'meoh_capacity': [s_df.loc[0, 'meoh_capacity']],
                'npp_capacity': [s_df.loc[0, 'npp_capacity']]}
      sweep_df = pd.concat([sweep_df,pd.DataFrame.from_dict(to_add)], ignore_index=True)
    else: 
      print(f'No sweep results for {location} there: {s_file}')
      exit() 
  sweep_df['delta_NPV'] = sweep_df['mean_NPV']-sweep_df['baseline_NPV']
  sweep_df['2std_dNPV'] = 2*np.sqrt(np.power(sweep_df['std_NPV'],2)+np.power(sweep_df['std_baseline_NPV'],2))
  return sweep_df

def get_baseline_NPV(case):
  baseline_case = case+'_baseline'
  baseline_file = os.path.join(baseline_case, 'gold', 'sweep.csv')
  if os.path.isfile(baseline_file):
    df = pd.read_csv(baseline_file)
    # Assume the right case is printed on the first line
    mean_NPV = float(df.iloc[0,:].mean_NPV)
    std_NPV = float(df.iloc[0,:].std_NPV)
  else:
    raise FileNotFoundError("Baseline results not found")
  return mean_NPV, std_NPV

def main():
  dir = os.path.dirname(os.path.abspath(__file__))
  os.chdir(dir)
  df = get_results()
  df.to_csv(os.path.join(dir,'sweep_results.csv'))
  plot_hist(df)

if __name__ == "__main__":
  main()