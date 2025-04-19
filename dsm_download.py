import os, glob
import requests
from bs4 import BeautifulSoup
import arcpy

# ---------------------------------------
# 0. Configuration
# ---------------------------------------
download_folder = r"C:\LiDAR\Philly2022"
base_url        = "https://noaa-nos-coastal-lidar-pds.s3.amazonaws.com/laz/geoid18/9848/"
index_url       = base_url + "index.html"
lasd_path       = os.path.join(download_folder, "Philly2022.lasd")
dsm_path        = os.path.join(download_folder, "DSM_Philadelphia_1m.tif")

arcpy.env.overwriteOutput = True

# ---------------------------------------
# 1. Download all .copc.laz if needed
# ---------------------------------------
os.makedirs(download_folder, exist_ok=True)
existing = glob.glob(os.path.join(download_folder, "*.copc.laz"))
if not existing:
    print("Downloading LAZ tiles…")
    r = requests.get(index_url); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # find links ending in .copc.laz
    tiles = [a["href"] for a in soup.find_all("a", href=True) if a["href"].endswith(".copc.laz")]
    for href in tiles:
        url      = href if href.startswith("http") else base_url + href
        name     = os.path.basename(url)
        out_path = os.path.join(download_folder, name)
        if not os.path.exists(out_path):
            print(" →", name)
            resp = requests.get(url, stream=True); resp.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
    print("Download complete.")
else:
    print(f"Found {len(existing)} LAZ tiles; skipping download.")

# ---------------------------------------
# 2. Build the LAS Dataset
# ---------------------------------------
if arcpy.CheckExtension("3D") != "Available":
    raise RuntimeError("3D Analyst extension required.")
arcpy.CheckOutExtension("3D")

laz_files = glob.glob(os.path.join(download_folder, "*.copc.laz"))
print(f"Creating LAS Dataset for {len(laz_files)} tiles…")
arcpy.management.CreateLasDataset(
    in_files         = laz_files,
    out_las_dataset  = lasd_path,
    spatial_reference= "",
    filter_type      = "",
    class_codes      = "",
    compute_stats    = "NONE"
)
print("LAS Dataset created at:", lasd_path)

# ---------------------------------------
# 3. Convert LAS Dataset → DSM raster
# ---------------------------------------
print("Building 1 m DSM raster…")
arcpy.ddd.LasDatasetToRaster(
    in_las_dataset       = lasd_path,
    out_raster           = dsm_path,
    value_field          = "ELEVATION",
    cell_assignment_type = "MAXIMUM",
    sampling_type        = "CELLSIZE",
    sampling_value       = 1,
    data_type            = "FLOAT"
)
print("DSM raster created at:", dsm_path)

arcpy.CheckInExtension("3D")
print("All done! Feed this DSM into AreaSolarRadiation().")
