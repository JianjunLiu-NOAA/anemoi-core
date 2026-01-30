#!/bin/bash
#SBATCH -A enter_your_account
#SBATCH -J model_serial_run
#SBATCH -o logs/run_model_serial_%j.out
#SBATCH -e logs/run_model_serial_%j.err
#SBATCH --time=01:00:00
# #SBATCH --partition=u1-service
#SBATCH --mem=8G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1

# === Parameters ===

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

python3 jobcard_submit_model.py --pdate "$PDATE"
