import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from matplotlib.ticker import MultipleLocator

locations_names = {'illinois':'Illinois', 'minnesota':'Minnesota', 'nebraska':'Nebraska', 'ohio':'Ohio', 
                    'texas':'Texas'}
REG_VARIABLES = ['capex', 'elec', 'om', 'synfuels']
reg_variables =['CAPEX', 'Electricity\nprices', 'O&M', 'Synfuels\nprices']
variables = ['CAPEX', 'Electricity\nprices', 'O&M', 'Synfuels\nprices','CO2', 'PTC']
W_VARIABLES = ['co2_high', 'co2_low', 'ptc_000', 'ptc_100', 'ptc_270', 'smr_40', 'smr_80']
w_variables = ['CO2', 'PTC']
total_var = W_VARIABLES+REG_VARIABLES
size_var = ['smr_40', 'smr_80']
ptc_var = ['ptc_000', 'ptc_100', 'ptc_270']
co2_var = ['co2_low','co2_high']
toplot_var = ['ptc_000', 'ptc_100', 'ptc_270','co2_low','co2_high']
variables_names = {'co2_high':r'$CO_2 (\$60/ton)$', 'co2_low':r'$CO_2\; (\$30/ton)$', 'ptc_000':r'$PTC\; (\$0/kg-H_2)$',
                    'ptc_100':r'$PTC\; (\$1.0/kg-H_2)$','ptc_270':r'$PTC\; (\$2.7/kg-H_2)$', 
                    'capex':'CAPEX', 'elec':'Electricity\nprices', 'om':'O&M', 'synfuels':'Synfuels\nprices'}
total_variables = ['CO2 ($60/ton)', 'CO2 ($30/ton)', 'PTC ($0/kg-H2)','PTC ($1.0/kg-H2)','PTC ($2.7/kg-H2)', \
  'CAPEX', 'Electricity\nprices', 'O&M', 'Synfuels\nprices']
BASELINE_SMR_CAP_REF = 720


def get_optimal_point(location):
  results_df = pd.read_csv('smr_meoh_results.csv')
  results_df = results_df[results_df['location'] == location]
  results_df = results_df[['htse_capacity', 'meoh_capacity', 'h2_storage_capacity']]
  results_df = results_df.to_dict(orient='records')[0]
  return results_df

def get_final_npv(case, baseline=False, opt_point={}, baseline_cap=BASELINE_SMR_CAP_REF):
  # Assumes sweep results csv file in gold folder and sorted
  sweep_file = os.path.join(".", case, "gold", 'sweep.csv')
  if not os.path.isfile(sweep_file):
    print('Results not found for {}'.format(case))
    return None
  df = pd.read_csv(sweep_file)
  if not baseline and not opt_point:
    df = df.iloc[:1,:]
  else:
    df = df[df['smr_capacity']==baseline_cap]
  if opt_point:
    for comp_name, comp_capacity in opt_point.items():
      df = df[np.round(df[comp_name]) == np.round(comp_capacity)]
  if df.empty:
    print('df empty')
    print(case)
    print(opt_point)
    print(pd.read_csv(sweep_file)[['htse_capacity', 'meoh_capacity', 'h2_storage_capacity']])
  final_npv = float(df.mean_NPV.to_list()[0])
  std_npv = float(df.std_NPV.to_list()[0])
  return final_npv, std_npv

