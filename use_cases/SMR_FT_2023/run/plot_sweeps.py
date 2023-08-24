import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import seaborn as sns
import matplotlib

locations_names = {'illinois':'Illinois', 'minnesota':'Minnesota', 'nebraska':'Nebraska', 'ohio':'Ohio', 
                    'texas':'Texas'}


def plot_hist(sweep_df):

  plt.style.use('seaborn-paper')
  fig, ax = plt.subplots(2,1, sharex=True)


  # Results in M$
  sweep_df['delta_NPV'] /=1e6
  sweep_df['2std_dNPV'] /=1e6
  sweep_df['mean_NPV'] /=1e6
  sweep_df['baseline_NPV'] /=1e6
  sweep_df['2std_mean_NPV'] /=1e6
  sweep_df['2std_baseline_NPV'] /=1e6


  yerr = sweep_df[['2std_mean_NPV', '2std_baseline_NPV']].to_numpy().T
  sweep_df.plot(ax = ax[0], x= 'name', kind='bar', y=['mean_NPV', 'baseline_NPV'], label=['NPV', 'BAU NPV'],legend = False,yerr=yerr , width=0.3, 
                error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3) )#, yerr = ['2std_mean_NPV','2std_baseline_NPV'])#, color='blue')
  #sweep_df.plot(ax = ax[0], kind='bar', y='baseline_NPV', yerr = '2std_baseline_NPV', color='red')
  ax[0].set_ylabel(r'$\$M \;USD(2020)$')
  ax[0].set_xlabel('')
  ax[0].yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(100))
  ax[0].set_ylim(-100+min(sweep_df['baseline_NPV']), 100+max(sweep_df['mean_NPV']))
  sns.despine(ax=ax[0], trim=True)


  sweep_df.plot(ax = ax[1], x='name',kind = "bar", y ='delta_NPV', yerr='2std_dNPV', label=r'$\Delta (NPV)$', width=0.3,capsize=2, ecolor='black', error_kw={'markeredgewidth':1}, legend = False,color='green') 
  ax[1].set_ylabel(r'$\$M \;USD(2020)$')
  ax[1].set_xticks(np.arange(len(list(locations_names.keys()))))
  ax[1].set_xticklabels(locations_names.values(), rotation=0)
  ax[1].set_xlabel('')
  ax[1].yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(100))
  ax[1].set_ylim(0, 100+max(sweep_df['delta_NPV']))
  sns.despine(ax=ax[1], trim=True)
  

  # Legend
  h1, l1, h2,l2= ax[0].get_legend_handles_labels() + ax[1].get_legend_handles_labels()
  fig.legend(h1+h2, l1+l2, bbox_to_anchor = (1,0.5))

  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "smr_ft_results.png"))
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
    'smr_capacity','htse_capacity','ft_capacity', 'h2_storage_capacity'])
  for location, location_name in locations_names.items():
    s_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), location+'_reduced_8', 'gold', 'sweep.csv')
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
                'ft_capacity': [s_df.loc[0, 'ft_capacity']],
                'smr_capacity': [s_df.loc[0, 'smr_capacity']]}
      sweep_df = pd.concat([sweep_df,pd.DataFrame.from_dict(to_add)], ignore_index=True)
    else: 
      print(f'No sweep results for {location} there: {s_file}')
      exit() 
  sweep_df['htse_capacity_h2'] = sweep_df['htse_capacity']*25.13
  sweep_df['2std_mean_NPV'] =2*sweep_df['std_NPV']
  sweep_df['2std_baseline_NPV'] = 2*sweep_df['std_baseline_NPV']
  sweep_df['delta_NPV'] = sweep_df['mean_NPV']-sweep_df['baseline_NPV']
  sweep_df['2std_dNPV'] = 2*np.sqrt(np.power(sweep_df['std_NPV'],2)+np.power(sweep_df['std_baseline_NPV'],2))
  print(sweep_df.columns)
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
  df.to_csv(os.path.join(dir,'smr_ft_results.csv'))
  plot_hist(df)

if __name__ == "__main__":
  main()