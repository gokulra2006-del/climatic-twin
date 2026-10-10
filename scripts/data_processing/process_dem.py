import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import box
import os
import glob

def process_dem():
    print("Processing Copernicus DEM...")
    base_dir = "data/raw/geospatial/copernicus_dem"
    out_dir = "data/processed/geospatial"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Merge DEM Tiles
    files = glob.glob(os.path.join(base_dir, "*.tif"))
    if not files:
        print("No DEM files found.")
        return
        
    src_files_to_mosaic = []
    for fp in files:
        src = rasterio.open(fp)
        src_files_to_mosaic.append(src)
        
    print(f"Merging {len(src_files_to_mosaic)} tiles...")
    mosaic, out_trans = merge(src_files_to_mosaic)
    out_meta = src_files_to_mosaic[0].meta.copy()
    
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans
    })
    
    temp_mosaic = os.path.join(out_dir, "temp_merged_dem.tif")
    with rasterio.open(temp_mosaic, "w", **out_meta) as dest:
        dest.write(mosaic)
        
    for src in src_files_to_mosaic:
        src.close()
        
    # 2. Clip to Chennai Bounding Box (79.5, 12.5, 80.5, 13.5)
    print("Clipping to Chennai Bounding Box...")
    minx, miny, maxx, maxy = 79.5, 12.5, 80.5, 13.5
    bbox = box(minx, miny, maxx, maxy)
    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs="EPSG:4326")
    shapes = [features["geometry"] for features in geo.iterfeatures()]
    
    with rasterio.open(temp_mosaic) as src:
        out_image, out_transform = mask(src, shapes, crop=True)
        out_meta = src.meta
        
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform
    })
    
    out_path = os.path.join(out_dir, "chennai_dem_30m.tif")
    with rasterio.open(out_path, "w", **out_meta) as dest:
        dest.write(out_image)
        
    os.remove(temp_mosaic)
    print(f"Saved processed DEM to {out_path}")

if __name__ == "__main__":
    process_dem()