def load_SA_results_loc(): 
  dir = os.path.dirname(os.path.abspath(__file__))
  # for each variable and each location compute delta NPV and sd delta NPV
  loc_dic_reg = {}
  var_dic ={}
  for v in REG_VARIABLES:
    var_dic[v] = {'low':[], 'low_sd':[], 'high':[], 'high_sd':[]}
  for v in W_VARIABLES:
    var_dic[v] = {'value':[], 'sd':[]}
  for loc in locations_names.keys(): 
    baseline = os.path.join(dir, loc+'_baseline')
    baseline_npv, baseline_npv_sd = get_final_npv(baseline, baseline=True)
    ref = os.path.join(dir, loc+'_reduced_8')
    ref_npv, ref_npv_sd = get_final_npv(ref)
    low_values = []
    high_values = []
    low_values_sd = []
    high_values_sd = []
    opt_point = get_optimal_point(location=loc)
    for v in REG_VARIABLES: 
      low_case = os.path.join(dir,loc+'_'+v+'_0.75')
      high_case = os.path.join(dir,loc+'_'+v+'_1.25')
      low_npv, low_npv_sd = get_final_npv(low_case, opt_point=opt_point)
      high_npv, high_npv_sd = get_final_npv(high_case, opt_point=opt_point)
      low_ddNPV = (low_npv-ref_npv)*100/np.abs(ref_npv-baseline_npv)
      low_ddNPV_sd = 2*100*np.sqrt((low_npv_sd/low_npv)**2 + 2*(ref_npv_sd/ref_npv)**2 + (baseline_npv_sd/baseline_npv)**2)
      high_ddNPV = (high_npv-ref_npv)*100/np.abs(ref_npv-baseline_npv)
      high_ddNPV_sd = 2*100*np.sqrt((high_npv_sd/high_npv)**2 + 2*(ref_npv_sd/ref_npv)**2 + (baseline_npv_sd/baseline_npv)**2)
      low_values.append(low_ddNPV)
      low_values_sd.append(low_ddNPV_sd)
      high_values.append(high_ddNPV)
      high_values_sd.append(high_ddNPV_sd)
      var_dic[v]['low'].append(low_ddNPV)
      var_dic[v]['high'].append(high_ddNPV)
      var_dic[v]['low_sd'].append(low_ddNPV_sd)
      var_dic[v]['high_sd'].append(high_ddNPV_sd)
    loc_dic_reg[loc] = {'low_values':low_values,
                    'low_values_sd':low_values_sd, 
                    'high_values':high_values, 
                    'high_values_sd':high_values_sd}
    for v in W_VARIABLES: 
      c = os.path.join(dir,loc+'_'+v)
      print(c)
      c_npv, c_npv_sd = get_final_npv(c)
      if 'smr_40' in v:
        baseline_npv, baseline_npv_sd = get_final_npv(baseline, baseline=True, baseline_cap=480)
      elif 'smr_80' in v: 
        baseline_npv, baseline_npv_sd = get_final_npv(baseline, baseline=True, baseline_cap=960)
      ddNPV = (c_npv-ref_npv)*100/np.abs(ref_npv-baseline_npv)
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


def plot_SA_locations(loc_dic, type='regular'): 

  plt.style.use('seaborn-paper')
  fig, axes = plt.subplots(5,1, figsize=(4,9), sharex=True)
  ax = fig.axes
  i=0
  for loc, loc_name in locations_names.items():
    val_dic = loc_dic[loc]
    ind = np.arange(len(val_dic['low_values']))
    width=0.35
    if type=='regular': 
      p1 = ax[i].bar(ind, val_dic['low_values'], width, yerr=val_dic['low_values_sd'], label='Low (Ref x0.75)', 
      error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
      p2 = ax[i].bar(ind, val_dic['high_values'], width, yerr=val_dic['high_values_sd'], label='High (Ref x1.25)', 
      error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
      ax[i].set_xticks(ind)
      ax[i].set_xticklabels(reg_variables)
    elif type=='ptc':
      p3 = ax[i].bar(ind, val_dic['ptc_000'], width, yerr=val_dic['ptc_000_sd'], label=r'$\$0/kg-H_2$')
      p4 = ax[i].bar(ind, val_dic['ptc_100'], width, yerr=val_dic['ptc_100_sd'], label=r'$\$1/kg-H_2$')
      p5 = ax[i].bar(ind, val_dic['ptc_270'], width, yerr=val_dic['ptc_270_sd'], label=r'$\$2.7/kg-H_2$')
      ax.set_xticks(ind)
      ax.set_xticklabels(w_variables[1])
    elif type=='co2':
      p7 = ax[i].bar(ind, val_dic['co2_cost_high'], width, yerr=val_dic['co2_cost_high_sd'], label=r'$\$60/ton-CO_2$')
      p6 = ax[i].bar(ind, val_dic['co2_cost_med'], width, yerr=val_dic['co2_cost_med_sd'], label=r'$\$30/ton-CO_2$')
      ax.set_xticks(ind)
      ax.set_xticklabels(w_variables[0])
    ax[i].axhline(0, color='grey', linewidth=0.8)
    ax[i].set_ylabel('Change in\nprofitability (%)')
    ax[i].set_title(loc_name)
    ax[i].yaxis.set_major_locator(MultipleLocator(25))
    ax[i].set_ylim(-100,100)
    sns.despine(ax=ax[i], trim=True)
    i+=1
    
  # legend
  lines_labels = [ax[0].get_legend_handles_labels()]
  lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
  fig.legend(lines, labels, ncol=1, loc='upper left')

  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "smr_meoh_SA_results_location_"+type+".png"))



