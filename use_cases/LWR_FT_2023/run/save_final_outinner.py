import os, shutil
import pandas as pd
import argparse
from plot_sweep import get_baseline_NPV

def get_final_npv(plant, baseline=False):
  opt_out_file = os.path.join(".", plant, "gold","opt_soln_0.csv")
  sweep_file = os.path.join(".", plant, "gold", 'sweep.csv')
  if os.path.isfile(opt_out_file):
    df = pd.read_csv(opt_out_file)
    final_npv = [float(df.iloc[-1].loc['mean_NPV'])]
    std_npv = [float(df.iloc[-1].loc['std_NPV'])]
    tag = 'opt'
  elif os.path.isfile(sweep_file) and not baseline:
    df = pd.read_csv(sweep_file)
    # get final npv for first 4 highest NPV
    df.sort_values(by=['mean_NPV'], ascending=False, inplace=True)
    df.reset_index(inplace=True)
    df.to_csv(os.path.join('.', plant, 'gold', 'sorted_sweep.csv'))
    df = df.iloc[:1,:]
    final_npv = df.mean_NPV.to_list()
    std_npv = df.std_NPV.to_list()
    tag = 'sweep'
  elif os.path.isfile(sweep_file) and baseline:
    df = pd.read_csv(sweep_file)
    # first line is the one 
    final_npv = [float(df.iloc[0].loc['mean_NPV'])]
    std_npv = [float(df.iloc[0].loc['std_NPV'])]
    tag = 'baseline'
  else: 
    raise FileNotFoundError("No sweep or optimization results in the gold folder of {} case".format(plant))
  return final_npv, std_npv, tag

def find_final_out(plant):
  """Assumes this notebook is saved in run folder
  Function find_out_file(plant) returning the path to the right out~inner given the name of the plant
  Look for the right out~inner file
  For each out~inner file
  get all npv results, take the average and compare it to final results in opt_soln_0.csv
  if it is the right file save it to gold folder and save path to final_ou
  """
  plant_folder = "./"+plant
  if "baseline" in plant:
    baseline = True
    print("Case {} identified as baseline case, only breaking down cashflows for first line in sweep results csv".format(plant))
  else: 
    baseline = False
  final_npv, std_npv, tag = get_final_npv(plant, baseline=baseline)
  for dirpath, dirnames, files in os.walk(plant_folder):
    for folder in dirnames: 
      if '_o' in folder:
        opt_folder = folder
  if tag == "opt":
    opt_folder = os.path.join(plant_folder,opt_folder,"optimize")
  else: 
    opt_folder = os.path.join(plant_folder,opt_folder, "sweep" )
  # Get all the out~inner files path in a list
  out_files =[]
  for f in os.listdir(opt_folder):
    if not os.path.isfile(os.path.join(opt_folder,f)) and "_i" not in f:
      out_file = os.path.join(opt_folder,f, "out~inner")
      out_files.append(out_file)
  # Map each out~inner to corresponding NPV
  out_to_npv = {}
  for out_file in out_files:
      lines =[]
      with open(out_file, 'rb') as fp:
        for line in fp: 
          lines.append(line.decode(errors='ignore'))
      npvs = []
      for l in lines:
        if "   NPV" in l:
          npvs.append(float(l.split(" ")[-1]))
      if len(npvs) != 0:
        avg_npv = sum(npvs)/len(npvs)
        out_to_npv[out_file] = avg_npv
  final_out = False
  final_out_dic = {}
  for idx, f_npv in enumerate(final_npv): 
    for out_file, npv in out_to_npv.items():
      if round(npv,1) == round(f_npv,1):
        final_out_dic[idx] = out_file
  return final_out_dic, tag

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('case_name', type=str, help="Case folder name in the run directory")
  args = parser.parse_args()
  dir = os.path.dirname(os.path.abspath(__file__))
  case_folder = os.path.join(dir, args.case_name)
  final_out, tag = find_final_out(args.case_name)
  print(final_out)
  if tag == "opt":
    assert len(final_out.keys()) == 1, "Problem optimization led to >1 out~inner file for final point"
    print("Final out~inner found here: {}, \n and copied to gold, commit it!".format(final_out[0]))
    shutil.copy(final_out[0], os.path.join(case_folder, "gold", "out~inner_"+tag))
  elif tag =="sweep":
    for k,f in final_out.items():
      print("Out~inner for case {} found here: {}, \n and copied to gold, commit it!".format(k,f))
      shutil.copy(f, os.path.join(case_folder, "gold", "out~inner"+str(k)+"_"+tag))
  elif tag =="baseline":
    assert len(final_out.keys()) == 1, "Problem baseline case led to >1 out~inner file"
    print("Final out~inner found here: {}, \n and copied to gold, commit it!".format(final_out[0]))
    shutil.copy(final_out[0], os.path.join(case_folder, "gold", "out~inner_"+tag))
  else: 
    print("Final out~inner file(s) were not found, maybe the case has been re-run and the gold folder not updated?")

if __name__=="__main__":
 main()
 #test()

