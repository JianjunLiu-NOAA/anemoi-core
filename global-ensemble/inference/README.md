Workflow

there are two steps for model inference: 1. generate ICs from 0.25 degree GEFSv12 with 31 ensemble members; 2. run anemoi-inference to make forcasts with 31 IC members

run_config: configurations of ICs generations and inference 

1. Generate ICs from 0.25 degree GEFSv12

	'gene_gefs_ics_0p25.py': main code to generate the ICs from 0.25 degree GEFSv12
	
	'run_gene_ICs_jobs.sh': batch script to run code to generate the ICs, run: 
		
		sbatch run_gene_ICs_jobs.sh --pdate 20250801_06

2. Run anemoi-inference to create a 15-day forecast

	'jobcard_submit_model.py': main code to run the anemoi-inference
	
	'run_model_jobs.sh': batch script to run code to generate the forecasts, run:
		
		sbatch run_model_jobs.sh --pdate 20250801_06
		

Your forecast files will be saved as NetCDF's in a inference_files directory. If 'save_grib' is true, we will create the predictions as 'grib2' file

Note: 
	Within inference_config.yaml you will find a path to a checkpoint. The submit script updates that for you. 
	However, if you have trained multiple models you may have to go edit this yourself to find the specific run_id you wish to use a checkpoint from.