def plot_SA_one_location(loc_dic, location, type='regular'):

  plt.style.use('seaborn-paper')
  fig, ax = plt.subplots()

  val_dic = loc_dic[location]
  ind = np.arange(len(val_dic['low_values']))
  width=0.35
  if type=='regular': 
    p1 = ax.bar(ind, val_dic['low_values'], width, yerr=val_dic['low_values_sd'], label='Low (Ref x0.75)', 
    error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
    p2 = ax.bar(ind, val_dic['high_values'], width, yerr=val_dic['high_values_sd'], label='High (Ref x1.25)', 
    error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
    ax.set_xticks(ind)
    ax.set_xticklabels(reg_variables)
  elif type=='ptc':
    p3 = ax.bar(ind, val_dic['ptc_000'], width, yerr=val_dic['ptc_000_sd'], capsize=2, ecolor='black', error_kw={'markeredgewidth':1},label=r'$\$0/kg-H_2$')
    p4 = ax.bar(ind, val_dic['ptc_100'], width, yerr=val_dic['ptc_100_sd'], capsize=2, ecolor='black', error_kw={'markeredgewidth':1},label=r'$\$1/kg-H_2$')
    p5 = ax.bar(ind, val_dic['ptc_270'], width, yerr=val_dic['ptc_270_sd'], capsize=2, ecolor='black', error_kw={'markeredgewidth':1},label=r'$\$2.7/kg-H_2$')
    ax.set_xticks(ind)
    ax.set_xticklabels(w_variables[1])
  elif type=='co2':
    p7 = ax.bar(ind, val_dic['co2_cost_high'], width, yerr=val_dic['co2_cost_high_sd'], capsize=2, ecolor='black', error_kw={'markeredgewidth':1},label=r'$\$60/ton-CO_2$')
    p6 = ax.bar(ind, val_dic['co2_cost_med'], width, yerr=val_dic['co2_cost_med_sd'],capsize=2, ecolor='black', error_kw={'markeredgewidth':1}, label=r'$\$30/ton-CO_2$')
    ax.set_xticks(ind)
    ax.set_xticklabels(w_variables[0])
  ax.axhline(0, color='grey', linewidth=0.8)
  ax.set_ylabel('Change in profitability (%)')
  ax.set_title(locations_names[location])
  sns.despine(ax=ax)
  
  # legend
  lines_labels = [ax.get_legend_handles_labels()]
  lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
  fig.legend(lines, labels, bbox_to_anchor=(1,1), ncol=1)

  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "smr_meoh_SA_results_location_"+location+'_'+type+".png"))


