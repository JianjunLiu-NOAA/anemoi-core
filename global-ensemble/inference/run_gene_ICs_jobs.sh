#!/bin/bash
#SBATCH -A enter_your_account
#SBATCH -J gene_gefs_ICs
#SBATCH -o logs/gene_gefs_ICs_%j.out
#SBATCH -e logs/gene_gefs_ICs_%j.err
#SBATCH --time=1-00:00:00
#SBATCH --partition=u1-service
#SBATCH --mem=320G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4

set -e
set -u

while [[ $# -gt 0 ]]; do
  case $1 in
    --pdate)
      PDATE="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

: "${PDATE:?Missing --pdate}"

echo "Prediction date: $PDATE"


source /pathtoconda/miniconda/etc/profile.d/conda.sh
conda activate ufs2arco

Nmember=31
keep='yes'


echo "=========================================="
echo ">>> Submitting Slurm jobs for $PDATE"
echo "=========================================="
python3 gene_gefs_ics_0p25.py --pdate "$PDATE" -n $Nmember -k $keep

   

