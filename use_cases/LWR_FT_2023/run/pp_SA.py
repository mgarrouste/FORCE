import pandas as pd
import seaborn as sns
import os
from gold_results import get_final_npv
import numpy as np
import matplotlib.pyplot as plt

LOCATIONS = ['braidwood', 'cooper', 'davis_besse', 'prairie_island', 'stp']
locations = ['Braidwood', 'Cooper', 'Davis-Besse', 'Prairie Island', 'South Texas Project']
REG_VARIABLES = ['capex', 'elec', 'om', 'synfuels']
reg_variables =['CAPEX', 'Electricity prices', 'O&M', 'Synfuels prices']
variables = ['CAPEX', 'Electricity prices', 'O&M', 'Synfuels prices','CO2', 'PTC']
W_VARIABLES = ['co2_cost_high', 'co2_cost_med', 'ptc_000', 'ptc_100', 'ptc_270']
w_variables = ['CO2', 'PTC']
total_var = W_VARIABLES+REG_VARIABLES
total_variables = ['CO2 ($60/kg)', 'CO2 ($30/kg)', 'PTC ($0/kg-H2)','PTC ($2.7/kg-H2)','PTC ($3/kg-H2)', \
  'CAPEX', 'Electricity prices', 'O&M', 'Synfuels prices']

def load_SA_results_loc(): 
  dir = os.path.dirname(os.path.abspath(__file__))
  # for each variable and each location compute delta NPV and sd delta NPV
  loc_dic_reg = {}
  var_dic ={}
  for v in REG_VARIABLES:
    var_dic[v] = {'low':[], 'low_sd':[], 'high':[], 'high_sd':[]}
  for v in W_VARIABLES:
    var_dic[v] = {'value':[], 'sd':[]}
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
      low_values.append(low_ddNPV)
      low_values_sd.append(low_ddNPV_sd)
      high_values.append(high_ddNPV)
      high_values_sd.append(high_ddNPV_sd)
      var_dic[v]['low'].append(low_ddNPV)
      var_dic[v]['high'].append(high_ddNPV)
      var_dic[v]['low_sd'].append(low_ddNPV_sd)
      var_dic[v]['high_sd'].append(high_ddNPV_sd)
    loc_dic_reg[loc] = {'low_values':low_values+[0,0],
                    'low_values_sd':low_values_sd+[0,0], 
                    'high_values':high_values+[0,0], 
                    'high_values_sd':high_values_sd+[0,0]}
    for v in W_VARIABLES: 
      c = os.path.join(dir,loc+'_'+v)
      c_npv, c_npv_sd = get_final_npv(c)
      ddNPV = (c_npv-ref_npv)*100/(ref_npv-baseline_npv)
      ddNPV_sd = 2*100*np.sqrt((c_npv_sd/c_npv)**2 + 2*(ref_npv_sd/ref_npv)**2 + (baseline_npv_sd/baseline_npv)**2)
      var_dic[v]['value'].append(ddNPV)
      var_dic[v]['sd'].append(ddNPV_sd)
      if 'co2' in c:
        loc_dic_reg[loc][v] = [0 for i in range(len(REG_VARIABLES))]+[ddNPV, 0]
        loc_dic_reg[loc][v+'_sd'] = [0 for i in range(len(REG_VARIABLES))]+[ddNPV_sd, 0]
      else:
        loc_dic_reg[loc][v] = [0 for i in range(len(REG_VARIABLES))]+[0,ddNPV]
        loc_dic_reg[loc][v+'_sd'] = [0 for i in range(len(REG_VARIABLES))]+[0,ddNPV_sd]
  return loc_dic_reg, var_dic


def plot_SA_locations(loc_dic): 

  plt.style.use('ggplot')
  fig, axes = plt.subplots(3,2, figsize=(12,10))
  ax = fig.axes
  for i in range(len(LOCATIONS)):
    val_dic = loc_dic[LOCATIONS[i]]
    ind = np.arange(len(val_dic['low_values']))
    width=0.35
    p1 = ax[i].bar(ind, val_dic['low_values'], width, yerr=val_dic['low_values_sd'], label='Low (Ref x0.75)')
    p2 = ax[i].bar(ind, val_dic['high_values'], width, yerr=val_dic['high_values_sd'], label='High (Ref x1.25)')
    p3 = ax[i].bar(ind, val_dic['ptc_000'], width, yerr=val_dic['ptc_000_sd'], label='$0/kg-H2')
    p4 = ax[i].bar(ind, val_dic['ptc_100'], width, yerr=val_dic['ptc_100_sd'], label='$1/kg-H2')
    p5 = ax[i].bar(ind, val_dic['ptc_270'], width, yerr=val_dic['ptc_270_sd'], label='$2.7/kg-H2')
    p7 = ax[i].bar(ind, val_dic['co2_cost_high'], width, yerr=val_dic['co2_cost_high_sd'], label='$60/kg-CO2')
    p6 = ax[i].bar(ind, val_dic['co2_cost_med'], width, yerr=val_dic['co2_cost_med_sd'], label='$30/kg-CO2')
    ax[i].axhline(0, color='grey', linewidth=0.8)
    ax[i].set_ylabel('Change in profitability (%)')
    ax[i].set_title(locations[i])
    ax[i].set_xticks(ind)
    ax[i].set_xticklabels(variables)

  # dont need last space for graph
  ax[-1].axis('tight')
  ax[-1].axis('off')
  # legend
  lines_labels = [ax[0].get_legend_handles_labels()]
  lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
  fig.legend(lines, labels, loc='lower right', ncol=1)

  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "SA_results_location.png"))

def plot_SA_variable(var_dic):
  plt.style.use('ggplot')
  fig, axes = plt.subplots(3,3, figsize=(12,10))
  ax = fig.axes 
  
  for i in range(len(total_var)):
    var = total_var[i]
    val_dic = var_dic[var]
    ind = np.arange(len(LOCATIONS))
    width = 0.35
    
    if ('co2' in var) or ('ptc' in var):
      ax[i].bar(ind, val_dic['value'], width, yerr=val_dic['sd'])
    else:
      ax[i].bar(ind, val_dic['low'], width, yerr=val_dic['low_sd'], label='Low (Ref x0.75)')
      ax[i].bar(ind, val_dic['high'], width, yerr=val_dic['high_sd'], label='High (Ref x1.25)')
    ax[i].axhline(0, color='grey', linewidth=0.8)
    ax[i].set_ylabel('Change in profitability (%)')
    ax[i].set_title(total_variables[i])
    ax[i].set_xticks(ind)
    ax[i].set_xticklabels(locations, rotation=50)

  # legend
  lines_labels = [ax[-1].get_legend_handles_labels()]
  lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
  fig.legend(lines, labels, loc='lower right', ncol=1)
  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "SA_results_variable.png"))




def main():
  # Create dataframe with columns location, sensitivity, variable, delta NPV, std delta NPV
  loc_dic, var_dic = load_SA_results_loc()
  plot_SA_locations(loc_dic)
  plot_SA_variable(var_dic)

if __name__ == "__main__":
  main()