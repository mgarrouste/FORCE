import argparse, os, glob
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np


STORAGE_INIT = 0.01 # 1% filled at the beginning of the day
steps_data = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'data', 'HERON_data.xlsx')


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
  co2 = -6.0429
  electricity = -0.0004
  naphtha = 0.0419
  jet_fuel = 0.3443
  diesel = 1.4813

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
  location = case.split('/')[-1].split('_')[0]

  # SA
  SA = True
  if 'sweep' in case_name: 
    SA = False
  elif 'baseline' in case_name:
    SA = False

  if SA: 
    sweep_values_df = htse_df[htse_df['location']==location].drop(columns=['location'])
    sweep_values = np.round(list(sweep_values_df.iloc[0,[0,2,4,6,8]]))
  else: 
    sweep_values_df = htse_df[htse_df['location']==location].drop(columns=['location'])
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
  location = case.split('/')[-1].split('_')[0]

  # SA
  SA = True
  if 'sweep' in case_name: 
    SA = False
  elif 'baseline' in case_name:
    SA = False

  if SA: 
    sweep_values_df = meoh_df[meoh_df['location']==location].drop(columns=['location'])
    sweep_values = np.round(list(sweep_values_df.iloc[0,[0,2,4,6,8]]))
  else: 
    sweep_values_df = meoh_df[meoh_df['location']==location].drop(columns=['location'])
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
  if 'sweep' in case_name: 
    SA = False
  elif 'baseline' in case_name:
    SA = False


  if SA: 
    sweep_values_df = storage_df[storage_df['location']==location].drop(columns=['location'])
    sweep_values = np.round(list(sweep_values_df.iloc[0,[0,2,4,6,8]]))
  else: 
    sweep_values_df = storage_df[storage_df['location']==location].drop(columns=['location'])
    sweep_values = np.round(list(sweep_values_df.iloc[0,:]))
  sweep_values = [str(v) for v in sweep_values]
  sweep_values = ','.join(sweep_values)

  for comp in root.findall('Component'):
    if comp.get('name') =='h2_storage':
      sweep_val_node = comp.find('stores').find('capacity').find('sweep_values')
      sweep_val_node.text = sweep_values
      
  with open(os.path.join(case, 'heron_input.xml'), 'wb') as f:
    tree.write(f)



def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-p', "--pattern", type=str, nargs='+', help="pattern in cases names or cases' names")
  parser.add_argument('-c', "--case", type=str, help="case")
  args = parser.parse_args()
  dir = os.path.dirname(os.path.abspath(__file__))
  if args.pattern:
    if len(args.pattern)<=1:
      cases = glob.glob(dir+"/*"+args.pattern[0]+"*")
    else: 
      cases = [os.path.join(dir, p) for p in list(args.pattern)]
  elif args.case:
    cases = [os.path.join(dir, args.case)]
  else: 
    raise Exception("No case or input passed to this script!")
  print("Cases to modify: {}\n".format(cases))
  for case in cases:
    init_storage(case)
    meoh_ratios(case)
    reduced_arma_samples = True
    if '_sweep' in case:
      reduced_arma_samples = False
    if '_baseline' in case:
      reduced_arma_samples = False
    if reduced_arma_samples:
      arma_samples(case)
    sweep_values_htse(case)
    sweep_values_meoh(case)
    sweep_values_storage(case)

      

if __name__=="__main__":
 main()
