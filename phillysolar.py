import arcpy
from arcpy.sa import *
import os
import time

# 0. Check out Spatial Analyst
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
else:
    raise RuntimeError("Spatial Analyst license is not available.")

# 1. Redirect scratch away from OneDrive
arcpy.env.scratchWorkspace = r"C:\Temp\ArcPyScratch"

# 2. Set workspace & overwrite
arcpy.env.workspace = r"C:\Users\ureka\OneDrive\Documents\Python Scripts\PhillySolar"
arcpy.env.overwriteOutput = True

# 3. Define inputs (exact paths)
dem_path = r"C:\Users\ureka\OneDrive\Documents\Python Scripts\PhillySolar\Philadelphia_dem_3ft_2022\Philadelphia_dem_3ft_2022.tif"
empowerment_zones = r"C:\Users\ureka\OneDrive\Documents\Python Scripts\PhillySolar\PhiladelphiaEmpowermentZones201201\Philadelphia Empowerment Zones\PhiladelphiaEmpowermentZones201201.shp"
building_footprints = r"C:\Users\ureka\OneDrive\Documents\Python Scripts\PhillySolar\LI_BUILDING_FOOTPRINTS\LI_BUILDING_FOOTPRINTS.shp"

# 4. Quick existence check
print("DEM exists?             ", os.path.exists(dem_path))
print("Empowerment Zones exist?", os.path.exists(empowerment_zones))
print("Buildings exist?        ", os.path.exists(building_footprints))

# 5. Clip DEM to Empowerment Zones
clipped_dem = "Clipped_DEM_EZ.tif"
print("→ Clipping DEM…")
arcpy.Clip_management(
    in_raster=dem_path,
    rectangle="",
    out_raster=clipped_dem,
    in_template_dataset=empowerment_zones,
    nodata_value="-9999",
    clipping_geometry="ClippingGeometry",
    maintain_clipping_extent="MAINTAIN_EXTENT"
)
print("✅ Clip complete:", clipped_dem)

# 6. Resample clipped DEM to 3 m
resampled_dem = "Resampled_DEM_3m.tif"
print("→ Resampling to 3 m…")
arcpy.Resample_management(
    in_raster=clipped_dem,
    out_raster=resampled_dem,
    cell_size="3",
    resampling_type="BILINEAR"
)
print("✅ Resample complete:", resampled_dem)

# 7. Apply building footprints mask
arcpy.env.mask = building_footprints

# 8. Run Solar Radiation with timing
print("→ Starting solar radiation (test run on 3 m DEM)…")
t0 = time.time()
time_config = TimeMultipleDays(2025, 1, 365)  # full calendar year
solar_raster = AreaSolarRadiation(
    resampled_dem,  # use the 3 m DEM now
    "",             # latitude (auto)
    200,            # sky_size
    time_config     # time configuration
)
t1 = time.time()
print(f"→ Solar calculation took {(t1 - t0)/60:.1f} minutes")

# 9. Save the result
solar_output = "SolarRadiation_EZ_3m.tif"
solar_raster.save(solar_output)
print("✅ Solar radiation complete and saved as:", solar_output)
