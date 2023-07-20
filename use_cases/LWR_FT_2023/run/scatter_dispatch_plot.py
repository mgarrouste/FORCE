import pandas as pd 
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt

CASES = ['braidwood', 'cooper', 'davis_besse', 'prairie_island', 'stp']
loc_names = {'braidwood':'Braidwood', 
              'cooper':'Cooper',
              'davis_besse':'Davis-Besse',
              'prairie_island':'Prairie Island',
              'stp': 'South Texas Project'}
npp_cap = {'braidwood':1193, 
              'cooper':769,
              'davis_besse':894,
              'prairie_island':522,
              'stp': 1280}
CLUSTER_nb = 0
START_YEAR = 2014
STOP_YEAR = 2023


""" Script to plot a scatter plot Y=MWh to the grid, X=price of electricity ($/MWh), 
for each location a different color"""

def load_data(location):
  """ Get the data for given location: price and MWh to the grid"""
  dir = os.path.dirname(os.path.abspath(__file__))
  path = os.path.join(dir,location+"_dispatch", "gold", "dispatch_print.csv")
  if os.path.exists(path):
    df = pd.read_csv(path)
  else:
    raise FileExistsError("Dispatch results do not exist for the location {} at {}".format(location, path))
  print("max price : {} ".format(max(df['price'])))
  df = df[(df['_ROM_Cluster']==CLUSTER_nb) & (df['Year']>=START_YEAR) &(df['Year']<=STOP_YEAR)]
  df_loc = df[['Year','price','Dispatch__electricity_market__production__electricity']]
  df_loc['location'] = location
  df_loc['Location'] = loc_names[location]
  df_loc.rename(columns={'Dispatch__electricity_market__production__electricity':'electricity_market'},
                inplace=True)
  df_loc['electricity_market'] = np.abs(df_loc['electricity_market'])*100/npp_cap[location]
  return df_loc

def aggregate_data(cases):
  list_df = []
  for case in cases: 
    list_df.append(load_data(case))
  df = pd.concat(list_df, axis=0, ignore_index=True)
  return df

def plot_dispatch_scatter_2(df, year):
  plt.style.use('seaborn-paper')
  fig, ax = plt.subplots()
  df_year = df[df['Year']==year]
  df_year.reset_index(inplace=True)
  g = sns.scatterplot(ax=ax, data=df_year, 
                  x="price", 
                  y='electricity_market', 
                  hue='Location',
                  palette='bright', s=30, linestyle='--')
  g.set_ylabel("Electricity sent to the grid \n(% NPP Capacity)")
  g.set_xlabel("Electricity price ($/MWh)")
  g.set(ylim=(-5, 105))
  sns.despine(trim=True)
  fig.tight_layout()
  fig_name = "scatter_dispatch_{}_cluster_{}.png".format(year, CLUSTER_nb)
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),'dispatch_results',fig_name))



def plot_dispatch_scatter(df):
  plt.style.use('seaborn-paper')
  fig, ax = plt.subplots(figsize=(6,8))
  for year in range(START_YEAR, STOP_YEAR+1):
    df_year = df[df['Year']==year]
    g = sns.relplot( data=df_year, 
                    x="price", 
                    y='electricity_market', 
                    hue='Location', 
                    col='Location', 
                    col_wrap=2, palette='bright',s=50,markers='.',legend=False)
    g.set_titles(col_template="{col_name}")
    g.set_ylabels("Electricity sent to the grid \n(% NPP Capacity)")
    g.set(ylim=(-5, 105))
    sns.despine(trim=True)
    g.set_xlabels("Electricity price ($/MWh)")
    g.tight_layout()
    fig_name = "scatter_dispatch_{}_cluster_{}_years_{}_{}.png".format(year, CLUSTER_nb, START_YEAR, STOP_YEAR)
    g.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),'dispatch_results',fig_name))

def main():
  df = aggregate_data(cases=CASES)
  plot_dispatch_scatter(df)
  for year in range(START_YEAR, STOP_YEAR+1):
    plot_dispatch_scatter_2(df,year)


def test():
  load_data('braidwood')

if __name__ == '__main__':
  main()