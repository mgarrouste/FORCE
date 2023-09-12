import argparse, os, glob
import xml.etree.ElementTree as ET
import shutil
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
          mult = ET.SubElement(ref_price, 'multiplier')
          mult.text = str(ITC_VALUE)
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

def project_lifetime(case, lifetime):
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Case')
  time = root.find('economics').find('ProjectTime')
  time.text =str(lifetime)
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
    shutil.copy(os.path.join(dir, loc+'_smr', 'heron_input.xml'), red_fold)

    # Read steps from csv
    sheet_name = 'Boundaries_'+str(number)+'steps'
    steps_df = pd.read_excel(steps_data, sheet_name=sheet_name, nrows=number)
    print(steps_df)
    htse_steps = list(steps_df['htse'])
    htse_steps = [str(np.round(v,1)) for v in htse_steps]
    htse_steps = ','.join(htse_steps)
    ft_steps = list(steps_df['ft'])
    ft_steps = [str(np.round(v,1))  for v in ft_steps]
    ft_steps = ','.join(ft_steps)
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
      elif comp.get('name') =='ft':
        sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
        sweep_val_node.text = ft_steps
      elif comp.get('name') =='h2_storage':
        sweep_val_node = comp.find('stores').find('capacity').find('sweep_values')
        sweep_val_node.text = h2_steps
    
    with open(os.path.join(red_fold, 'heron_input.xml'), 'wb') as f:
      tree.write(f)

def sweep_values(case):
  case_name = case.split('/')[-1]
  tree = ET.parse(os.path.join(case, 'heron_input.xml'))
  root = tree.getroot().find('Components')

  df = pd.read_excel(steps_data, sheet_name='steps')

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
    sweep_values_htse = df[(df['component']=='htse') & (df['size']==size)].drop(columns=['component', 'size'])
    sweep_values_htse = np.round(list(sweep_values_htse.iloc[0,[0,2,4,6,8]]))
    sweep_values_ft = df[(df['component']=='ft') & (df['size']==size)].drop(columns=['component', 'size'])
    sweep_values_ft = np.round(list(sweep_values_ft.iloc[0,[0,2,4,6,8]]))
    sweep_values_storage = df[(df['component']=='storage') & (df['size']==size)].drop(columns=['component', 'size'])
    sweep_values_storage = np.round(list(sweep_values_storage.iloc[0,[0,2,4,6,8]]))
  else: 
    sweep_values_htse = df[(df['component']=='htse') & (df['size']==size)].drop(columns=['component', 'size'])
    sweep_values_htse = np.round(list(sweep_values_htse.iloc[0,:]))
    sweep_values_ft = df[(df['component']=='ft') & (df['size']==size)].drop(columns=['component', 'size'])
    sweep_values_ft = np.round(list(sweep_values_ft.iloc[0,:]))
    sweep_values_storage = df[(df['component']=='storage') & (df['size']==size)].drop(columns=['component', 'size'])
    sweep_values_storage = np.round(list(sweep_values_storage.iloc[0,:]))
  sweep_values_htse = ','.join([str(v) for v in sweep_values_htse])
  sweep_values_ft = ','.join([str(v) for v in sweep_values_ft])
  sweep_values_storage = ','.join([str(v) for v in sweep_values_storage])

  for comp in root.findall('Component'):
    if comp.get('name') =='htse':
      sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
      sweep_val_node.text = sweep_values_htse
    if comp.get('name') =='ft':
      sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
      sweep_val_node.text = sweep_values_ft
    if comp.get('name') =='h2_storage':
      sweep_val_node = comp.find('stores').find('capacity').find('sweep_values')
      sweep_val_node.text = sweep_values_storage

  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)

def get_opt_config(location):
  """Get the optimal configuration of the location for SA inputs"""
  dir = os.path.dirname(os.path.abspath(__file__))
  sweep_results = pd.read_csv(os.path.join(dir,location+'_reduced_8', 'gold', 'sweep.csv'))
  sweep_results = sweep_results[['htse_capacity', 'ft_capacity', 'h2_storage_capacity']].iloc[0,:]
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
    if comp.get('name') =='ft':
      sweep_val_node = comp.find('produces').find('capacity').find('sweep_values')
      sweep_values = [opt_dict['ft_capacity'], opt_dict['ft_capacity']/2]
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
      ft_steps = list(steps_df['ft'])
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
        if comp.get('name') =='ft':
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
  parser.add_argument('-p', "--pattern", type=str, nargs='+', required=False, help="pattern in cases names or cases' names")
  parser.add_argument('-c', "--case", type=str, help="case", required=False)
  parser.add_argument('-r', '--reduced', type=bool, help='create reduced reference cases', required=False)
  parser.add_argument('-m', '--module', type=bool, help='Correct module size SA inputs', required=False)
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
  if args.pattern or args.case:
    print("Cases to modify: {}\n".format(cases))
    for case in cases:
      vom_smr(case)
      init_storage(case)
      project_lifetime(case, lifetime=60)
      if (not 'reduced' in case) and (not 'sweep' in case): 
        sa_sweep_values(case)
      #add_depreciation(case)
      


if __name__=="__main__":
 main()
