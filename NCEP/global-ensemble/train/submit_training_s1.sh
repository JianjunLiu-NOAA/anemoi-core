#!/bin/bash
#SBATCH -A enter_your_account
#SBATCH -J p025_gdas_s1
#SBATCH -o slurm/p025_gdas_s1.%j.out
#SBATCH -e slurm/p025_gdas_s1.%j.err
#SBATCH --nodes=4
#SBATCH -t 00:30:00 #15:30:00
#SBATCH --partition=u1-h100
#SBATCH --qos=gpu
#SBATCH --gpus-per-node=2
#SBATCH --mem=256G
#SBATCH --exclusive
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=24

module purge
module load hpc-x/2.18.1-mt-gcc
module load cuda

# activate the environment
source /pathtoconda/miniconda/bin/activate
conda activate anemoi

export HYDRA_FULL_ERROR=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# submit the code
srun anemoi-training train --config-name=aifs_en_gdas_s1
