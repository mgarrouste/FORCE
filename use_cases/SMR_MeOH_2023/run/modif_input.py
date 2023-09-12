import argparse, os, glob, shutil
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

ITC_VALUE = 0.7
STORAGE_INIT = 0.0 # 1% filled at the beginning of the day
MACRS = 15
SMR_VOM = -23.2
locations  = ['illinois', 'minnesota', 'nebraska', 'ohio', 'texas']
steps_data = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'data', 'HERON_model_data.xlsx')

def itc(case):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')

  for comp in root.findall('Component'):
    if comp.get('name') == 'smr':
      comp = comp.find('economics')
      for cash in comp.findall('CashFlow'):
        if cash.get('name') == 'smrCAPEX':
          ref_price = cash.find('reference_price')
          mult = ET.Element('multiplier')
          mult.text = str(ITC_VALUE)
          ref_price.append(mult)
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)


def delete_double_itc(case):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')

  for comp in root.findall('Component'):
    if comp.get('name') == 'smr':
      comp = comp.find('economics')
      for cash in comp.findall('CashFlow'):
        if cash.get('name') == 'smrCAPEX':
          ref_price = cash.find('reference_price')
          mult = ref_price.findall('multiplier')
          for m in mult:
            if m.text =='0.7':
              ref_price.remove(m)
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)


def init_storage(case):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')

  for comp in root.findall('Component'):
    if comp.get('name') == 'h2_storage':
      init = comp.find('stores').find('initial_stored').find('fixed_value')
      init.text = str(STORAGE_INIT)
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)

def arma_samples(case, number=2):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Case')

  num_arma = root.find('num_arma_samples')
  num_arma.text = str(number)

  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)


def meoh_ratios(case):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')

  #Ratios from updated MeOH data in HERON_info.xlsx
  h2 = -1.0
  co2 = -5.9316
  electricity = -0.0004
  naphtha = 0.0923
  jet_fuel = 0.4135
  diesel = 1.6097

  for comp in root.findall('Component'):
    if comp.get('name') =='meoh':
      linear = comp.find('produces').find('transfer').find('linear')
      rate_nodes = linear.findall('rate')
      
      add_elec = True
      for rate in rate_nodes:
        if rate.get('resource') == 'electricity':
          add_elec = False
        if rate.get('resource') == 'h2':
          rate.text = str(h2)
        elif rate.get('resource') == 'naphtha':
          rate.text = str(naphtha)
        elif rate.get('resource') == 'jet_fuel':
          rate.text = str(jet_fuel)
        elif rate.get('resource') == 'diesel':
          rate.text = str(diesel)
      
      # Add electricity
      if add_elec:
        mult = ET.SubElement(linear, 'rate', resource='electricity')
        mult.text = str(electricity)

  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)


def sweep_values_htse(case):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')

  htse_df = pd.read_excel(steps_data, sheet_name='HTSE_steps')

  case_name = case.split('/')[-1]

  # SA
  SA = True
  if 'smr_20' in case_name: 
    size = 20
  elif 'smr_100' in case_name:
    size = 100
  elif 'smr' in case_name:
    size = 60
    SA = False
  elif 'baseline' in case_name:
    SA = False
    size = 60
  else: 
    size = 60 

  if SA: 
    sweep_values_df = htse_df[htse_df['size']==size].drop(columns=['size'])
    sweep_values = np.round(list(sweep_values_df.iloc[0,[0,2,4,6,8]]))
  else: 
    sweep_values_df = htse_df[htse_df['size']==size].drop(columns=['size'])
    sweep_values = np.round(list(sweep_values_df.iloc[0,:]))
  sweep_values = [str(v) for v in sweep_values]
  sweep_values = ','.join(sweep_values)

  for comp in root.findall('Component'):
    if comp.get('name') =='htse':
      sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
      sweep_val_node.text = sweep_values
      
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)


def sweep_values_meoh(case):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')

  meoh_df = pd.read_excel(steps_data, sheet_name='MeOH_steps')

  case_name = case.split('/')[-1]

  # SA
  SA = True
  if 'smr_20' in case_name: 
    size = 20
  elif 'smr_100' in case_name:
    size = 100
  elif 'smr' in case_name:
    size = 60
    SA = False
  elif 'baseline' in case_name:
    SA = False
    size = 60
  else: 
    size = 60 

  if SA: 
    sweep_values_df = meoh_df[meoh_df['size']==size].drop(columns=['size'])
    sweep_values = np.round(list(sweep_values_df.iloc[0,[0,2,4,6,8]]))
  else: 
    sweep_values_df = meoh_df[meoh_df['size']==size].drop(columns=['size'])
    sweep_values = np.round(list(sweep_values_df.iloc[0,:]))
  sweep_values = [str(v) for v in sweep_values]
  sweep_values = ','.join(sweep_values)

  for comp in root.findall('Component'):
    if comp.get('name') =='meoh':
      sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
      sweep_val_node.text = sweep_values
      
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)

