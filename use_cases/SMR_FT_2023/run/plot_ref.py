import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import csv

LOCATIONS = ['illinois', 'minnesota', 'nebraska', 'ohio', 'texas']
locations = ['Illinois', 'Minnesota', 'Nebraska', 'Ohio', 'Texas']
variables = ['smr_capacity','htse_capacity','ft_capacity','h2_storage_capacity', 'mean_NPV','std_NPV' ]


def load_results():
  dir = os.path.dirname(os.path.abspath(__file__))
  df_plot = pd.DataFrame(columns=variables+['location'])
  df_plot.set_index(['location'], inplace=True)
  for loc in LOCATIONS:
    loc_dir = os.path.join(dir, loc+'_smr')
    sweep_file = os.path.join(loc_dir, 'gold', 'sweep.csv')
    if os.path.isfile(sweep_file):
      temp_df = pd.read_csv(sweep_file).iloc[0,:]
      for var in variables:
        df_plot.loc[loc, var] = temp_df[var]
    else: 
      print('File not found at {}'.format(sweep_file))
  df_plot['2std_NPV'] = 2*df_plot['std_NPV']
  print(df_plot)
  writer = pd.ExcelWriter('results.xlsx', engine='openpyxl', mode='a', if_sheet_exists='replace')
  df_plot.to_excel(writer, index=True, header=True, sheet_name='data')
  writer.close()
  return df_plot


def plot_ref(df_plot): 
  plt.style.use('ggplot')
  fig, axes = plt.subplots(figsize=(5,5))
  ind = np.arange(len(df_plot))
  width=0.35
  axes.bar(df_plot.index, df_plot['mean_NPV'], width, yerr=df_plot['2std_NPV'])
  fig.tight_layout()
  fig.savefig('smr_ft.png')
  



def main():
  df_plot = load_results()
  plot_ref(df_plot)

if __name__ == "__main__":
  main()