import pandas as pd
import seaborn as sns
import os, glob
from gold_results import get_final_npv
import numpy as np
import matplotlib.pyplot as plt

LOCATIONS = ['braidwood', 'cooper', 'davis_besse', 'prairie_island', 'stp']
REG_VARIABLES = ['capex', 'elec', 'om', 'synfuels']
W_VARIABLES = ['co2', 'ptc']

def load_SA_results(): 
  # create empty dataframe
  dir = os.path.dirname(os.path.abspath(__file__))
  reg_df = pd.DataFrame(columns=['location', 'variable', 'ddNPV low', 'sd ddNPV low', 'ddNPV high', 'sd ddNPV high'])
  w_df = pd.DataFrame(columns=['location', 'variable', 'ddNPV'])
  # for each variable and each location compute delta NPV and sd delta NPV
  loc_dic = {}
  for loc in LOCATIONS: 
    baseline = os.path.join(dir, loc+'_baseline')
    baseline_npv, baseline_npv_sd = get_final_npv(baseline)
    ref = os.path.join(dir, loc+'_sweep')
    ref_npv, ref_npv_sd = get_final_npv(ref)
    low_values = []
    high_values = []
    low_values_sd = []
    high_values_sd = []
    for v in REG_VARIABLES: 
      low_case = os.path.join(dir,loc+'_'+v+'_0.75')
      high_case = os.path.join(dir,loc+'_'+v+'_1.25')
      low_npv, low_npv_sd = get_final_npv(low_case)
      high_npv, high_npv_sd = get_final_npv(high_case)
      low_ddNPV = (low_npv-ref_npv)*100/(ref_npv-baseline_npv)
      low_ddNPV_sd = 2*100*np.sqrt((low_npv_sd/low_npv)**2 + 2*(ref_npv_sd/ref_npv)**2 + (baseline_npv_sd/baseline_npv)**2)
      high_ddNPV = (high_npv-ref_npv)*100/(ref_npv-baseline_npv)
      high_ddNPV_sd = 2*100*np.sqrt((high_npv_sd/high_npv)**2 + 2*(ref_npv_sd/ref_npv)**2 + (baseline_npv_sd/baseline_npv)**2)
      v_row = {'location':loc,
                  'variable':v,  
                  'ddNPV low':low_ddNPV, 
                  'sd ddNPV low':low_ddNPV_sd, 
                  'ddNPV high':high_ddNPV, 
                  'sd ddNPV high':high_ddNPV_sd}#Error bar = 2*SD for 95% values
      reg_df = reg_df.append(v_row, ignore_index=True)
      low_values.append(low_ddNPV)
      low_values_sd.append(low_ddNPV_sd)
      high_values.append(high_ddNPV)
      high_values_sd.append(high_ddNPV_sd)
    loc_dic[loc] = {'low_values':low_values,
                    'low_values_sd':low_values_sd, 
                    'high_values':high_values, 
                    'high_values_sd':high_values_sd}
    for v in W_VARIABLES: 
      cases = glob.glob(os.path.join(dir,loc+'_'+v+'*'))
      for c in cases:
        c_npv, c_npv_sd = get_final_npv(c)
        ddNPV = (c_npv-ref_npv)*100/(ref_npv-baseline_npv)
        ddNPV_sd = 2*100*np.sqrt((c_npv_sd/c_npv)**2 + 2*(ref_npv_sd/ref_npv)**2 + (baseline_npv_sd/baseline_npv)**2)
        c_row = {'location':loc,
                'variable':c.split('/')[-1],
                'ddNPV':ddNPV,
                'sd ddNPV':ddNPV_sd}
        w_df = w_df.append(c_row, ignore_index=True)
  return reg_df, w_df, loc_dic

def plot_SA(df, loc_dic): 
  plt.style.use('ggplot')
  fig, axes = plt.subplots(3,2, sharex=True, figsize=(12,10))
  ax = fig.axes
  for i in range(len(LOCATIONS)):
    df_loc = df[df['location']==LOCATIONS[i]]
    val_dic = loc_dic[LOCATIONS[i]]
    ind = np.arange(len(val_dic['low_values']))
    width=0.35

    p1 = ax[i].bar(ind, val_dic['low_values'], width, yerr=val_dic['low_values_sd'], label='Low (Ref x0.75)')
    p2 = ax[i].bar(ind, val_dic['high_values'], width, yerr=val_dic['high_values_sd'], label='High (Ref x1.25)')
    ax[i].axhline(0, color='grey', linewidth=0.8)
    ax[i].set_ylabel('Change in profitability (%)')
    ax[i].set_title(LOCATIONS[i])
    ax[i].set_xticks(ind)
    ax[i].set_xticklabels(REG_VARIABLES)
  handles, labels = ax[-1].get_legend_handles_labels()
  # So far, nothing special except the managed prop_cycle. Now the trick:
  lines_labels = [ax[0].get_legend_handles_labels()]
  lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]

# Finally, the legend (that maybe you'll customize differently)
  fig.legend(lines, labels, loc='upper center', ncol=4)
  fig.tight_layout()
  plt.show()

  #sns.barplot(ax=ax[0],data=high_df, x='variable', y='ddNPV', hue='location', errorbar='sd', errcolor='black')
  #sns.barplot(ax=ax[1],data=low_df, x='variable', y='ddNPV', hue='location', errorbar='sd', errcolor='black')
  #print(high_df)
  #test_df.plot(ax = ax[0], kind = "bar",stacked=True, x='variable',y = 'ddNPV', legend = False) 
  #ax[0].errorbar(x=test_df['variable'], y=test_df['ddNPV'],  yerr = test_df['sd ddNPV'], 
  #            linewidth = 1, color = "black", capsize = 2, fmt='none')
  #plt.show()



def main():
  # Create dataframe with columns location, sensitivity, variable, delta NPV, std delta NPV
  reg_df, w_df, loc_dic = load_SA_results()
  plot_SA(reg_df, loc_dic)
  # Plot results 2 subplots, 1 high values, 1 low values, x axis variables, y axis delta NPV, colors for location

if __name__ == "__main__":
  main()