def sweep_values_storage(case): 
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')
  storage_df = pd.read_excel(steps_data, sheet_name='storage_steps')
  case_name = case.split('/')[-1]
  location = case.split('/')[-1].split('_')[0]

  # SA
  SA = True
  if 'smr_20' in case_name: 
    size = 20
  elif 'smr_100' in case_name:
    size = 100
  elif 'smr' in case_name:
    size = 60
    SA = False
  elif 'baseline' in case_name:
    SA = False
    size = 60
  else: 
    size = 60 

  if SA: 
    sweep_values_df = storage_df[(storage_df['location']==location)&(storage_df['size']==size)].drop(columns=['location', 'size'])
    sweep_values = np.round(list(sweep_values_df.iloc[0,[0,2,4,6,8]]))
  else: 
    sweep_values_df = storage_df[(storage_df['location']==location)&(storage_df['size']==size)].drop(columns=['location', 'size'])
    sweep_values = np.round(list(sweep_values_df.iloc[0,:]))
  sweep_values = [str(v) for v in sweep_values]
  sweep_values = ','.join(sweep_values)

  for comp in root.findall('Component'):
    if comp.get('name') =='h2_storage':
      sweep_val_node = comp.find('stores').find('capacity').find('sweep_values')
      sweep_val_node.text = sweep_values
      
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)

def add_elec_consumption_meoh(case):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')

  for comp in root.findall('Component'):
    if comp.get('name') =='meoh':
      consumes_node = comp.find('produces').find('consumes')
      consumes_node.text = 'h2,electricity'
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)

def add_depreciation(case):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')
  for comp in root.findall('Component'):
    if comp.get('name') == 'smr':
      cash = comp.find('economics').findall('CashFlow')
      for c in cash:
        if c.get('name')=='smrCAPEX':
          mult = ET.SubElement(c, 'depreciate')
          mult.text = str(MACRS)
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)

def create_reduced_inputs(number): 
  dir = os.path.dirname(os.path.abspath(__file__))
  for loc in locations: 
    # Copy heron input from smr to reduced folder
    red_fold = os.path.join(dir,loc+'_reduced'+'_'+str(number))
    if not os.path.isdir(red_fold):
      os.mkdir(os.path.join(dir,loc+'_reduced'+'_'+str(number)))
    shutil.copy(os.path.join(dir, loc+'_sweep', 'heron_input.xml'), red_fold)

    # Read steps from csv
    sheet_name = 'Boundaries_'+str(number)+'steps'
    steps_df = pd.read_excel(steps_data, sheet_name=sheet_name, nrows=number)
    htse_steps = list(steps_df['htse'])
    htse_steps = [str(np.round(v,1)) for v in htse_steps]
    htse_steps = ','.join(htse_steps)
    meoh_steps = list(steps_df['meoh'])
    meoh_steps = [str(np.round(v,1))  for v in meoh_steps]
    meoh_steps = ','.join(meoh_steps)
    h2_steps = list(steps_df[loc])
    h2_steps = [str(np.round(v))  for v in h2_steps]
    h2_steps = ','.join(h2_steps)

    # XML modif
    tree = ET.parse(os.path.join(red_fold, 'heron_input.xml'))
    root = tree.getroot().find('Components')

    for comp in root.findall('Component'):
      if comp.get('name') == 'htse':
        sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
        sweep_val_node.text = htse_steps
      elif comp.get('name') =='meoh':
        sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
        sweep_val_node.text = meoh_steps
      elif comp.get('name') =='h2_storage':
        sweep_val_node = comp.find('stores').find('capacity').find('sweep_values')
        sweep_val_node.text = h2_steps
    
    with open(os.path.join(red_fold, 'heron_input.xml'), 'wb') as f:
      tree.write(f)


def project_lifetime(case, lifetime):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Case')
  time = root.find('economics').find('ProjectTime')
  time.text =str(lifetime)
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)


def get_opt_config(location):
  """Get the optimal configuration of the location for SA inputs"""
  dir = os.path.dirname(os.path.abspath(__file__))
  sweep_results = pd.read_csv(os.path.join(dir,location+'_reduced_8', 'gold', 'sweep.csv'))
  sweep_results = sweep_results[['htse_capacity', 'meoh_capacity', 'h2_storage_capacity']].iloc[0,:]
  sweep_results = sweep_results.to_dict()
  return sweep_results


