"""
Save Tool for GIS-MCP

This module provides a universal save function and exposes it as an MCP tool
so results from any GIS-MCP tool can be persisted in multiple formats.
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd
import geopandas as gpd
from shapely import wkt
import numpy as np
import rasterio
from rasterio.transform import from_origin
from PIL import Image

from .mcp import gis_mcp


def save_output(
    output: Dict[str, Any],
    filename: Optional[str] = None,
    folder: str = "outputs",
    formats: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Save the output dictionary to multiple formats:
    JSON, CSV, TXT, YAML, XLSX, SHP, GEOJSON, GeoTIFF, TIFF.

    Returns a mapping of format -> saved file path.
    """
    os.makedirs(folder, exist_ok=True)

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output_{timestamp}"

    if formats is None:
        formats = ["json", "csv", "txt", "yaml", "xlsx", "shp", "geojson", "geotiff", "tiff"]

    saved_files = {}

    # JSON
    if "json" in formats:
        path = os.path.join(folder, f"{filename}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)
        saved_files["json"] = path

    # CSV
    if "csv" in formats:
        try:
            path = os.path.join(folder, f"{filename}.csv")
            df = pd.json_normalize(output)
            df.to_csv(path, index=False)
            saved_files["csv"] = path
        except Exception as e:
            print(f"Could not save CSV: {e}")

    # TXT
    if "txt" in formats:
        path = os.path.join(folder, f"{filename}.txt")
        with open(path, "w", encoding="utf-8") as f:
            for k, v in output.items():
                f.write(f"{k}: {v}\n")
        saved_files["txt"] = path

    # YAML
    if "yaml" in formats:
        path = os.path.join(folder, f"{filename}.yaml")
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(output, f, allow_unicode=True)
        saved_files["yaml"] = path

    # Excel
    if "xlsx" in formats:
        try:
            path = os.path.join(folder, f"{filename}.xlsx")
            df = pd.json_normalize(output)
            df.to_excel(path, index=False)
            saved_files["xlsx"] = path
        except Exception as e:
            print(f"Could not save Excel: {e}")

    # Shapefile
    if "shp" in formats and "geometry" in output:
        try:
            path = os.path.join(folder, f"{filename}.shp")
            geom = wkt.loads(output["geometry"])
            gdf = gpd.GeoDataFrame([output], geometry=[geom], crs="EPSG:4326")
            gdf.to_file(path, driver="ESRI Shapefile")
            saved_files["shp"] = path
        except Exception as e:
            print(f"Could not save Shapefile: {e}")

    # GeoJSON
    if "geojson" in formats and "geometry" in output:
        try:
            path = os.path.join(folder, f"{filename}.geojson")
            geom = wkt.loads(output["geometry"])
            gdf = gpd.GeoDataFrame([output], geometry=[geom], crs="EPSG:4326")
            gdf.to_file(path, driver="GeoJSON")
            saved_files["geojson"] = path
        except Exception as e:
            print(f"Could not save GeoJSON: {e}")

    # GeoTIFF
    if "geotiff" in formats and "raster" in output:
        try:
            path = os.path.join(folder, f"{filename}.tif")
            raster_data = np.array(output["raster"])
            transform = from_origin(0, 0, 1, 1)
            crs = output.get("crs", "EPSG:4326")

            with rasterio.open(
                path,
                "w",
                driver="GTiff",
                height=raster_data.shape[0],
                width=raster_data.shape[1],
                count=1 if raster_data.ndim == 2 else raster_data.shape[2],
                dtype=raster_data.dtype,
                crs=crs,
                transform=transform,
            ) as dst:
                if raster_data.ndim == 2:
                    dst.write(raster_data, 1)
                else:
                    for i in range(raster_data.shape[2]):
                        dst.write(raster_data[:, :, i], i + 1)

            saved_files["geotiff"] = path
        except Exception as e:
            print(f"Could not save GeoTIFF: {e}")

    # TIFF
    if "tiff" in formats and "image" in output:
        try:
            path = os.path.join(folder, f"{filename}.tiff")
            img = Image.fromarray(np.uint8(output["image"]))
            img.save(path, format="TIFF")
            saved_files["tiff"] = path
        except Exception as e:
            print(f"Could not save TIFF: {e}")

    return saved_files


@gis_mcp.tool()
def save_results(
    data: Dict[str, Any],
    filename: Optional[str] = None,
    formats: Optional[List[str]] = None,
    folder: str = "outputs"
) -> Dict[str, Any]:
    """
    MCP Tool: Save any GIS-MCP result dict to files, only when the user requests.

    Args:
        data: The dictionary returned by any GIS-MCP tool.
        filename: Base filename without extension.
        formats: List of formats to save (default = all).
        folder: Target folder.

    Returns:
        Dict with 'saved_files' mapping format -> path.
    """
    try:
        paths = save_output(data, filename=filename, folder=folder, formats=formats)
        return {
            "status": "success",
            "saved_files": paths,
            "message": "Results saved successfully."
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to save results: {e}"}
