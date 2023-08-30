import glob, os, argparse, shutil
import pandas as pd
import numpy as np

BASELINE_SMR_CAP_REF = 720.0

def check_gold_dir(case):
  # Make gold dir if does not exist
  gold_dir = os.path.join(case, "gold")
  if not os.path.isdir(gold_dir):
    print("Gold folder not found for case {}, creating it".format(case))
    os.mkdir(gold_dir)

def check_run_status(case, results_df):
  case_name = case.split('/')[-1]
  if 'smr_' in case:
    SA = True
  elif 'smr' in case:
    SA = False
    baseline = False
  elif 'baseline' in case:
    SA = False
    baseline = True
  else: 
    SA = True
  length = len(results_df)
  if SA:
    if length<125:
      print(f'Run not finished for {case_name}: \n only {length} runs')
      save = False
    else:
      save = True
  else:
    if baseline:
      if length<2: 
        print(f'Run not finished for {case_name}: \n only {length} runs')
        save = False
      else:
        save = True
    else:
      if length<1000:
        print(f'Run not finished for {case_name}: \n only {length} runs')
        save = False
      else:
        save = True
  return save
    


def save_sweep_results(case, force=False):
  opt_folder = glob.glob(case+"/*_o")
  if len(opt_folder)>1:
    raise Exception("More than 1 sweep folder: {}".format(opt_folder))
  elif len(opt_folder) ==0:
    print("No optimization folder for case {}, skip saving sweep csv results file".format(case))
    return None
  else:
    #sort by mean NPV descending order and save in gold folder
    opt_folder = opt_folder[0]
    sweep_results_df = pd.read_csv(opt_folder+"/sweep.csv")
    save = check_run_status(case,sweep_results_df)
    if save or force:
      sweep_results_df.sort_values(by=['mean_NPV'], ascending=False, inplace=True)
      print("Sorting and saving the latest sweep results to gold folder for case {}".format(case))
      sweep_results_df.to_csv(os.path.join(case, "gold", "sweep.csv"), index=False)

def get_final_npv(case, baseline=False, opt_point={}):
  # Assumes sweep results csv file in gold folder and sorted
  sweep_file = os.path.join(".", case, "gold", 'sweep.csv')
  if not os.path.isfile(sweep_file):
    print('Results not found for {}'.format(case))
    return None
  df = pd.read_csv(sweep_file)
  if not baseline and not opt_point:
    df = df.iloc[:1,:]
  else:
    df = df[df['smr_capacity']==BASELINE_SMR_CAP_REF]
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

def save_final_out(case, baseline):
  final_npv, std_npv= get_final_npv(case, baseline=baseline)
  opt_folder = glob.glob(case+"/*_o")
  if len(opt_folder)>1:
    raise Exception("More than 1 sweep folder: {}".format(opt_folder))
  elif len(opt_folder) ==0:
    print("No optimization folder for case {}, skip saving out~inner file".format(case))
    return None
  else:
    opt_folder = opt_folder[0]
  sweep_folder = opt_folder+ "/sweep"
  # Get all the out~inner files path in a list
  out_files = glob.glob(sweep_folder+"/*/out~inner")
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
  final_out_file = ""
  for out_file, npv in out_to_npv.items():
      if round(npv,0) == round(final_npv,0):
        final_out_file = out_file
  if len(final_out_file) <=1:
    print("Final out~inner file not found! Re-run the case?")
  else:
    print("Final out~inner found here: {}, \n and copied to gold, commit it!".format(final_out_file))
    shutil.copy(final_out_file, os.path.join(case, "gold", "out~inner"))

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-p', "--pattern", type=str, nargs='+', help="pattern in cases names or cases' names")
  parser.add_argument('-c', "--case", type=str, help="case")
  parser.add_argument('-f',"--force", type=bool, help='Force saving results even in run not finished')
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
  print("Cases to gold : {}\n".format(cases))
  for case in cases:
    if os.path.isdir(case) and not 'dispatch' in case:
      baseline = False
      if 'baseline' in case: 
        baseline = True
      check_gold_dir(case)
      if args.force:
        save_sweep_results(case, force=args.force)
      else:
        save_sweep_results(case)
      

if __name__=="__main__":
 main()
