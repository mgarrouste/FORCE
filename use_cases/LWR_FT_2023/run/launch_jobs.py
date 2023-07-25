import os
import glob, argparse
from subprocess import Popen, PIPE


def launch_heron(case):
  heron_input = os.path.join(case, 'heron_input.xml')
  heron_code = "/home/garrm/HERON/heron"
  heron_process = Popen([heron_code, heron_input])
  stdout, stderr = heron_process.communicate()
  print(stdout)

def launch_raven(case):
  outer = os.path.join(case, 'outer.xml')
  raven_code = "/home/garrm/raven/raven_framework"
  raven_process = Popen([raven_code, outer])
  stdout, stderr = raven_process.communicate()
  print(stdout)



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
  print("Cases to launch : {}\n".format(cases))
  nb_cases = len(cases)
  for case in cases:
    launch_heron(case)
    launch_raven(case)


if __name__=="__main__":
 main()