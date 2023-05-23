import glob, os, argparse, shutil
import pandas as pd

def check_gold_dir(case):
  # Make gold dir if does not exist
  gold_dir = os.path.join(case, "gold")
  if not os.path.isdir(gold_dir):
    print("Gold folder not found for case {}, creating it".format(case))
    os.mkdir(gold_dir)

def save_sweep_results(case):
  opt_folder = glob.glob(case+"/*_o")
  if len(opt_folder)>1:
    raise Exception("More than 1 sweep folder: {}".format(opt_folder))
  else:
    #sort by mean NPV descending order and save in gold folder
    sweep_results_df = pd.read_csv(os.path.join(opt_folder, "sweep.csv"))
    sweep_results_df.sort_values(by=['mean_NPV'], ascending=False, inplace=True)
    print("Sorting and saving the latest sweep results to gold folder for case {}".format(case))
    sweep_results_df.to_csv(os.path.join(case, "gold", "sweep.csv"), index=False)

def get_final_npv(case):
  # Assumes sweep results csv file in gold folder and sorted
  sweep_file = os.path.join(".", case, "gold", 'sweep.csv')
  df = pd.read_csv(sweep_file)
  df = df.iloc[:1,:]
  final_npv = df.mean_NPV.to_list()
  std_npv = df.std_NPV.to_list()
  return final_npv, std_npv

def save_final_out(case):
  final_npv, std_npv= get_final_npv(case)
  for dirpath, dirnames, files in os.walk(case):
    for folder in dirnames: 
      if '_o' in folder:
        opt_folder = folder
  opt_folder = os.path.join(case,opt_folder, "sweep" )
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
  final_out_file = ""
  for out_file, npv in out_to_npv.items():
      if round(npv,1) == round(final_npv,1):
        final_out_file = out_file
  if len(final_out_file) <=1:
    print("Final out~inner file not found! Re-run the case?")
  else:
    print("Final out~inner found here: {}, \n and copied to gold, commit it!".format(final_out_file))
    shutil.copy(final_out_file, os.path.join(case, "gold", "out~inner"))

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('pattern', type=str, nargs='+', help="pattern in cases names or cases' names")
  args = parser.parse_args()
  dir = os.path.dirname(os.path.abspath(__file__))
  if len(args.pattern)<=1:
    cases = glob.glob(dir+"/*"+args.pattern[0]+"*")
  else: 
    cases = [os.path.join(dir, p) for p in list(args.pattern)]
  for case in cases:
    if os.path.isdir(case):
      check_gold_dir(case)
      save_sweep_results(case)
      save_final_out(case)
      
      

if __name__=="__main__":
 main()