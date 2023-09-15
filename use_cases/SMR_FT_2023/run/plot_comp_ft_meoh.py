import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import seaborn as sns
import matplotlib

locations_names = {'illinois':'Illinois', 'minnesota':'Minnesota', 'nebraska':'Nebraska', 'ohio':'Ohio', 'texas':'Texas'}


def plot_hist(df_dic):

  plt.style.use('seaborn-paper')
  fig, ax = plt.subplots()

  ft_df = df_dic['FT']
  meoh_df = df_dic['MeOH']
  merged_df = ft_df[['delta_NPV', '2std_dNPV', 'name']].merge(meoh_df[['delta_NPV', '2std_dNPV', 'name']], left_on='name', right_on='name', suffixes=('_ft', '_meoh'))

  # Results in M$
  merged_df['delta_NPV_ft'] /=1e6
  merged_df['delta_NPV_meoh'] /=1e6
  merged_df['2std_dNPV_ft'] /=1e6
  merged_df['2std_dNPV_meoh'] /=1e6

  yerr = merged_df[['2std_dNPV_ft', '2std_dNPV_meoh']].to_numpy().T

  merged_df.plot(ax = ax, kind = "bar", x='name', y =['delta_NPV_ft', 'delta_NPV_meoh'], yerr=yerr , width=0.3, 
                error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
  ax.set_xticks(np.arange(len(list(locations_names.keys()))))
  ax.set_xticklabels(locations_names.values(), rotation=0)
  ax.set_ylabel(r'$\Delta(NPV) \;\$M \;USD(2020)$')
  ax.set_xlabel('')
  ax.legend(["FT", "MTD"])

  ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(100))
  ax.set_ylim(-200+min(merged_df['delta_NPV_ft']), 100+max(merged_df['delta_NPV_meoh']))
  sns.despine(ax=ax, trim=True)

  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "comparison_ft_meoh_smr.png"))
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
  df_dic = {}
  for pathway in ['FT', 'MeOH']:
    run_dir = os.path.join('/Users/garrm/FORCE/use_cases/', 'SMR_'+pathway+'_2023', 'run')
    synfuel_process_name = pathway.lower()+'_capacity'
    sweep_df = pd.DataFrame(columns=['location', 'name', 'mean_NPV', 'std_NPV', 'baseline_NPV', 'std_baseline_NPV', \
    'npp_capacity','htse_capacity','synfuel_process_capacity', 'h2_storage_capacity'])
    for location, location_name in locations_names.items():
      s_file = os.path.join(run_dir, location+'_reduced_8', 'gold', 'sweep.csv')
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
                  'synfuel_process_capacity': [s_df.loc[0, synfuel_process_name]],
                  'smr_capacity': [s_df.loc[0, 'smr_capacity']]}
        sweep_df = pd.concat([sweep_df,pd.DataFrame.from_dict(to_add)], ignore_index=True)
      else: 
        print(f'No sweep results for {location} there: {s_file}')
        exit() 
    sweep_df['delta_NPV'] = sweep_df['mean_NPV']-sweep_df['baseline_NPV']
    sweep_df['2std_dNPV'] = 2*np.sqrt(np.power(sweep_df['std_NPV'],2)+np.power(sweep_df['std_baseline_NPV'],2))
    df_dic[pathway] = sweep_df
  return df_dic

def get_baseline_NPV(case):
  baseline_case = case+'_baseline'
  baseline_file = os.path.join(baseline_case, 'gold', 'sweep.csv')
  if os.path.isfile(baseline_file):
    df = pd.read_csv(baseline_file)
    # Assume the right case is printed on the first line
    df.set_index('smr_capacity', inplace=True)
    mean_NPV = float(df.at[720.0,'mean_NPV'])
    std_NPV = float(df.loc[720.0,'std_NPV'])
  else:
    raise FileNotFoundError("Baseline results not found")
  return mean_NPV, std_NPV

def main():
  dir = os.path.dirname(os.path.abspath(__file__))
  os.chdir(dir)
  df_dic= get_results()
  ft = df_dic['FT']
  ft['pathway'] = 'FT'
  meoh = df_dic['MeOH']
  meoh['pathway'] = 'MeOH'
  to_save = pd.concat([ft, meoh], ignore_index=True)
  to_save.to_csv(os.path.join(dir,'comparison_ft_meoh_smr_results.csv'))
  plot_hist(df_dic)

if __name__ == "__main__":
  main()