
USAGE

Modify the 'ufs2arco_gdas_L13.yaml' with your configures (e.g., date period, resolution: '1p00' abd '0p25' for 1 degree and 0.25 degree GDAS )

Modify the 'submit_ufs2arco_gdas.sh' with your project account and the path to your miniconda installation.

Then run the following to submit a job to get all the data you need:

	sbatch submit_ufs2arco_gdas.sh

STDOUT and STDERR from the job will be placed in the logs directory.

This job creates NOAA GDAS data that has been processed for training with the Anemoi framework. 

Data from 2021-04-01 to 2024-09-30 will be used for training
