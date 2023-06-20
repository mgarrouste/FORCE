import pandas as pd
import seaborn as sns
import os, glob
from gold_results import get_final_npv
import numpy as np
import matplotlib.pyplot as plt

LOCATIONS = ['braidwood', 'cooper', 'davis_besse', 'prairie_island', 'stp']
locations = ['Braidwood', 'Cooper', 'Davis-Besse', 'Prairie Island', 'South Texas Project']
REG_VARIABLES = ['capex', 'elec', 'om', 'synfuels']
reg_variables = ['CAPEX', 'Electricity prices', 'O&M', 'Synfuels prices']
W_VARIABLES = ['co2_cost_high', 'co2_cost_med', 'ptc_000', 'ptc_100', 'ptc_270']
w_variables = ['CO2', 'PTC']

def load_SA_results(): 
  # create empty dataframe
  dir = os.path.dirname(os.path.abspath(__file__))
  reg_df = pd.DataFrame(columns=['location', 'variable', 'ddNPV low', 'sd ddNPV low', 'ddNPV high', 'sd ddNPV high'])
  w_df = pd.DataFrame(columns=['location', 'variable', 'ddNPV'])
  # for each variable and each location compute delta NPV and sd delta NPV
  loc_dic_reg = {}
  loc_dic_w = {}
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
    loc_dic_reg[loc] = {'low_values':low_values,
                    'low_values_sd':low_values_sd, 
                    'high_values':high_values, 
                    'high_values_sd':high_values_sd}
    loc_dic_w[loc] ={}
    for v in W_VARIABLES: 
      c = os.path.join(dir,loc+'_'+v)
      c_npv, c_npv_sd = get_final_npv(c)
      ddNPV = (c_npv-ref_npv)*100/(ref_npv-baseline_npv)
      ddNPV_sd = 2*100*np.sqrt((c_npv_sd/c_npv)**2 + 2*(ref_npv_sd/ref_npv)**2 + (baseline_npv_sd/baseline_npv)**2)
      c_row = {'location':loc,
              'variable':c.split('/')[-1],
              'ddNPV':ddNPV,
              'sd ddNPV':ddNPV_sd}
      w_df = w_df.append(c_row, ignore_index=True)
      if 'co2' in c:
        loc_dic_w[loc][v] = [ddNPV, 0]
        loc_dic_w[loc][v+'_sd'] = [ddNPV_sd, 0]
      else:
        loc_dic_w[loc][v] = [0,ddNPV]
        loc_dic_w[loc][v+'_sd'] = [0,ddNPV_sd]
  return loc_dic_reg, loc_dic_w

def plot_SA_location(loc_dic): 

  plt.style.use('ggplot')
  fig, axes = plt.subplots(3,2, figsize=(10,8))
  ax = fig.axes
  print(loc_dic)
  for i in range(len(LOCATIONS)):
    val_dic = loc_dic[LOCATIONS[i]]
    ind = np.arange(len(val_dic['low_values']))
    width=0.35
    p1 = ax[i].bar(ind, val_dic['low_values'], width, yerr=val_dic['low_values_sd'], label='Low (Ref x0.75)')
    p2 = ax[i].bar(ind, val_dic['high_values'], width, yerr=val_dic['high_values_sd'], label='High (Ref x1.25)')
    #p3 = ax[i].bar(ind, val_dic['ptc_000'], width, yerr=val_dic['ptc_000_sd'], label='PTC $0/kg-H2')
    ax[i].axhline(0, color='grey', linewidth=0.8)
    ax[i].set_ylabel('Change in profitability (%)')
    ax[i].set_title(locations[i])
    ax[i].set_xticks(ind)
    ax[i].set_xticklabels(reg_variables)

  # dont need last space for graph
  ax[-1].axis('tight')
  ax[-1].axis('off')
  # legend
  lines_labels = [ax[0].get_legend_handles_labels()]
  lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
  fig.legend(lines, labels, loc='lower right', ncol=1)

  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "SA_results_location.png"))

  #sns.barplot(ax=ax[0],data=high_df, x='variable', y='ddNPV', hue='location', errorbar='sd', errcolor='black')
  #sns.barplot(ax=ax[1],data=low_df, x='variable', y='ddNPV', hue='location', errorbar='sd', errcolor='black')
  #print(high_df)
  #test_df.plot(ax = ax[0], kind = "bar",stacked=True, x='variable',y = 'ddNPV', legend = False) 
  #ax[0].errorbar(x=test_df['variable'], y=test_df['ddNPV'],  yerr = test_df['sd ddNPV'], 
  #            linewidth = 1, color = "black", capsize = 2, fmt='none')
  #plt.show()



def main():
  # Create dataframe with columns location, sensitivity, variable, delta NPV, std delta NPV
  loc_dic_reg, loc_dic_w = load_SA_results()
  print(loc_dic_w)
  plot_SA_location(loc_dic_reg)
  # Plot results 2 subplots, 1 high values, 1 low values, x axis variables, y axis delta NPV, colors for location

if __name__ == "__main__":
  main()