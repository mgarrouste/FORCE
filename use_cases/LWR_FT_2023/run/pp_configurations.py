import pandas as pd
import os
import matplotlib.pyplot as plt
from gold_results import get_final_npv
import numpy as np
import seaborn as sns

LOCATIONS = ['braidwood', 'cooper', 'davis_besse', 'prairie_island', 'stp']
locations = ['Braidwood', 'Cooper', 'Davis-Besse', 'Prairie Island', 'South Texas Project']
opt_variables = ['htse_capacity', 'ft_capacity', 'h2_storage_capacity']
opt_variables_names = ['HTSE', 'FT', r'$H_2\; storage$']
opt_variables_units = ['MWe', r'$ton-H_2/h$', r'$ton-H_2$']
opt_variables_colors = ['blue', 'green', 'red']

def get_range_capacities(location):
  """Get the range of capacities tested for a given location and each component
  Absolute values
  """
  # Load data from sweep run
  sweep_results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), location+'_sweep', 'gold', 'sweep.csv')
  sweep_df = pd.read_csv(sweep_results_path)
  # Capacities dictionary 
  capacities_range = {}
  for var in opt_variables:
    capacities_range[var] = {'min':np.abs(sweep_df[var].max()),
                            'max':np.abs(sweep_df[var].min())}
  return capacities_range


def plot_configurations(df_list): 
  # Input: list of dataframes to plot 
  # for each dataframe corresponding to each location
  plt.style.use('seaborn-whitegrid')
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
    df['ft_capacity'] = np.abs(df['ft_capacity'])/1e3
    df['htse_capacity'] = np.abs(df['htse_capacity'])
    df['h2_storage_capacity'] = df['h2_storage_capacity']/1e3
    
    # Baseline npv
    baseline = os.path.join(os.path.dirname(os.path.abspath(__file__)), loc+'_baseline')
    baseline_npv, baseline_npv_sd = get_final_npv(baseline)

    # Reference npv
    ref = os.path.join(os.path.dirname(os.path.abspath(__file__)), loc+'_sweep')
    ref_npv, ref_npv_sd = get_final_npv(ref)

    # Title for the row = location
    subfig.suptitle(loc_name)

    # Optimized variables values
    opt_var_dic = get_opt_var(df)

    # Max and min for location and components
    capacities_range = get_range_capacities(loc)

    # create 1x3 subplots per subfig
    axs = subfig.subplots(nrows=1, ncols=3, sharey=True)
    for col, ax in enumerate(axs):
      var = list(opt_var_dic.keys())[col]
      if 'ft' in var:
        min_var = capacities_range[var]['min']/1e3
        max_var = capacities_range[var]['max']/1e3
      elif 'h2' in var:
        min_var = capacities_range[var]['max']/1e3
        max_var = capacities_range[var]['min']/1e3
      elif 'htse' in var:
        min_var = capacities_range[var]['min']
        max_var = capacities_range[var]['max']
      temp_vars = opt_variables.copy()
      temp_vars.remove(var)
      print(f'Location {loc_name}, variable {var}, min {min_var}, max {max_var}')

      # Select only rows where other 2 variables = optimized value
      var_df = df[df[temp_vars[0]]==opt_var_dic[temp_vars[0]]]
      var_df = var_df[var_df[temp_vars[1]]==opt_var_dic[temp_vars[1]]]

      # Compute change in profitability
      var_df['ddNPV'] = (var_df['mean_NPV']-ref_npv)*100/(ref_npv-baseline_npv)
      var_df['ddNPV_sd'] = 2*100*np.sqrt((var_df['std_NPV']/var_df['mean_NPV'])**2 + 2*(ref_npv_sd/ref_npv)**2 + (baseline_npv_sd/baseline_npv)**2)
      var_df.plot(ax=ax, kind='scatter', x=var, y='ddNPV', yerr='ddNPV_sd', color=opt_variables_colors[col])

      # Vertical dashed lines to indicate range
      ax.axvline(x=min_var, color=opt_variables_colors[col], linestyle="--", linewidth=0.7)
      ax.axvline(x=max_var, color=opt_variables_colors[col], linestyle="--", linewidth=0.8)

      # Limits
      if 'ft' in var:
        ax.set_xlim([min_var-0.5, max_var+0.5])
      elif (loc == 'stp') and ('h2' in var):
        ax.set_xlim([min_var-100, max_var+200])
      else:
        ax.set_xlim([min_var-20, max_var+20])
      ax.set_ylim(-300,15)

      # Labels
      ax.set_ylabel('Change in profitability (%)')
      ax.set_xlabel(f'{opt_variables_names[col]} capacity ({opt_variables_units[col]})', color=opt_variables_colors[col])
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "SA_results_configurations.png"))


def get_opt_var(df): 
  """ Returns dictionary with htse, ft, and h2_storage capacity optimized values"""
  df_sorted = df.sort_values(by=['mean_NPV'], ascending=False)
  opt_var = {}
  for v in opt_variables: 
    opt_var[v] = df_sorted.iloc[0,:][v]
  return opt_var

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