def plot_SA_variable_v2(var_dic):
  ptc_df = pd.DataFrame()
  co2_df = pd.DataFrame()
  size_df = pd.DataFrame()

  for var in ptc_var:
    val_dic = var_dic[var]
    ptc_df[var+'_value'] = val_dic['value']
    ptc_df[var+'_sd'] =val_dic['sd']
  for var in co2_var:
    val_dic = var_dic[var]
    co2_df[var+'_value'] = val_dic['value']
    co2_df[var+'_sd'] =val_dic['sd']
  for var in size_var:
    val_dic = var_dic[var]
    size_df[var+'_value'] = val_dic['value']
    size_df[var+'_sd'] =val_dic['sd']

  plt.style.use('seaborn-paper')
  fig, ax = plt.subplots(3,1, sharex=True)# figsize=(10,8))
  
  # Error bars
  yerr_ptc = ptc_df[['ptc_000_sd', 'ptc_100_sd', 'ptc_270_sd']].to_numpy().T
  yerr_co2 = co2_df[['co2_low_sd', 'co2_high_sd']].to_numpy().T
  yerr_size = size_df[['smr_40_sd', 'smr_80_sd']].to_numpy().T

  # PTC first
  ptc_df.plot(ax = ax[0], kind = "bar", y =['ptc_000_value', 'ptc_100_value', 'ptc_270_value'], 
              yerr=yerr_ptc , width=0.3, color=['red', 'orange', 'green'], error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
  ax[0].set_xticks(np.arange(len(list(locations_names.keys()))))
  ax[0].set_xticklabels(locations_names.values(), rotation=0)
  ax[0].set_ylabel('Change in \nprofitability (%)')
  ax[0].set_xlabel('')
  ax[0].legend( [r'$PTC\; (\$0/kg-H_2)$',r'$PTC\; (\$1.0/kg-H_2)$',r'$PTC\; (\$2.7/kg-H_2)$'], bbox_to_anchor=(1,1))
  ax[0].yaxis.set_major_locator(MultipleLocator(100))
  ax[0].set_ylim(-400,0)

  # CO2
  co2_df.plot(ax = ax[1], kind = "bar", y =['co2_high_value', 'co2_low_value'], 
              yerr=yerr_co2, width=0.3, color=['black', 'grey'], 
              error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
  ax[1].set_xticks(np.arange(len(list(locations_names.keys()))))
  ax[1].set_xticklabels(locations_names.values(), rotation=0)
  ax[1].set_ylabel('Change in \nprofitability (%)')
  ax[1].set_xlabel('')
  ax[1].legend( [r'$CO_2 (\$60/ton)$', r'$CO_2\; (\$30/ton)$'], bbox_to_anchor=(1,1))
  ax[1].yaxis.set_major_locator(MultipleLocator(50))
  ax[1].set_ylim(-100,0)

  # Size of module
  size_df.plot(ax = ax[2], kind = "bar", y =['smr_40_value', 'smr_80_value'], 
              yerr=yerr_size, width=0.3, color=['blue', 'pink'], 
              error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
  ax[2].set_xticks(np.arange(len(list(locations_names.keys()))))
  ax[2].set_xticklabels(locations_names.values(), rotation=0)
  #ax[2].set_yscale('log')
  ax[2].set_ylabel('Change in \nprofitability (%)')
  ax[2].set_xlabel('')
  ax[2].legend( ['Module size 40MWe', 'Module size 80MWe'], bbox_to_anchor=(1,1))
  ax[2].yaxis.set_major_locator(MultipleLocator(25))
  ax[2].set_ylim(-50,50)

  sns.despine()
  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "smr_meoh_SA_results_variable.png"))




def main():
  # Create dataframe with columns location, sensitivity, variable, delta NPV, std delta NPV
  loc_dic, var_dic = load_SA_results_loc()
  plot_SA_locations(loc_dic)
  plot_SA_one_location(loc_dic, location='texas',type='regular')
  plot_SA_variable_v2(var_dic)

if __name__ == "__main__":
  main()