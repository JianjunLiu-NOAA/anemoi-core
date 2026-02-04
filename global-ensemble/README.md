
OVERVIEW

This repository contains various configurations to guide users through a full machine learning pipeline for weather prediction!

The key steps to this pipeline include:

1. Data preprocessing using ufs2arco to create training, validation, and test datasets
	
2. Model training using anemoi-core modules to train a graph-based model
	
3. Creating a forecast with anemoi-inference to run inference from a model checkpoint



ENVIRONMENT

Before getting started, you will need to set up a conda environment. First, if you have not already, use these instructions to set up miniconda: https://www.anaconda.com/docs/getting-started/miniconda/install#linux. 
Be sure to install this in your scratch directory, as the environment we will create is quite big.

Set up the conda environment and install ufs2arco from the EMC repository:

Clone the package
	
		git clone https://github.com/NOAA-EMC/ufs2arco.git

Create the conda environment and install the package
	
		cd ufs2arco
		conda env create -f environment.yaml
		conda activate ufs2arco
		pip install .
		
		conda install -c conda-forge mpi4py
		
Setup the conda environment and install the anemoi from ECMWF repository:

		conda create -n anemoi python=3.12
		conda activate anemoi
		module load cuda
		pip install anemoi-datasets==0.5.26 anemoi-graphs==0.6.4 anemoi-models==0.9.1 anemoi-training==0.6.1 anemoi-inference==0.7.0
		pip install flash-attn mpi4py trimesh 'numpy<2.3' 'earthkit-data<0.14.0' 

Note: To install from a personal repository, clone the anemoi-core package from your own repository to ursa and install the anemoi package following the ufs2arco installation instructions. Subsequent updates to your local anemoi-core repository on ursa will be automatically synchronized with the anemoi environment.


USAGE

After the conda environments have been created, go follow instructions within each folder in this directory in order

Step 1: Data Creation (/data)
	
   Data preprocessing using ufs2arco to create training, validation, and test datasets
		
Step 2: Model Training (/training)
	
   Model training using anemoi-core modules to train a graph-based model
		
Step 3: Create a Forecast (/inference)
	
   Creating a forecast with anemoi-inference to run inference from a model checkpoint
