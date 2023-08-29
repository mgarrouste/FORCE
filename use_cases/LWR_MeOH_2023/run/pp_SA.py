import os
from gold_results import get_final_npv
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

LOCATIONS = ['braidwood', 'cooper', 'davis_besse', 'prairie_island', 'stp']
locations = ['Braidwood', 'Cooper', 'Davis-Besse', 'Prairie Island', 'South Texas Project']
locations_names = {'braidwood':'Braidwood', 'cooper':'Cooper', 'davis_besse':'Davis-Besse', 'prairie_island':'Prairie Island', 
                    'stp':'South Texas Project'}
locations_names_reg = {'braidwood':'Braidwood', 'cooper':'Cooper', 'davis_besse':'Davis-Besse', 'prairie_island':'Prairie Island'}
locations_names_stp = {'stp':'South Texas\nProject'}
REG_VARIABLES = ['capex', 'elec', 'om', 'synfuels']
reg_variables =['CAPEX', 'Electricity\nprices', 'O&M', 'Synfuels\nprices']
variables = ['CAPEX', 'Electricity\nprices', 'O&M', 'Synfuels\nprices','CO2', 'PTC']
W_VARIABLES = ['co2_high', 'co2_low', 'ptc_000', 'ptc_100', 'ptc_270']
w_variables = ['CO2', 'PTC']
total_var = W_VARIABLES+REG_VARIABLES
ptc_var = ['ptc_000', 'ptc_100', 'ptc_270']
co2_var = ['co2_low','co2_high']
toplot_var = ['ptc_000', 'ptc_100', 'ptc_270','co2_low','co2_high']
variables_names = {'co2_high':r'$CO_2 (\$60/ton)$', 'co2_low':r'$CO_2\; (\$30/ton)$', 'ptc_000':r'$PTC\; (\$0/kg-H_2)$',
                    'ptc_100':r'$PTC\; (\$1.0/kg-H_2)$','ptc_270':r'$PTC\; (\$2.7/kg-H_2)$', 
                    'capex':'CAPEX', 'elec':'Electricity\nprices', 'om':'O&M', 'synfuels':'Synfuels\nprices'}
total_variables = ['CO2 ($60/ton)', 'CO2 ($30/ton)', 'PTC ($0/kg-H2)','PTC ($1.0/kg-H2)','PTC ($2.7/kg-H2)', \
  'CAPEX', 'Electricity\nprices', 'O&M', 'Synfuels\nprices']

def get_final_npv(case, baseline=False):
  # Assumes sweep results csv file in gold folder and sorted
  sweep_file = os.path.join(".", case, "gold", 'sweep.csv')
  if not os.path.isfile(sweep_file):
    print('Results not found for {}'.format(case))
    return None
  df = pd.read_csv(sweep_file)
  df = df.iloc[:1,:]
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
      c_npv, c_npv_sd = get_final_npv(c)
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
  fig, axes = plt.subplots(3,2, figsize=(8,6))
  ax = fig.axes
  for i in range(len(LOCATIONS)):
    val_dic = loc_dic[LOCATIONS[i]]
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
    ax[i].set_title(locations[i])
    sns.despine(ax=ax[i], trim=True)
    

  # dont need last space for graph
  ax[-1].axis('tight')
  ax[-1].axis('off')
  # legend
  lines_labels = [ax[0].get_legend_handles_labels()]
  lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
  fig.legend(lines, labels, bbox_to_anchor=(0,1), ncol=1)

  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lwr_meoh_SA_results_location_"+type+".png"))



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
    p3 = ax.bar(ind, val_dic['ptc_000'], width, yerr=val_dic['ptc_000_sd'], label=r'$\$0/kg-H_2$')
    p4 = ax.bar(ind, val_dic['ptc_100'], width, yerr=val_dic['ptc_100_sd'], label=r'$\$1/kg-H_2$')
    p5 = ax.bar(ind, val_dic['ptc_270'], width, yerr=val_dic['ptc_270_sd'], label=r'$\$2.7/kg-H_2$')
    ax.set_xticks(ind)
    ax.set_xticklabels(w_variables[1])
  elif type=='co2':
    p7 = ax.bar(ind, val_dic['co2_cost_high'], width, yerr=val_dic['co2_cost_high_sd'], label=r'$\$60/ton-CO_2$')
    p6 = ax.bar(ind, val_dic['co2_cost_med'], width, yerr=val_dic['co2_cost_med_sd'], label=r'$\$30/ton-CO_2$')
    ax.set_xticks(ind)
    ax.set_xticklabels(w_variables[0])
  ax.axhline(0, color='grey', linewidth=0.8)
  ax.set_ylabel('Change in profitability (%)')
  ax.set_title(locations_names[location])
  sns.despine(ax=ax, trim=True)
  
  # legend
  lines_labels = [ax.get_legend_handles_labels()]
  lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
  fig.legend(lines, labels, bbox_to_anchor=(1,1), ncol=1)

  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lwr_meoh_SA_results_location_"+location+'_'+type+".png"))

