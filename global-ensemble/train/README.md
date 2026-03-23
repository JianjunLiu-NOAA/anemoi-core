Workflow

'aifs_en_gdas_s1.yaml' - configuration file of the model training. s1 - the training for stage 1 for AR=1

modify the sbatch script to run model training with the 'yaml' file, and Run:

	sbatch submit_training_s1.sh

After submission, go into the outputs/ folder to monitor training. You will see the following model output:

Logs: found within a folder including the date of your run (e.g. 2025-08-01)

Checkpoints: found within a folder that matches the run_id of your training. It will resemble something like cf574663-cfa7-4ff2-aafd-37fb5af6bef5.

Notes:
	The model training uses the 8 GPUs (4-nodes)
	
