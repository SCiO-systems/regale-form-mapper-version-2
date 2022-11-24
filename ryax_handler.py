import sys
import os

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(1, 'functions/')

#imports
from dbfread import DBF
import pandas as pd
import numpy as np
import copy
import string
from datar import dplyr,tidyr
from datar.all import f
from itertools import compress
import math
import os
import requests
import datar
import json


#import from other files
from LITAP_functions import *
from LITAP_utils import *
from LITAP_load import *
from LITAP_read_write import *

from form_01_calc_form import *
from form_02_calc_weti import *
from form_03_calc_relz import *
from form_04_calc_length import *


import warnings
warnings.filterwarnings("ignore")

#%%
def handle(module_input):
    # input_json = sys.argv[1]
    # input_json = "/home/christos/Desktop/SCiO_Projects/REGALE/regale/code/form_epirus_3_input_json.json"

    with open(module_input["input_json"], "r") as file:
      data = json.load(file)

    # TMP_DIR = "/tmp/"
    TMP_DIR = "/home/christos/Desktop/SCiO_Projects/REGALE/regale-ryax-modules/"

    out_directory = TMP_DIR + "python_epirus_3_example_outputs/"


    output_backup_folder = TMP_DIR + "backup/"
    output_stats_folder = TMP_DIR + "form/"


    grid = data["hyperparameters"]["grid"]
    str_val = data["hyperparameters"]["str_val"]
    ridge_val = data["hyperparameters"]["ridge_val"]
    verbose = data["hyperparameters"]["verbose"]

    # folder = "/home/christos/Desktop/SCiO_Projects/REGALE/sciocore-regale-e4979917ee0c/python_outputs/"
    # resume = ""
    # grid = 5
    # str_val = 10000
    # ridge_val = 10000
    out_format = "csv"
    # resume = None
    # end = None
    # log = True
    # clean = False
    # verbose = False
    # quiet = False

    # in order to be compatible with ryax platform, inputs with value -1 are translated to None value
    # if clim==-1:
    #     clim = None
    # if rlim==-1:
    #     rlim = None

    resume = ""

    #%% Load previous results from flow_mapper

    # loading data from flow execution
    # Get backup fill dem
    db = get_previous(out_directory,step="fill",where="flow")
    db = dplyr.select(db, f.seqno, f.row, f.col, f.elev, f.drec, f.upslope, f.fill_shed, f.local_shed)
    db = add_buffer(db)

    # Get backup inverted dem
    idb = get_previous(out_directory,step="ilocal",where="flow")
    if "ldir" in idb.columns:
        idb = datar.all.rename(idb, ddir="ldir")
    idb = dplyr.select(idb,f.seqno,f.row,f.col,f.elev,f.drec,f.ddir,f.upslope,f.shedno)
    idb = add_buffer(idb)

    # Get backup pond stats
    pond = pd.read_csv(out_directory + "flow/stats_pond.csv")
    pond = add_buffer(db,stats=pond)


    os.system("mkdir " + out_directory + "form/")
    #%% # Form 
    if (resume=="" or resume=="form"):
        db_form = calc_form(db, grid,verbose=verbose)
        
        save_output2(data=db_form, name="form", locs=out_directory, out_format=out_format, where = "form")


    #%% # Wetness indices 
    if (resume=="" or resume=="weti"):
        db_weti = calc_weti(db, grid, verbose = verbose)

        db_form = dplyr.full_join(db_form, db_weti, by=["seqno", "col", "row", "buffer"])
        
        db_form["lnqarea1"] = np.where(db_form["aspect"] > -1, np.log(db_form["qarea1"].astype(float)), 0)
        db_form["lnqarea2"] = np.where(db_form["aspect"] > -1, np.log(db_form["qarea2"].astype(float)), 0)
        db_form["new_asp"] = np.where(db_form["aspect"] > -1, db_form["aspect"] + 45, 0)
        db_form["new_asp"] = np.where(db_form["new_asp"] > 360,db_form["new_asp"] -360, db_form["new_asp"])
        db_form["lnqarea1"] = round(db_form["lnqarea1"], 3)
        db_form["lnqarea2"] = round(db_form["lnqarea2"], 3)

        #CHECK SAVED FILE THAT IS SIMILAR TO THE R-PRODUCED FILE
        save_output2(data=db_form, name="weti", locs=out_directory, out_format=out_format, where = "form")
        
        del db_form
        del db_weti
        

    #%% # Relief
    if (resume=="" or resume=="relief"):
        db_relz = calc_relz(db, idb, str_val = str_val, ridge_val = ridge_val, pond = pond, verbose = verbose)

        save_output2(data=db_relz, name="relief", locs=out_directory, out_format=out_format, where = "form")

    #%% # Length 
    if (resume=="" or resume=="length"):
        db_length = calc_length(db, db_relz, verbose = verbose)

        save_output2(data=db_length, name="length", locs=out_directory, out_format=out_format, where = "form")


    #%%
        del db_length
        del db_relz

    #%%

    # print(db_relz.json())
    # t = pd.DataFrame(db_relz.json())
    response = requests.get("https://r-lambdas-dummy.s3.eu-central-1.amazonaws.com/output.json")
    print(response)

    return {'python_outputs' : out_directory}


f1 = {
"input_json" :"/home/christos/Desktop/SCiO_Projects/REGALE/regale-ryax-modules/form_mapper_version_2/data/form_epirus_3_input_json.json",
      }

# f1 = {
# "input_json" :"/home/christos/Desktop/SCiO_Projects/REGALE/regale-ryax-modules/form_mapper_version_2/data/form_input_json.json",
#       }


t = handle(f1)  





