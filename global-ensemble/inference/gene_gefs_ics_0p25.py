"""
Description: script gets ensemble GEFS members for aifs_en initialization
"""
import os, argparse
from time import time
from datetime import datetime, timedelta
import xarray as xr
import numpy as np
import pandas as pd
from collections import defaultdict
import pygrib, zarr, subprocess, yaml
from concurrent.futures import ProcessPoolExecutor, as_completed

class GEFSDataProcessor:
    def __init__(self,pdate,member,fhr,output_directory,download_directory,keep_downloaded_data=True):
        self.pdate = pdate
        self.member = member
        self.fhr = fhr
        self.output_directory = output_directory
        self.cache_dir  = download_directory
        self.keep_downloaded_data = keep_downloaded_data
        
        os.makedirs(self.output_directory, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.file_suffix = ("", "s")
        self.param_sfc = ["10u", "10v", "2d", "2t","sp","orog","msl", "lsm", "t", "2sh"] 
        self.typeOfLevel_sfc = ['heightAboveGround','heightAboveGround','heightAboveGround',
                                'heightAboveGround','surface','surface','meanSea','surface',
                                'surface','heightAboveGround']    
        self.para_pl = ["gh", "t", "u", "v", "w", "q"] 
        self.typeOfLevel_pl= ['isobaricInhPa']
        self.pl_levels = [1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50]

    def open_local(self,t0):     
        cache_dir = self.cache_dir
        c_or_p = "c" if self.member == 0 else "p"
        pdate = t0.strftime("%Y%m%d")
        phour = t0.strftime("%H")
        local_path = os.path.join(f"{cache_dir}/{pdate}T{phour}")
        os.makedirs(local_path,exist_ok=True)
        
        cached_files  = []
        for file_suffix in self.file_suffix:
            fname = f"ge{c_or_p}{self.member:02d}.t{phour}z.pgrb2{file_suffix}.0p25.f000"
            local_file = f"{local_path}/{fname}"
            if not os.path.exists(local_file):
                print(f"ERROR: File not found: {local_file}")
                sys.exit(1)
            cached_files.append(local_file)
            del fname,local_file

        return cached_files
            
    def remove_downloaded_data(self):
        # Remove downloaded data from the specified directory
        print("Removing downloaded grib2 data...")
        try:
            os.system(f"rm -r {self.cache_dir}/*")
            print("Downloaded data removed.")
        except Exception as e:
            print(f"Error removing downloaded data: {str(e)}")
                
    def get_open_data(self,params,typeOfLevel,levelist=[]):
        fields = defaultdict(list)
        for k, param in enumerate(params):
            print(f'processing param: {param}')
            for t0 in [self.pdate - timedelta(hours=6), self.pdate]:
                for file in self.open_local(t0): 
                    grbs = pygrib.open(file)
                    if len(levelist)==0:   # surface
                        try:
                            msgs = grbs.select(shortName=param, typeOfLevel=typeOfLevel[k])[0]
                            value = msgs.values.flatten()
                            fields[msgs.shortName].append(value)
                            del value, msgs
                        except ValueError:
                            pass                  
                    else: 
                        for level in levelist:
                            try:
                                msgs = grbs.select(shortName=param,typeOfLevel=typeOfLevel,level=level)[0]
                                value = msgs.values.flatten()
                                vname = f"{param}_{level}" 
                                fields[vname].append(value)
                                del msgs,value,vname
                            except ValueError:
                                pass
                   
        # Create a single matrix for each parameter
        for param, values in fields.items():
            fields[param] = np.stack(values)
            
        return(fields)

    def get_vars(self):
        fields = {}
        fields.update(self.get_open_data(params=self.param_sfc,typeOfLevel=self.typeOfLevel_sfc))
        fields.update(self.get_open_data(params=self.para_pl,typeOfLevel=self.typeOfLevel_pl,levelist=self.pl_levels))
        
        # Convert geopotential height (gh) into geopotential (z)
        for level in self.pl_levels:
            gh = fields.pop(f"gh_{level}")
            fields[f"z_{level}"] = gh * 9.80665
        # Orography (surface geopotential height) into geopotential
        fields['orog'] = fields['orog'] * 9.80665
  
        # rename
        rename_map = {"t": "skt","2sh":"sh2"}
        fields = {rename_map.get(k, k): v for k, v in fields.items()}
        
        # Optionally, remove downloaded data
        if not self.keep_downloaded_data:
            self.remove_downloaded_data()
           
        return(fields)

class Save2Zarr:
    def __init__(self,data,fname,datetime,latitudes,longitudes):
        self.fields = data
        self.fname = fname
        self.datetime = datetime
        self.ntime = len(datetime)
        self.nens = 1
        self.ncell = latitudes.shape[0]
        self.latitudes = latitudes
        self.longitudes = longitudes
        self.variables = list(data.keys())
        
    def SaveData(self):
        name_to_index = {var: i for i, var in enumerate(self.variables)}
        # Stack fields into a 4D array: (time, variable, ensemble, cell)
        stacked_data = np.stack([self.fields[v] for v in self.variables], axis=1)
        stacked_data = stacked_data[:, :, np.newaxis, :]
        # Compute statistics
        mean = stacked_data.mean(axis=(0, 2, 3))
        minimum = stacked_data.min(axis=(0, 2, 3))
        squares = (stacked_data**2).mean(axis=(0, 2, 3))
        stdev = stacked_data.std(axis=(0, 2, 3))
        # convert coords
        ds = xr.Dataset(
            data_vars=dict(
                data=(["time", "variable", "ensemble", "cell"], stacked_data),
                mean=(["variable"], mean),
                minimum=(["variable"], minimum),
                squares=(["variable"], squares),
                stdev=(["variable"], stdev),
            ),
            coords=dict(
                time=("time", np.arange(self.ntime)),
                variable=("variable", self.variables),
                ensemble=("ensemble", np.arange(self.nens)),
                cell=("cell", np.arange(self.ncell)),
                latitudes=("cell", self.latitudes),
                longitudes=("cell", self.longitudes),
            ),
        )
        ds.attrs["name_to_index"] = name_to_index
        ds.to_zarr(self.fname, mode="w")
        nds = self.add_dates()
        nds.to_zarr(self.fname, mode="a")
        
    def add_dates(self) -> None:
        """Deal with the dates issue
        for some reason, it is a challenge to get the datetime64 dtype to open
        consistently between zarr and xarray, and
        it is much easier to deal with this all at once here
        than in the create_container and incrementally fill workflow.
        """
        xds = xr.open_zarr(self.fname)
        attrs = xds.attrs.copy()
        nds = xr.Dataset()
        nds["dates"] = xr.DataArray(
            self.datetime,
            coords=xds["time"].coords,
        )
        nds["dates"].encoding = {
            "dtype": "datetime64[s]",
            "units": "seconds since 1970-01-01",
        }
        nds.attrs = attrs
        return nds

def process_single_member(member, pdate, fhr, out_dir, cache_dir, keep_downloaded_data, pdates, latitudes, longitudes):
    
    sdate = pdates[1]
    fname = f"{out_dir}/gefs_en_data_0p25_{sdate}_M{member}.zarr"
    
    if os.path.exists(fname):
        return f"Skipped: {fname} (exists)"
    try:
        member_cache = os.path.join(cache_dir, f"mem_{member}")
        
        data_processor = GEFSDataProcessor(pdate, member, fhr, out_dir, member_cache, keep_downloaded_data)
        fields = data_processor.get_vars()     

        data_save = Save2Zarr(fields, fname, pdates, latitudes, longitudes)
        data_save.SaveData()
        return f"Successfully processed member {member}"
    except Exception as e:
        return f"Error processing member {member}: {str(e)}"   


#*****************************************************************************************************
# usage: python3 gene_gefs_ics_0p25.py -p '20250801_00' -n 31 -k yes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process GEFS data for aifs_en ics")
    parser.add_argument("-p","--pdate", help="Processing datetime in the format 'YYYYMMDD_HH'")
    parser.add_argument("-n","--nmember", help="total number of members")
    parser.add_argument("-k", "--keep", help="Keep downloaded data (yes or no)", default="no")

    args = parser.parse_args()
    sdate = args.pdate
    NM = int(args.nmember)
    keep_downloaded_data = args.keep.lower() == "yes"
    
    pdate = datetime.strptime(sdate, '%Y%m%d_%H')
    fhr = 0    

    with open("run_config.yaml", "r") as f:
        conf = yaml.safe_load(f)
    data_path = conf['data_path']
    resolution = conf['resolution']
    cache_dir = conf['cache_dir']
    out_dir = f"{data_path}/{resolution}"
    os.makedirs(out_dir,exist_ok=True)
    
    lat = np.arange(90, -90.001, -0.25); lon = np.arange(0, 360, 0.25);    
    lon2d, lat2d = np.meshgrid(lon, lat)
    latitudes = lat2d.ravel()
    longitudes  = lon2d.ravel()
    
    # current date and previous 6-h
    cdate = [pdate - timedelta(hours=6), pdate]
    pdates = [d.strftime('%Y-%m-%dT%H') for d in cdate]
    sdate = pdates[1]
    out_dir = f'{out_dir}/{sdate}'
    os.makedirs(out_dir,exist_ok=True)
    
    print(f"*******************************************************")
    # The number of CPUs to use
    slurm_cpus = os.getenv('SLURM_CPUS_PER_TASK')
    if slurm_cpus:
        num_workers = int(slurm_cpus)
    else:
        num_workers = 4
    print(f"Starting parallel processing with {num_workers} workers for {NM} members")
    
    # Use ProcessPoolExecutor to parallelize the loop
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(
                process_single_member, 
                m, pdate, fhr, out_dir, cache_dir, 
                keep_downloaded_data, pdates, latitudes, longitudes
            ) for m in range(NM)
        ]
        
        for future in as_completed(futures):
            print(future.result())
    