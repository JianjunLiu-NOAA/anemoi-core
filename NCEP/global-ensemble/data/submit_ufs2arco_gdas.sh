#!/bin/bash

#SBATCH -J ufs2arco_gdas_L13_0p25
#SBATCH -o logs/0p25/prep13.%j.out
#SBATCH -e logs/0p25/prep13.%j.err
#SBATCH --account=enter_your_account
#SBATCH --partition=u1-service
#SBATCH --mem=128g
#SBATCH -t 00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1

source /pathtoyourminiconda/miniconda/etc/profile.d/conda.sh
module load openmpi
conda activate ufs2arco

srun ufs2arco ufs2arco_gdas_L13.yaml --overwrite
