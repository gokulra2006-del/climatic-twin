import xarray as xr
import os
import glob
import zipfile
import tempfile
import shutil

def process_era5():
    print("Processing ERA5-Land...")
    base_dir = "data/raw/weather/era5_land"
    out_dir = "data/processed/weather"
    os.makedirs(out_dir, exist_ok=True)
    
    files = glob.glob(os.path.join(base_dir, "*.nc"))
    if not files:
        print("No ERA5-Land files found.")
        return
        
    print(f"Found {len(files)} files. Extracting and loading...")
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        extracted_files = []
        for i, f in enumerate(files):
            try:
                # The CDS API returned zip files saved as .nc
                with zipfile.ZipFile(f, 'r') as zip_ref:
                    # Extract to tmpdir with a unique name
                    for info in zip_ref.infolist():
                        info.filename = f"data_{i}.nc"
                        zip_ref.extract(info, tmpdirname)
                        extracted_files.append(os.path.join(tmpdirname, info.filename))
            except zipfile.BadZipFile:
                # In case it's actually a raw NetCDF file and not a zip
                shutil.copy(f, os.path.join(tmpdirname, f"data_{i}.nc"))
                extracted_files.append(os.path.join(tmpdirname, f"data_{i}.nc"))

        if not extracted_files:
            print("No valid data found inside ERA5 archives.")
            return

        # Open multiple datasets and concatenate along the time dimension
        ds = xr.open_mfdataset(extracted_files, combine='by_coords', engine='netcdf4')
        
        print("Resampling to daily aggregates...")
        ds_daily = ds.resample(valid_time='1D').mean()
        
        out_path = os.path.join(out_dir, "era5_land_chennai_daily.nc")
        ds_daily.to_netcdf(out_path)
        print(f"Saved processed ERA5-Land data to {out_path}")

if __name__ == "__main__":
    process_era5()