def plot_SA_variable_v2(var_dic):
  ptc_df = pd.DataFrame()
  co2_df = pd.DataFrame()
  for var in ptc_var:
    val_dic = var_dic[var]
    ptc_df[var+'_value'] = val_dic['value']
    ptc_df[var+'_sd'] =val_dic['sd']
  for var in co2_var:
    val_dic = var_dic[var]
    co2_df[var+'_value'] = val_dic['value']
    co2_df[var+'_sd'] =val_dic['sd']

  plt.style.use('seaborn-paper')
  fig, ax = plt.subplots(2,1, sharex=True)# figsize=(10,8))
  
  # Error bars
  yerr_ptc = ptc_df[['ptc_000_sd', 'ptc_100_sd', 'ptc_270_sd']].to_numpy().T
  yerr_co2 = co2_df[['co2_low_sd', 'co2_high_sd']].to_numpy().T

  # PTC first
  ptc_df.plot(ax = ax[0], kind = "bar", y =['ptc_000_value', 'ptc_100_value', 'ptc_270_value'], 
              yerr=yerr_ptc , width=0.3, color=['red', 'orange', 'green'], error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
  ax[0].set_xticks(np.arange(len(list(locations_names.keys()))))
  ax[0].set_xticklabels(locations_names.values(), rotation=0)
  ax[0].set_ylabel('Change in profitability (%)')
  ax[0].set_xlabel('')
  ax[0].legend( [r'$PTC\; (\$0/kg-H_2)$',r'$PTC\; (\$1.0/kg-H_2)$',r'$PTC\; (\$2.7/kg-H_2)$'])

  # CO2
  co2_df.plot(ax = ax[1], kind = "bar", y =['co2_low_value', 'co2_high_value'], 
              yerr=yerr_co2, width=0.3, color=['black', 'grey'], 
              error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
  ax[1].set_xticks(np.arange(len(list(locations_names.keys()))))
  ax[1].set_xticklabels(locations_names.values(), rotation=0)
  ax[1].set_ylabel('Change in profitability (%)')
  ax[1].set_xlabel('')
  ax[1].legend( [r'$CO_2\; (\$30/ton)$', r'$CO_2 (\$60/ton)$'])

  sns.despine()
  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lwr_meoh_SA_results_variable.png"))

def plot_SA_variable_v3(var_dic):
  ptc_df = pd.DataFrame()
  co2_df = pd.DataFrame()
  for var in ptc_var:
    val_dic = var_dic[var]
    ptc_df[var+'_value'] = val_dic['value']
    ptc_df[var+'_sd'] =val_dic['sd']
  for var in co2_var:
    val_dic = var_dic[var]
    co2_df[var+'_value'] = val_dic['value']
    co2_df[var+'_sd'] =val_dic['sd']


  ptc_df_stp = ptc_df.iloc[-1,:].to_frame().transpose()
  co2_df_stp = co2_df.iloc[-1,:].to_frame().transpose()
  ptc_df.drop(index=4, inplace=True)
  co2_df.drop(index=4, inplace=True)
  
  plt.style.use('seaborn-paper')

  # create the subfigures and subplots
  fig = plt.figure(figsize=(8, 6), constrained_layout=True)
  subfigs = fig.subfigures(1, 2, width_ratios=[4, 1.25], wspace=.05)

  # Reg locations
  ax = subfigs[0].subplots(2, 1, sharex=True)
  # Error bars
  yerr_ptc = ptc_df[['ptc_000_sd', 'ptc_100_sd', 'ptc_270_sd']].to_numpy().T
  yerr_co2 = co2_df[['co2_low_sd', 'co2_high_sd']].to_numpy().T

  # PTC first
  ptc_df.plot(ax = ax[0], kind = "bar", y =['ptc_000_value', 'ptc_100_value', 'ptc_270_value'], 
              yerr=yerr_ptc , width=0.3, color=['red', 'orange', 'green'], error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
  ax[0].set_xticks(np.arange(len(list(locations_names_reg.keys()))))
  ax[0].set_xticklabels(locations_names_reg.values(), rotation=0)
  ax[0].set_ylabel('Change in profitability (%)')
  ax[0].set_xlabel('')
  ax[0].legend( [r'$PTC\; (\$0/kg-H_2)$',r'$PTC\; (\$1.0/kg-H_2)$',r'$PTC\; (\$2.7/kg-H_2)$'])

  # CO2
  co2_df.plot(ax = ax[1], kind = "bar", y =['co2_low_value', 'co2_high_value'], 
              yerr=yerr_co2, width=0.3, color=['black', 'grey'], 
              error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
  ax[1].set_xticks(np.arange(len(list(locations_names_reg.keys()))))
  ax[1].set_xticklabels(locations_names_reg.values(), rotation=0)
  ax[1].set_ylabel('Change in profitability (%)')
  ax[1].set_xlabel('')
  ax[1].legend( [r'$CO_2\; (\$30/ton)$', r'$CO_2 (\$60/ton)$'])
  sns.despine()


  # STP
  ax_stp = subfigs[1].subplots(2, 1, sharex=True)
  # Error bars
  yerr_ptc_stp = ptc_df_stp[['ptc_000_sd', 'ptc_100_sd', 'ptc_270_sd']].to_numpy().T
  yerr_co2_stp = co2_df_stp[['co2_low_sd', 'co2_high_sd']].to_numpy().T

  # PTC first
  ptc_df_stp.plot(ax = ax_stp[0], kind = "bar", y =['ptc_000_value', 'ptc_100_value', 'ptc_270_value'], 
              yerr=yerr_ptc_stp , width=0.3, color=['red', 'orange', 'green'], error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
  ax_stp[0].set_xticks(np.arange(len(list(locations_names_stp.keys()))))
  ax_stp[0].set_xticklabels(locations_names_stp.values(), rotation=0)
  ax_stp[0].set_ylabel('Change in profitability (%)')
  ax_stp[0].set_xlabel('')
  ax_stp[0].get_legend().remove()
  #ax_stp[0].legend( [r'$PTC\; (\$0/kg-H_2)$',r'$PTC\; (\$1.0/kg-H_2)$',r'$PTC\; (\$2.7/kg-H_2)$'])

  # CO2
  co2_df_stp.plot(ax = ax_stp[1], kind = "bar", y =['co2_low_value', 'co2_high_value'], 
              yerr=yerr_co2_stp, width=0.3, color=['black', 'grey'], 
              error_kw=dict(ecolor='black',elinewidth=1, capthick=1, capsize=3))
  ax_stp[1].set_xticks(np.arange(len(list(locations_names_stp.keys()))))
  ax_stp[1].set_xticklabels(locations_names_stp.values(), rotation=0)
  ax_stp[1].set_ylabel('Change in profitability (%)')
  ax_stp[1].set_xlabel('')
  ax_stp[1].get_legend().remove()
  #ax_stp[1].legend( [r'$CO_2\; (\$30/ton)$', r'$CO_2 (\$60/ton)$'])
  sns.despine()

  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lwr_meoh_SA_results_variable.png"))


def plot_SA_variable(var_dic):
  plt.style.use('seaborn-paper')
  fig, axes = plt.subplots(2,3)#, figsize=(12,10))
  ax = fig.axes 
  
  for i in range(len(toplot_var)):
    var = toplot_var[i]
    val_dic = var_dic[var]
    ind = np.arange(len(LOCATIONS))
    width = 0.35
    ax[i].bar(ind, val_dic['value'], width, yerr=val_dic['sd'])

    ax[i].set_ylabel('Change in\nprofitability (%)')
    ax[i].set_title(variables_names[var])
    ax[i].set_xticks(ind)
    ax[i].set_xticklabels(locations, rotation=50)
    sns.despine(ax=ax[i], trim=True)
  # dont need last space for graph
  ax[-1].axis('tight')
  ax[-1].axis('off')
  # legend
  lines_labels = [ax[-1].get_legend_handles_labels()]
  lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
  fig.legend(lines, labels, loc='lower right', ncol=1)
  fig.tight_layout()
  fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lwr_meoh_SA_results_variable.png"))




def main():
  # Create dataframe with columns location, sensitivity, variable, delta NPV, std delta NPV
  loc_dic, var_dic = load_SA_results_loc()
  plot_SA_locations(loc_dic)
  plot_SA_one_location(loc_dic, location='stp',type='regular')
  plot_SA_variable_v3(var_dic)

if __name__ == "__main__":
  main()