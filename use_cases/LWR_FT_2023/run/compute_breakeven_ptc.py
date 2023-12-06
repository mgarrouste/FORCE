import pandas as pd
import os
import matplotlib.pyplot as plt
from gold_results import get_final_npv
import numpy as np
import seaborn as sns
from sklearn.linear_model import LinearRegression

LOCATIONS = ['braidwood', 'cooper', 'davis_besse', 'prairie_island', 'stp']
PTC = [0,1,2.7,3]
case_names = ['ptc_000', 'ptc_100', 'ptc_270', 'sweep']

def compute_lin_reg_coefs(PTC, mean_NPV):
  x = np.array(PTC).reshape((-1,1))
  y = np.array(mean_NPV)
  model = LinearRegression.fit(x,y)
  a = model.coef_
  b = model.intercept_
  r_squared = model.score(x,y)
  return a,b,r_squared


def get_npv_data(location):
  baseline = os.path.join(os.path.dirname(os.path.abspath(__file__)), location+'_baseline')
  baseline_npv, baseline_npv_sd = get_final_npv(baseline)

  mean_NPV_list = []
  for case in case_names: 
    full_case = os.path.join(os.path.dirname(os.path.abspath(__file__)), location+'_'+case)
    npv, sd = get_final_npv(full_case)
    mean_NPV_list.append(npv)

  return mean_NPV_list, baseline_npv

def build_reg_table():
  dic_list =[]
  for location in LOCATIONS:
    loc_dic = {}
    loc_dic['location'] = location
    mean_NPV_list, baseline_NPV = get_npv_data(location)
    a, b, r_squared = compute_lin_reg_coefs(PTC, mean_NPV_list)
    loc_dic['a'] = a
    loc_dic['b'] = b
    loc_dic['r_squared'] = r_squared
    ptc_be = (baseline_NPV-b)/a
    loc_dic['ptc_breakeven'] = ptc_be
    dic_list.append(loc_dic)
  return dic_list


def main():
  build_reg_table()

if __name__ == "__main__":
  main()