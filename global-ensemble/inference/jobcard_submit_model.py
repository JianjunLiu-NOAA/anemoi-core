import argparse
import os
from datetime import datetime, timedelta
import numpy as np
import yaml
import pandas as pd
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString as DQ
import subprocess,time

# from nc2grib import Netcdf2Grib

def write_yaml(
    checkpoint,
    lead_time,
    DATE,
    dfile,
    pfile,
    output_variables=None,
    ):
    """
    Generate an Anemoi inference YAML config file in exact style.
    """
    patch_metadata = CommentedMap()
    patch_metadata["dataset"] = CommentedMap()
    constant_fields = CommentedSeq(["lsm", "orog"])
    constant_fields.fa.set_flow_style()  # force inline: [lsm, orog]
    patch_metadata["dataset"]["constant_fields"] = constant_fields
    # Use CommentedMap to add comments and preserve order
    data = CommentedMap()
    data["checkpoint"] = DQ(checkpoint)
    data["lead_time"] = lead_time
    data.yaml_add_eol_comment("hours", "lead_time")  # comment after lead_time
    data["date"] = DATE
    # input/output
    data["input"] = CommentedMap()
    data["input"]["dataset"] = DQ(dfile)

    if output_variables==None:
        data["output"] = CommentedMap()
        data["output"]["netcdf"] = DQ(pfile)
    else:
        data["output"] = CommentedMap()
        data["output"]["netcdf"] = CommentedMap()
        data["output"]["netcdf"]["path"] = DQ(pfile)
        cf_vars = CommentedSeq(output_variables)
        cf_vars.fa.set_flow_style()  # inline list
        data["output"]["netcdf"]["variables"] = cf_vars

    data["write_initial_state"] = True
    # patch_metadata
    data["patch_metadata"] = patch_metadata
    return data
    
#----------------------
# usage: # python3 jobcard_submit_model.py --pdate 20250801_00
#----------------------

# date for processing
parser = argparse.ArgumentParser(description="Data processing from sdate to edate")
parser.add_argument("--pdate", type=str, required=True, help="Process start date in format yyyymmdd_hh")
args = parser.parse_args()
pdate = args.pdate

# config
with open("run_config.yaml", "r") as f:
    conf = yaml.safe_load(f)
data_path = conf['data_path']
lead_time = conf['lead_time']
resolution = conf['resolution']
job_path = conf['fjob']
os.makedirs(job_path,exist_ok=True)
save_grib = conf['save_grib']
data_path = f"{data_path}/{resolution}"

# Template of the job card
job_card_template = """#!/bin/bash
#SBATCH -A enter_your_account
#SBATCH -J inf_gefs_{pt}_M{MEMBER}
#SBATCH -o logs/inf_gefs_{pt}_M{MEMBER}.out
#SBATCH -e logs/inf_gefs_{pt}_M{MEMBER}.err
#SBATCH --nodes=1
#SBATCH -t 00:05:00
#SBATCH --partition=u1-h100
#SBATCH --qos=gpu
#SBATCH --gpus-per-node=1
#SBATCH --mem=256G 
#SBATCH --ntasks-per-node=1

# module load and activate en
source /pathtoconda/miniconda/etc/profile.d/conda.sh
conda activate anemoi

srun anemoi-inference run {job_path}/inference_config_{pt}_M{MEMBER}.yaml
"""

# Generate and submit job cards
pdate_dt = datetime.strptime(pdate, "%Y%m%d_%H")
pt = pdate_dt.strftime("%Y-%m-%dT%H")
pred_path = f"{conf['pred_path']}/{pt}"
os.makedirs(pred_path,exist_ok=True)

for MEMBER in np.arange(0,31):
    pfile = f"{pred_path}/ai_gefs_en_{pt}_{lead_time}h_M{MEMBER}.nc"
    if os.path.exists(pfile):
        continue

    # write a slurm
    job_card = job_card_template.format(pt=pt,MEMBER=MEMBER,job_path=job_path)
    job_filename = f"{job_path}/submit_inference_{pt}_M{MEMBER}.sh"
    with open(job_filename, 'w') as job_file:
        job_file.write(job_card)
    del job_card 

    # write the inference_config.yaml file
    dfile = f"{data_path}/{pt}/gefs_en_data_{resolution}_{pt}_M{MEMBER}.zarr"
    data = write_yaml(conf['checkpoint'],lead_time,pt,dfile,pfile)
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True
    yaml_filename = f'{job_path}/inference_config_{pt}_M{MEMBER}.yaml'
    with open(yaml_filename, "w") as f:
        yaml.dump(data, f)
    del dfile,pfile,data,yaml_filename
    
    # Submit the job and capture job ID
    result = subprocess.run(["sbatch", job_filename], capture_output=True, text=True)
    print(result.stdout.strip())
    try:
        job_id = result.stdout.strip().split()[-1]
        job_ids.append(job_id)
    except Exception:
        print(f"⚠️ Could not extract job ID for time:{pt} @ M{MEMBER}")
        
if save_grib:
# ============================================================
# === All MEMBERS finished → convert NC → GRIB for this pt ===
# ============================================================
    print(f"🔄 Converting all NC → GRIB for point: {pt}")
    for MEMBER in np.arange(0,31):
        pfile = f"{pred_path}/ai_gefs_en_{pt}_{lead_time}h_M{MEMBER}.nc"
        if not os.path.exists(pfile):
            print(f"ERROR: File not found: {pfile}")
            sys.exit(1)
        else:
            converter = Netcdf2Grib()
            converter.save_grib2(pfile, pred_path, MEMBER)
                    

