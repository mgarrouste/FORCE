import pandas as pd
import os
import matplotlib.pyplot as plt
from gold_results import get_final_npv
import numpy as np
import seaborn as sns

LOCATIONS = ['braidwood', 'cooper', 'davis_besse', 'prairie_island', 'stp']
locations = ['Braidwood', 'Cooper', 'Davis-Besse', 'Prairie Island', 'South Texas Project']
opt_variables = ['htse_capacity', 'meoh_capacity', 'h2_storage_capacity']
dic_var_units = {'htse_capacity':'MWe', 'meoh_capacity':r'$ton-H_2/h$', 'h2_storage_capacity':r'$ton-H_2$'}
dic_var_names = {'htse_capacity':'HTSE', 'meoh_capacity':'Methanol', 'h2_storage_capacity':r'$H_2\; storage$'}


def plot_configurations(df_list): 
  # Input: list of dataframes to plot 
  # for each dataframe corresponding to each location
  plt.style.use('seaborn-paper')
  fig = plt.figure(constrained_layout=True, figsize=(10,12))

  # create 3x1 subfigs
  subfigs = fig.subfigures(nrows=5, ncols=1)

  # Each row corresponds to one location
  for row, subfig in enumerate(subfigs):
    # Get data for given location ataframe
    loc_name = locations[row]
    loc = LOCATIONS[row]
    df = df_list[row]

    # Absolute values and manageable units
    df['meoh_capacity'] = np.abs(df['meoh_capacity'])/1e3
    df['htse_capacity'] = np.abs(df['htse_capacity'])
    df['h2_storage_capacity'] = df['h2_storage_capacity']/1e3

    # Only feasible runs
    df = df[df['mean_NPV']> -1e9]
    
    # Baseline npv
    baseline = os.path.join(os.path.dirname(os.path.abspath(__file__)), loc+'_baseline')
    baseline_npv, baseline_npv_sd = get_final_npv(baseline)

    # Reference npv
    ref = os.path.join(os.path.dirname(os.path.abspath(__file__)), loc+'_sweep')
    ref_npv, ref_npv_sd = get_final_npv(ref)

    # Title for the row = location
    subfig.suptitle(loc_name)

    # create 1x3 subplots per subfig
    axs = subfig.subplots(nrows=1, ncols=3, sharey=True)
    for col, ax in enumerate(axs):
      var = opt_variables[col]
      var_df = df.copy()

      # Compute change in profitability
      var_df['ddNPV'] = (var_df['mean_NPV']-ref_npv)*100/np.abs(ref_npv-baseline_npv)
      if var =='meoh_capacity':
        leg_var = 'h2_storage_capacity'        
      elif var=='h2_storage_capacity':
        leg_var = 'meoh_capacity'
      else: 
        leg_var = 'meoh_capacity'
      sns.scatterplot(data=var_df, ax=ax, x=var, y='ddNPV',marker='+', hue=leg_var)

      # Labels
      ax.set_ylabel('Change in profitability (%)')
      ax.set_xlabel(f'{dic_var_names[var]} capacity ({dic_var_units[var]})')
      sns.despine(ax=ax, trim=True)
      ax.legend(title=dic_var_names[leg_var]+'\n('+dic_var_units[leg_var]+')',bbox_to_anchor=(1,1) )
      
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "SA_results_configurations.png"))


def load_sweep_data(location): 
  # Path to sweep.csv for the location
  dir = os.path.dirname(os.path.abspath(__file__))
  sweep_file = os.path.join(dir, location+'_sweep', 'gold', 'sweep.csv')
  if os.path.isfile(sweep_file):
    df = pd.read_csv(sweep_file)
  else: 
    print('No sweep results for {}, \n Sweep file path: {}'.format(location, sweep_file))
    return None
  return df

def main():
  # Load sweep data for each location and create list of dataframes
  df_list = []
  for loc in LOCATIONS:
    df_list.append(load_sweep_data(loc))
  # plot stuff
  plot_configurations(df_list)


if __name__ == "__main__":
  main()