def sa_sweep_values(case):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')

  case_name = case.split('/')[-1]
  if 'davis_besse' in case_name:
    location='davis_besse'
  elif 'prairie_island' in case_name:
    location='prairie_island'
  else:
    location = case.split('/')[-1].split('_')[0]
  opt_dict = get_opt_config(location)

  for comp in root.findall('Component'):
    # Storage
    if comp.get('name') =='h2_storage':
      sweep_val_node = comp.find('stores').find('capacity').find('sweep_values')
      sweep_values = [opt_dict['h2_storage_capacity'], opt_dict['h2_storage_capacity']/2]
      sweep_values = [str(v) for v in sweep_values]
      sweep_values = ','.join(sweep_values)
      sweep_val_node.text = sweep_values
    # FT
    if comp.get('name') =='meoh':
      sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
      sweep_values = [opt_dict['meoh_capacity'], opt_dict['meoh_capacity']/2]
      sweep_values = [str(v) for v in sweep_values]
      sweep_values = ','.join(sweep_values)
      sweep_val_node.text = sweep_values
    # HTSE
    if comp.get('name') =='htse':
      sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
      sweep_values = [opt_dict['htse_capacity'], opt_dict['htse_capacity']/2]
      sweep_values = [str(v) for v in sweep_values]
      sweep_values = ','.join(sweep_values)
      sweep_val_node.text = sweep_values
  
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)

def vom_smr(case): 
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')
  for comp in root.findall('Component'):
    if comp.get('name') =='smr':
      nodes = comp.find('economics').findall('CashFlow')
      for node in nodes: 
        if node.get('name')=='smrVOM':
          refprice = node.find('reference_price').find('fixed_value')
          refprice.text = str(SMR_VOM)
  
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)


def module_sa():
  dir = os.path.dirname(os.path.abspath(__file__))
  for loc in locations: 
    module_low = os.path.join(dir, loc+'_smr_40')
    module_high = os.path.join(dir, loc+'_smr_80')

    def correct_smr_capacity(case, capacity):
      tree = ET.parse(os.path.join(case, 'heron_input.xml'))
      root = tree.getroot().find('Components')
      for comp in root.findall('Component'):
        if comp.get('name') =='smr':
          capacity_value = comp.find('produces').find('capacity').find('fixed_value')
          capacity_value.text = str(capacity)
      with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
          tree.write(f)
    correct_smr_capacity(module_low, 480)
    correct_smr_capacity(module_high, 960)

    module_dic = {module_low:'40_MWe', module_high:'80_MWe'}
    for case_name, sheet_name in module_dic.items():
      steps_df = pd.read_excel(steps_data, sheet_name=sheet_name, nrows=8)
      htse_steps = list(steps_df['htse'])
      htse_steps = [str(np.round(v,1)) for v in htse_steps]
      htse_steps = ','.join(htse_steps)
      ft_steps = list(steps_df['meoh'])
      ft_steps = [str(np.round(v,1))  for v in ft_steps]
      ft_steps = ','.join(ft_steps)
      h2_steps = list(steps_df['storage'])
      h2_steps = [str(np.round(v))  for v in h2_steps]
      h2_steps = ','.join(h2_steps)

      tree = ET.parse(os.path.join(case_name, 'heron_input.xml'))
      root = tree.getroot().find('Components')
      for comp in root.findall('Component'):
          # Storage
        if comp.get('name') =='h2_storage':
          sweep_val_node = comp.find('stores').find('capacity').find('sweep_values')
          sweep_val_node.text = h2_steps
        # FT
        if comp.get('name') =='meoh':
          sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
          sweep_val_node.text = ft_steps
        # HTSE
        if comp.get('name') =='htse':
          sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
          sweep_val_node.text = htse_steps
        with open(os.path.join(case_name, 'heron_input.xml'), 'wb') as f:
          tree.write(f)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-p', "--pattern", type=str, nargs='+', help="pattern in cases names or cases' names", required=False)
  parser.add_argument('-c', "--case", type=str, help="case", required=False)
  parser.add_argument('-r', '--reduced', type=bool, help='create reduced reference cases', required=False)
  parser.add_argument('-m', '--module', type=bool, help='Correct smr module size sa inputs', required=False )
  args = parser.parse_args()
  dir = os.path.dirname(os.path.abspath(__file__))
  if args.pattern:
    if len(args.pattern)<=1:
      cases = glob.glob(dir+"/*"+args.pattern[0]+"*")
    else: 
      cases = [os.path.join(dir, p) for p in list(args.pattern)]
  elif args.case:
    cases = [os.path.join(dir, args.case)]
  elif args.reduced:
    for number in range(5,9):
      create_reduced_inputs(number)
  elif args.module: 
    module_sa()
  else: 
    raise Exception("No case or input passed to this script!")
  if args.case or args.pattern:
    print("Cases to modify: {}\n".format(cases))
    for case in cases:
      #delete_double_itc(case)
      vom_smr(case)
      init_storage(case)
      meoh_ratios(case)
      reduced_arma_samples = True
      if '_smr' in case:
        reduced_arma_samples = False
      if 'baseline' in case:
        reduced_arma_samples = False
      if 'smr_20' in case:
        reduced_arma_samples = True
      if 'smr_100' in case:
        reduced_arma_samples = True
      if reduced_arma_samples:
        arma_samples(case)
      if (not 'reduced' in case) and (not 'sweep' in case): 
        sa_sweep_values(case)
      #add_depreciation(case)
      #add_elec_consumption_meoh(case)
      project_lifetime(case=case, lifetime=60)

      

if __name__=="__main__":
 main()
