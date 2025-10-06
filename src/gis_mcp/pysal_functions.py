"""PySAL-related MCP tool functions and resource listings."""
import os
import logging
import numpy as np
import geopandas as gpd
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from .mcp import gis_mcp

# Configure logging
logger = logging.getLogger(__name__)

@gis_mcp.resource("gis://operations/esda")
def get_spatial_operations() -> Dict[str, List[str]]:
    """List available spatial analysis operations. This is for esda library. They are using pysal library."""
    return {
        "operations": [
            "getis_ord_g",
            "morans_i",
            "gearys_c",
            "gamma_statistic",
            "moran_local",
            "getis_ord_g_local",
            "join_counts",
            "join_counts_local",
            "adbscan"
        ]
    }

@gis_mcp.tool()
def getis_ord_g(
    shapefile_path: str,
    dependent_var: str = "LAND_USE",
    target_crs: str = "EPSG:4326",
    distance_threshold: float = 100000
) -> Dict[str, Any]:
    """Compute Getis-Ord G for global hot spot analysis."""
    try:
        # Clean backticks from string parameters
        shapefile_path = shapefile_path.replace("`", "")
        dependent_var = dependent_var.replace("`", "")
        target_crs = target_crs.replace("`", "")

        # Validate input file
        if not os.path.exists(shapefile_path):
            logger.error(f"Shapefile not found: {shapefile_path}")
            return {"status": "error", "message": f"Shapefile not found: {shapefile_path}"}

        # Load GeoDataFrame
        gdf = gpd.read_file(shapefile_path)
        
        # Validate dependent variable
        if dependent_var not in gdf.columns:
            logger.error(f"Dependent variable '{dependent_var}' not found in columns")
            return {"status": "error", "message": f"Dependent variable '{dependent_var}' not found in shapefile columns"}

        # Reproject to target CRS
        gdf = gdf.to_crs(target_crs)

        # Convert distance_threshold to degrees if using geographic CRS (e.g., EPSG:4326)
        effective_threshold = distance_threshold
        unit = "meters"
        if target_crs == "EPSG:4326":
            effective_threshold = distance_threshold / 111000
            unit = "degrees"

        # Extract dependent data
        dependent = gdf[dependent_var].values.astype(np.float64)

        # Create distance-based spatial weights matrix
        import libpysal
        import esda
        w = libpysal.weights.DistanceBand.from_dataframe(gdf, threshold=effective_threshold, binary=False)
        w.transform = 'r'

        # Handle islands
        for island in w.islands:
            w.weights[island] = [0] * len(w.weights[island])
            w.cardinalities[island] = 0

        # Getis-Ord G
        getis = esda.G(dependent, w)

        # Prepare GeoDataFrame preview
        preview = gdf[['geometry', dependent_var]].copy()
        preview['geometry'] = preview['geometry'].apply(lambda g: g.wkt)
        preview = preview.head(5).to_dict(orient="records")

        return {
            "status": "success",
            "message": f"Getis-Ord G analysis completed successfully (distance threshold: {effective_threshold} {unit})",
            "result": {
                "shapefile_path": shapefile_path,
                "getis_ord_g": {
                    "G": float(getis.G),
                    "p_value": float(getis.p_sim),
                    "z_score": float(getis.z_sim)
                },
                "data_preview": preview
            }
        }
    
    except Exception as e:
        logger.error(f"Error performing Getis-Ord G analysis: {str(e)}")
        return {"status": "error", "message": f"Failed to perform Getis-Ord G analysis: {str(e)}"}


def pysal_load_data(shapefile_path: str, dependent_var: str, target_crs: str, distance_threshold: float):
    """Common loader and weight creation for esda statistics."""
    if not os.path.exists(shapefile_path):
        return None, None, None, None, f"Shapefile not found: {shapefile_path}"

    gdf = gpd.read_file(shapefile_path)
    if dependent_var not in gdf.columns:
        return None, None, None, None, f"Dependent variable '{dependent_var}' not found in shapefile columns"

    gdf = gdf.to_crs(target_crs)

    effective_threshold = distance_threshold
    unit = "meters"
    if target_crs.upper() == "EPSG:4326":
        effective_threshold = distance_threshold / 111000
        unit = "degrees"

    y = gdf[dependent_var].values.astype(np.float64)
    import libpysal
    w = libpysal.weights.DistanceBand.from_dataframe(gdf, threshold=effective_threshold, binary=False)
    w.transform = 'r'

    for island in w.islands:
        w.weights[island] = [0] * len(w.weights[island])
        w.cardinalities[island] = 0

    return gdf, y, w, (effective_threshold, unit), None


@gis_mcp.tool()
def morans_i(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326", distance_threshold: float = 100000) -> Dict[str, Any]:
    """Compute Moran's I Global Autocorrelation Statistic."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    import esda
    stat = esda.Moran(y, w)
    preview = gdf[['geometry', dependent_var]].head(5).assign(
        geometry=lambda df: df.geometry.apply(lambda g: g.wkt)
    ).to_dict(orient="records")

    return {
        "status": "success",
        "message": f"Moran's I completed successfully (threshold: {threshold} {unit})",
        "result": {
            "I": float(stat.I),
            "p_value": float(stat.p_sim),
            "z_score": float(stat.z_sim),
            "data_preview": preview
        }
    }


@gis_mcp.tool()
def gearys_c(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326", distance_threshold: float = 100000) -> Dict[str, Any]:
    """Compute Global Geary's C Autocorrelation Statistic."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    import esda
    stat = esda.Geary(y, w)
    preview = gdf[['geometry', dependent_var]].head(5).assign(
        geometry=lambda df: df.geometry.apply(lambda g: g.wkt)
    ).to_dict(orient="records")

    return {
        "status": "success",
        "message": f"Geary's C completed successfully (threshold: {threshold} {unit})",
        "result": {
            "C": float(stat.C),
            "p_value": float(stat.p_sim),
            "z_score": float(stat.z_sim),
            "data_preview": preview
        }
    }


@gis_mcp.tool()
def gamma_statistic(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326", distance_threshold: float = 100000) -> Dict[str, Any]:
    """Compute Gamma Statistic for spatial autocorrelation."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    import esda
    stat = esda.Gamma(y, w)
    preview = gdf[['geometry', dependent_var]].head(5).assign(
        geometry=lambda df: df.geometry.apply(lambda g: g.wkt)
    ).to_dict(orient="records")

    return {
        "status": "success",
        "message": f"Gamma Statistic completed successfully (threshold: {threshold} {unit})",
        "result": {
            "Gamma": float(stat.gamma),
            "p_value": float(stat.p_value) if hasattr(stat, "p_value") else None,
            "data_preview": preview
        }
    }


@gis_mcp.tool()
def moran_local(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326",
                distance_threshold: float = 100000) -> Dict[str, Any]:
    """Local Moran's I."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    import esda
    stat = esda.Moran_Local(y, w)
    preview = gdf[['geometry', dependent_var]].head(5).copy()
    preview['geometry'] = preview['geometry'].apply(lambda g: g.wkt)

    # Return local statistics array summary
    return {
        "status": "success",
        "message": f"Local Moran's I completed successfully (threshold: {threshold} {unit})",
        "result": {
            "Is": stat.Is.tolist(),
            "p_values": stat.p_sim.tolist(),
            "z_scores": stat.z_sim.tolist(),
            "data_preview": preview.to_dict(orient="records")
        }
    }


@gis_mcp.tool()
def getis_ord_g_local(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326",
                      distance_threshold: float = 100000) -> Dict[str, Any]:
    """Local Getis-Ord G."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    import esda
    stat = esda.G_Local(y, w)
    preview = gdf[['geometry', dependent_var]].head(5).copy()
    preview['geometry'] = preview['geometry'].apply(lambda g: g.wkt)

    return {
        "status": "success",
        "message": f"Local Getis-Ord G completed successfully (threshold: {threshold} {unit})",
        "result": {
            "G_local": stat.Gs.tolist(),
            "p_values": stat.p_sim.tolist(),
            "z_scores": stat.z_sim.tolist(),
            "data_preview": preview.to_dict(orient="records")
        }
    }


@gis_mcp.tool()
def join_counts(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326",
                distance_threshold: float = 100000) -> Dict[str, Any]:
    """Global Binary Join Counts."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    # Join counts requires binary/categorical data - user must ensure y is binary (0/1 or True/False)
    import esda
    stat = esda.Join_Counts(y, w)
    preview = gdf[['geometry', dependent_var]].head(5).copy()
    preview['geometry'] = preview['geometry'].apply(lambda g: g.wkt)

    return {
        "status": "success",
        "message": f"Join Counts completed successfully (threshold: {threshold} {unit})",
        "result": {
            "join_counts": stat.jc,
            "expected": stat.expected,
            "variance": stat.variance,
            "z_score": stat.z_score,
            "p_value": stat.p_value,
            "data_preview": preview.to_dict(orient="records")
        }
    }


@gis_mcp.tool()
def join_counts_local(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326",
                      distance_threshold: float = 100000) -> Dict[str, Any]:
    """Local Join Counts."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    import esda
    stat = esda.Join_Counts_Local(y, w)
    preview = gdf[['geometry', dependent_var]].head(5).copy()
    preview['geometry'] = preview['geometry'].apply(lambda g: g.wkt)

    return {
        "status": "success",
        "message": f"Local Join Counts completed successfully (threshold: {threshold} {unit})",
        "result": {
            "local_join_counts": stat.local_join_counts.tolist(),
            "data_preview": preview.to_dict(orient="records")
        }
    }


@gis_mcp.tool()
def adbscan(shapefile_path: str, dependent_var: str = None, target_crs: str = "EPSG:4326",
            distance_threshold: float = 100000, eps: float = 0.1, min_samples: int = 5) -> Dict[str, Any]:
    """Adaptive DBSCAN clustering (requires coordinates, no dependent_var)."""
    if not os.path.exists(shapefile_path):
        return {"status": "error", "message": f"Shapefile not found: {shapefile_path}"}
    gdf = gpd.read_file(shapefile_path)
    gdf = gdf.to_crs(target_crs)

    coords = np.array(list(gdf.geometry.apply(lambda g: (g.x, g.y))))
    import esda
    stat = esda.adbscan.ADBSCAN(coords, eps=eps, min_samples=min_samples)

    preview = gdf[['geometry']].head(5).copy()
    preview['geometry'] = preview['geometry'].apply(lambda g: g.wkt)

    return {
        "status": "success",
        "message": f"A-DBSCAN clustering completed successfully (eps={eps}, min_samples={min_samples})",
        "result": {
            "labels": stat.labels_.tolist(),
            "core_sample_indices": stat.core_sample_indices_.tolist(),
            "components": stat.components_.tolist() if hasattr(stat, "components_") else None,
            "data_preview": preview.to_dict(orient="records")
        }
    }

@gis_mcp.tool()
def weights_from_shapefile(shapefile_path: str, contiguity: str = "queen", id_field: Optional[str] = None) -> Dict[str, Any]:

    """Create a spatial weights (W) from a shapefile using contiguity.

    - contiguity: 'queen' or 'rook' (default 'queen')
    - id_field: optional attribute name to use as observation IDs
    """
    try:
        if not os.path.exists(shapefile_path):
            return {"status": "error", "message": f"Shapefile not found: {shapefile_path}"}

        contiguity_lower = (contiguity or "").lower()
        import libpysal
        if contiguity_lower == "queen":
            w = libpysal.weights.Queen.from_shapefile(shapefile_path, idVariable=id_field)
        elif contiguity_lower == "rook":
            w = libpysal.weights.Rook.from_shapefile(shapefile_path, idVariable=id_field)
        else:
            # Fallback to generic W loader if an unrecognized contiguity is provided
            w = libpysal.weights.W.from_shapefile(shapefile_path, idVariable=id_field)

        ids = w.id_order
        neighbor_counts = [w.cardinalities[i] for i in ids]
        islands = list(w.islands) if hasattr(w, "islands") else []

        preview_ids = ids[:5]
        neighbors_preview = {i: w.neighbors.get(i, []) for i in preview_ids}
        weights_preview = {i: w.weights.get(i, []) for i in preview_ids}

        result = {
            "n": int(w.n),
            "id_count": int(len(ids)),
            "id_field": id_field,
            "contiguity": contiguity_lower if contiguity_lower in {"queen", "rook"} else "generic",
            "neighbors_stats": {
                "min": int(min(neighbor_counts)) if neighbor_counts else 0,
                "max": int(max(neighbor_counts)) if neighbor_counts else 0,
                "mean": float(np.mean(neighbor_counts)) if neighbor_counts else 0.0,
            },
            "islands": islands,
            "neighbors_preview": neighbors_preview,
            "weights_preview": weights_preview,
        }

        return {
            "status": "success",
            "message": "Spatial weights constructed successfully",
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error creating spatial weights from shapefile: {str(e)}")
        return {"status": "error", "message": f"Failed to create spatial weights: {str(e)}"}

@gis_mcp.tool()
def distance_band_weights(
    data_path: str,
    threshold: float,
    binary: bool = True,
    id_field: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a distance-based spatial weights (W) object from point data.

    - data_path: path to point shapefile or GeoPackage
    - threshold: distance threshold for neighbors (in CRS units, e.g., meters)
    - binary: True for binary weights, False for inverse distance weights
    - id_field: optional attribute name to use as observation IDs
    """
    try:
        if not os.path.exists(data_path):
            return {"status": "error", "message": f"Data file not found: {data_path}"}

        gdf = gpd.read_file(data_path)

        if gdf.empty:
            return {"status": "error", "message": "Input file contains no features"}

        # Extract coordinates
        coords = [(geom.x, geom.y) for geom in gdf.geometry]

        # Create DistanceBand weights
        from libpysal.weights import weights
        if id_field and id_field in gdf.columns:
            ids = gdf[id_field].tolist()
            w = weights.DistanceBand(coords, threshold=threshold, binary=binary, ids=ids)
        else:
            w = weights.DistanceBand(coords, threshold=threshold, binary=binary)

        ids = w.id_order
        neighbor_counts = [w.cardinalities[i] for i in ids]
        islands = list(w.islands) if hasattr(w, "islands") else []

        # Previews
        preview_ids = ids[:5]
        neighbors_preview = {i: w.neighbors.get(i, []) for i in preview_ids}
        weights_preview = {i: w.weights.get(i, []) for i in preview_ids}

        result = {
            "n": int(w.n),
            "id_count": len(ids),
            "threshold": threshold,
            "binary": binary,
            "id_field": id_field,
            "neighbors_stats": {
                "min": int(min(neighbor_counts)) if neighbor_counts else 0,
                "max": int(max(neighbor_counts)) if neighbor_counts else 0,
                "mean": float(np.mean(neighbor_counts)) if neighbor_counts else 0.0,
            },
            "islands": islands,
            "neighbors_preview": neighbors_preview,
            "weights_preview": weights_preview,
        }

        return {
            "status": "success",
            "message": "DistanceBand spatial weights constructed successfully",
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error creating DistanceBand weights: {str(e)}")
        return {"status": "error", "message": f"Failed to create DistanceBand weights: {str(e)}"}


@gis_mcp.tool()
def knn_weights(
    data_path: str,
    k: int,
    id_field: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a k-nearest neighbors spatial weights (W) object from point data.

    - data_path: path to point shapefile or GeoPackage
    - k: number of nearest neighbors
    - id_field: optional attribute name to use as observation IDs
    """
    try:
        if not os.path.exists(data_path):
            return {"status": "error", "message": f"Data file not found: {data_path}"}

        gdf = gpd.read_file(data_path)

        if gdf.empty:
            return {"status": "error", "message": "Input file contains no features"}

        # Extract coordinates
        coords = [(geom.x, geom.y) for geom in gdf.geometry]

        # Create KNN weights
        from libpysal.weights import weights
        if id_field and id_field in gdf.columns:
            ids = gdf[id_field].tolist()
            w = weights.KNN(coords, k=k, ids=ids)
        else:
            w = weights.KNN(coords, k=k)

        ids = w.id_order
        neighbor_counts = [w.cardinalities[i] for i in ids]
        islands = list(w.islands) if hasattr(w, "islands") else []

        # Previews
        preview_ids = ids[:5]
        neighbors_preview = {i: w.neighbors.get(i, []) for i in preview_ids}
        weights_preview = {i: w.weights.get(i, []) for i in preview_ids}

        result = {
            "n": int(w.n),
            "id_count": len(ids),
            "k": k,
            "id_field": id_field,
            "neighbors_stats": {
                "min": int(min(neighbor_counts)) if neighbor_counts else 0,
                "max": int(max(neighbor_counts)) if neighbor_counts else 0,
                "mean": float(np.mean(neighbor_counts)) if neighbor_counts else 0.0,
            },
            "islands": islands,
            "neighbors_preview": neighbors_preview,
            "weights_preview": weights_preview,
        }

        return {
            "status": "success",
            "message": "KNN spatial weights constructed successfully",
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error creating KNN weights: {str(e)}")
        return {"status": "error", "message": f"Failed to create KNN weights: {str(e)}"}


@gis_mcp.tool()
def build_transform_and_save_weights(
    data_path: str,
    method: str = "queen",
    id_field: Optional[str] = None,
    threshold: Optional[float] = None,
    k: Optional[int] = None,
    binary: bool = True,
    transform_type: Optional[str] = None,
    output_path: str = "weights.gal",
    format: str = "gal",
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Pipeline: Read shapefile, build spatial weights, optionally transform, and save to file.

    Parameters:
    - data_path: Path to point shapefile or GeoPackage
    - method: 'queen', 'rook', 'distance_band', 'knn'
    - id_field: Optional field name for IDs
    - threshold: Distance threshold (required if method='distance_band')
    - k: Number of neighbors (required if method='knn')
    - binary: True for binary weights, False for inverse distance (DistanceBand only)
    - transform_type: 'r', 'v', 'b', 'o', or 'd' (optional)
    - output_path: File path to save weights
    - format: 'gal' or 'gwt'
    - overwrite: Allow overwriting if file exists
    """
    try:
        # --- Step 1: Check input file ---
        if not os.path.exists(data_path):
            return {"status": "error", "message": f"Data file not found: {data_path}"}

        gdf = gpd.read_file(data_path)
        if gdf.empty:
            return {"status": "error", "message": "Input file contains no features"}

        coords = [(geom.x, geom.y) for geom in gdf.geometry]

        # --- Step 2: Build weights ---
        method = (method or "").lower()
        if method == "queen":
            w = libpysal.weights.Queen.from_dataframe(gdf, idVariable=id_field)
        elif method == "rook":
            w = libpysal.weights.Rook.from_dataframe(gdf, idVariable=id_field)
        elif method == "distance_band":
            if threshold is None:
                return {"status": "error", "message": "Threshold is required for distance_band method"}
            if id_field and id_field in gdf.columns:
                ids = gdf[id_field].tolist()
                w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary, ids=ids)
            else:
                w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary)
        elif method == "knn":
            if k is None:
                return {"status": "error", "message": "k is required for knn method"}
            if id_field and id_field in gdf.columns:
                ids = gdf[id_field].tolist()
                w = libpysal.weights.KNN(coords, k=k, ids=ids)
            else:
                w = libpysal.weights.KNN(coords, k=k)
        else:
            return {"status": "error", "message": f"Unsupported method: {method}"}

        # --- Step 3: Apply transformation if given ---
        if transform_type:
            transform_type = (transform_type or "").lower()
            if transform_type not in {"r", "v", "b", "o", "d"}:
                return {"status": "error", "message": f"Invalid transform type: {transform_type}"}
            w.transform = transform_type

        # --- Step 4: Save weights to file ---
        format = (format or "").lower()
        if format not in {"gal", "gwt"}:
            return {"status": "error", "message": f"Invalid format: {format}"}

        if not output_path.lower().endswith(f".{format}"):
            output_path += f".{format}"

        if os.path.exists(output_path) and not overwrite:
            return {"status": "error", "message": f"File already exists: {output_path}. Set overwrite=True to replace it."}

        w.to_file(output_path, format=format)

        # --- Step 5: Build result ---
        return {
            "status": "success",
            "message": f"{method} weights built and saved successfully",
            "result": {
                "path": output_path,
                "format": format,
                "n": int(w.n),
                "transform": getattr(w, "transform", None),
                "islands": list(w.islands) if hasattr(w, "islands") else [],
            },
        }

    except Exception as e:
        logger.error(f"Error in build_transform_and_save_weights: {str(e)}")
        return {"status": "error", "message": f"Failed to build and save weights: {str(e)}"}


@gis_mcp.tool()
def ols_with_spatial_diagnostics_safe(
    data_path: str,
    y_field: str,
    x_fields: List[str],
    weights_path: Optional[str] = None,
    weights_method: str = "queen",
    id_field: Optional[str] = None,
    threshold: Optional[float] = None,
    k: Optional[int] = None,
    binary: bool = True
) -> Dict[str, Any]:
    """
    Safe MCP pipeline: Read shapefile, build/load W, convert numeric, check NaNs, run OLS.

    Parameters:
    - data_path: path to shapefile or GeoPackage
    - y_field: dependent variable column name
    - x_fields: list of independent variable column names
    - weights_path: optional path to existing weights file (.gal or .gwt)
    - weights_method: 'queen', 'rook', 'distance_band', or 'knn' (used if weights_path not provided)
    - id_field: optional attribute name to use as observation IDs
    - threshold: required if method='distance_band'
    - k: required if method='knn'
    - binary: True for binary weights (DistanceBand only)
    """
    try:
        # --- Step 1: Read data ---
        if not os.path.exists(data_path):
            return {"status": "error", "message": f"Data file not found: {data_path}"}

        gdf = gpd.read_file(data_path)
        if gdf.empty:
            return {"status": "error", "message": "Input file contains no features"}

        # --- Step 2: Extract and convert y and X ---
        if y_field not in gdf.columns:
            return {"status": "error", "message": f"Dependent variable '{y_field}' not found in dataset"}
        if any(xf not in gdf.columns for xf in x_fields):
            return {"status": "error", "message": f"Independent variable(s) {x_fields} not found in dataset"}

        y = gdf[[y_field]].astype(float).values
        X = gdf[x_fields].astype(float).values

        # --- Step 3: Check for NaNs or infinite values ---
        if not np.all(np.isfinite(y)):
            return {"status": "error", "message": "Dependent variable contains NaN or infinite values"}
        if not np.all(np.isfinite(X)):
            return {"status": "error", "message": "Independent variables contain NaN or infinite values"}

        # --- Step 4: Load or build weights ---
        if weights_path:
            if not os.path.exists(weights_path):
                return {"status": "error", "message": f"Weights file not found: {weights_path}"}
            w = libpysal.open(weights_path).read()
        else:
            coords = [(geom.x, geom.y) for geom in gdf.geometry]
            wm = weights_method.lower()
            if wm == "queen":
                w = libpysal.weights.Queen.from_dataframe(gdf, idVariable=id_field)
            elif wm == "rook":
                w = libpysal.weights.Rook.from_dataframe(gdf, idVariable=id_field)
            elif wm == "distance_band":
                if threshold is None:
                    return {"status": "error", "message": "Threshold is required for distance_band"}
                ids = gdf[id_field].tolist() if id_field and id_field in gdf.columns else None
                w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary, ids=ids)
            elif wm == "knn":
                if k is None:
                    return {"status": "error", "message": "k is required for knn"}
                ids = gdf[id_field].tolist() if id_field and id_field in gdf.columns else None
                w = libpysal.weights.KNN(coords, k=k, ids=ids)
            else:
                return {"status": "error", "message": f"Unsupported weights method: {weights_method}"}

        w.transform = "r"  # Row-standardize for regression

        # --- Step 5: Fit OLS with spatial diagnostics ---
        ols_model = libpysal.model.ML_Lag.from_dataframe(gdf, y_field, x_fields, w=w, name_y=y_field, name_x=x_fields)

        # --- Step 6: Collect results ---
        results = {
            "n_obs": ols_model.n,
            "r2": float(ols_model.r2),
            "std_error": ols_model.std_err.tolist(),
            "betas": {name: float(beta) for name, beta in zip(ols_model.name_x + [ols_model.name_y], ols_model.betas.flatten())},
            "moran_residual": float(ols_model.moran_res[0]) if hasattr(ols_model, "moran_res") else None,
            "moran_pvalue": float(ols_model.moran_res[1]) if hasattr(ols_model, "moran_res") else None,
        }

        return {
            "status": "success",
            "message": "OLS regression with spatial diagnostics completed successfully",
            "result": results
        }

    except Exception as e:
        logger.error(f"Error in ols_with_spatial_diagnostics_safe: {str(e)}")
        return {"status": "error", "message": f"Failed to run OLS regression: {str(e)}"}


@gis_mcp.tool()
def build_and_transform_weights(
    data_path: str,
    method: str = "queen",
    id_field: Optional[str] = None,
    threshold: Optional[float] = None,
    k: Optional[int] = None,
    binary: bool = True,
    transform_type: str = "r"
) -> Dict[str, Any]:
    """
    Build and transform spatial weights in one step.

    Parameters:
    - data_path: Path to point shapefile or GeoPackage
    - method: 'queen', 'rook', 'distance_band', or 'knn'
    - id_field: Optional field name for IDs
    - threshold: Distance threshold (required if method='distance_band')
    - k: Number of neighbors (required if method='knn')
    - binary: True for binary weights, False for inverse distance (DistanceBand only)
    - transform_type: 'r', 'v', 'b', 'o', or 'd'
    """
    try:
        # --- Step 1: Check file ---
        if not os.path.exists(data_path):
            return {"status": "error", "message": f"Data file not found: {data_path}"}

        gdf = gpd.read_file(data_path)
        if gdf.empty:
            return {"status": "error", "message": "Input file contains no features"}

        coords = [(geom.x, geom.y) for geom in gdf.geometry]

        # --- Step 2: Build weights ---
        method = (method or "").lower()
        if method == "queen":
            w = libpysal.weights.Queen.from_dataframe(gdf, idVariable=id_field)
        elif method == "rook":
            w = libpysal.weights.Rook.from_dataframe(gdf, idVariable=id_field)
        elif method == "distance_band":
            if threshold is None:
                return {"status": "error", "message": "Threshold is required for distance_band method"}
            if id_field and id_field in gdf.columns:
                ids = gdf[id_field].tolist()
                w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary, ids=ids)
            else:
                w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary)
        elif method == "knn":
            if k is None:
                return {"status": "error", "message": "k is required for knn method"}
            if id_field and id_field in gdf.columns:
                ids = gdf[id_field].tolist()
                w = libpysal.weights.KNN(coords, k=k, ids=ids)
            else:
                w = libpysal.weights.KNN(coords, k=k)
        else:
            return {"status": "error", "message": f"Unsupported method: {method}"}

        # --- Step 3: Apply transformation ---
        if not isinstance(w, libpysal.weights.W):
            return {"status": "error", "message": "Failed to build a valid W object"}
        transform_type = (transform_type or "").lower()
        if transform_type not in {"r", "v", "b", "o", "d"}:
            return {"status": "error", "message": f"Invalid transform type: {transform_type}"}
        w.transform = transform_type

        # --- Step 4: Build result ---
        ids = w.id_order
        neighbor_counts = [w.cardinalities[i] for i in ids]
        islands = list(w.islands) if hasattr(w, "islands") else []
        preview_ids = ids[:5]
        neighbors_preview = {i: w.neighbors.get(i, []) for i in preview_ids}
        weights_preview = {i: w.weights.get(i, []) for i in preview_ids}

        result = {
            "n": int(w.n),
            "id_count": len(ids),
            "method": method,
            "threshold": threshold if method == "distance_band" else None,
            "k": k if method == "knn" else None,
            "binary": binary if method == "distance_band" else None,
            "transform": transform_type,
            "neighbors_stats": {
                "min": int(min(neighbor_counts)) if neighbor_counts else 0,
                "max": int(max(neighbor_counts)) if neighbor_counts else 0,
                "mean": float(np.mean(neighbor_counts)) if neighbor_counts else 0.0,
            },
            "islands": islands,
            "neighbors_preview": neighbors_preview,
            "weights_preview": weights_preview,
        }

        return {
            "status": "success",
            "message": f"{method} spatial weights built and transformed successfully",
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error in build_and_transform_weights: {str(e)}")
        return {"status": "error", "message": f"Failed to build and transform weights: {str(e)}"}


@gis_mcp.tool()

def spatial_markov(
    shapefile_path: str,
    value_columns: Union[str, List[str]],   # time-ordered, oldest -> newest
    target_crs: str = "EPSG:4326",
    weights_method: str = "queen",          # 'queen'|'rook'|'distance'
    distance_threshold: float = 100000,     # meters (converted to degrees if 4326)
    k: int = 5,                             # classes for y (quantile bins if continuous)
    m: int = 5,                             # classes for spatial lags
    fixed: bool = True,                     # pooled quantiles across all periods
    permutations: int = 0,                  # >0 to get randomization p-values for x2
    relative: bool = True,                  # divide each period by its mean
    drop_na: bool = True,                   # drop features with any NA across time columns
    fill_empty_classes: bool = True         # handle empty bins by making them self-absorbing
) -> Dict[str, Any]:
    """Run giddy Spatial Markov on a panel (n regions x t periods) from a shapefile."""
    try:
        # --- sanitize ---
        for s in ("shapefile_path","target_crs","weights_method"):
            v = locals()[s]
            if isinstance(v, str):
                locals()[s] = v.replace("`","")

        if isinstance(value_columns, str):
            value_cols = [c.strip() for c in value_columns.replace("`","").split(",") if c.strip()]
        else:
            value_cols = list(value_columns)

        if not os.path.exists(shapefile_path):
            return {"status": "error", "message": f"Shapefile not found: {shapefile_path}"}
        if len(value_cols) < 2:
            return {"status": "error", "message": "value_columns must include at least 2 time steps (wide format)."}

        # --- load + project ---
        gdf = gpd.read_file(shapefile_path)
        missing = [c for c in value_cols if c not in gdf.columns]
        if missing:
            return {"status": "error", "message": f"Columns not found: {missing}"}

        gdf = gdf.to_crs(target_crs)

        # Ensure numeric
        gdf[value_cols] = gdf[value_cols].apply(pd.to_numeric, errors="coerce")

        # --- prepare Y (n x t) ---
        Y = gdf[value_cols].to_numpy(copy=True).astype(float)  # shape (n, t)
        if drop_na:
            mask = ~np.any(np.isnan(Y), axis=1)
            if mask.sum() < Y.shape[0]:
                gdf = gdf.loc[mask].reset_index(drop=True)
                Y = Y[mask, :]

        # optional relative values (period-wise)
        if relative:
            col_means = Y.mean(axis=0)
            col_means[col_means == 0] = 1.0
            Y = Y / col_means

        # --- spatial weights ---
        import libpysal
        wm = weights_method.lower()
        if wm == "queen":
            w = libpysal.weights.Queen.from_dataframe(gdf, use_index=True)
        elif wm == "rook":
            w = libpysal.weights.Rook.from_dataframe(gdf, use_index=True)
        elif wm == "distance":
            thr = distance_threshold
            if target_crs.upper() == "EPSG:4326":
                thr = distance_threshold / 111000.0  # meters -> degrees
            w = libpysal.weights.DistanceBand.from_dataframe(
                gdf, threshold=thr, binary=False, use_index=True
            )
        else:
            return {"status":"error","message":f"Unknown weights_method: {weights_method}"}

        w.transform = "r"

        # handle islands by dropping rows and rebuilding weights
        if w.islands:
            keep_idx = [i for i in range(gdf.shape[0]) if i not in set(w.islands)]
            if not keep_idx:
                return {"status":"error","message":"All units are islands under current weights; adjust weights_method/threshold."}
            gdf = gdf.iloc[keep_idx].reset_index(drop=True)
            Y = Y[keep_idx, :]
            if wm == "queen":
                w = libpysal.weights.Queen.from_dataframe(gdf, use_index=True)
            elif wm == "rook":
                w = libpysal.weights.Rook.from_dataframe(gdf, use_index=True)
            else:
                thr = distance_threshold if target_crs.upper() != "EPSG:4326" else distance_threshold/111000.0
                w = libpysal.weights.DistanceBand.from_dataframe(gdf, threshold=thr, binary=False, use_index=True)
            w.transform = "r"

        # --- Spatial Markov ---
        try:
            from giddy.markov import Spatial_Markov
        except ModuleNotFoundError:
            return {"status": "error", "message": "The 'giddy' package is not installed. Install with: pip install giddy"}

        sm = Spatial_Markov(
            Y, w,
            k=int(k), m=int(m),
            permutations=int(permutations),
            fixed=bool(fixed),
            discrete=False,
            fill_empty_classes=bool(fill_empty_classes),
            variable_name=";".join(value_cols)
        )

        # --- package results (JSON-safe) ---
        def tolist(x):
            try:
                return np.asarray(x).tolist()
            except Exception:
                if isinstance(x, (list, tuple)):
                    return [tolist(xx) for xx in x]
                return x

        # Safer preview: keep geometry, write WKT to a new column, then drop geometry
        preview = gdf[[*value_cols, "geometry"]].head(5).copy()
        preview["geometry_wkt"] = preview["geometry"].apply(
            lambda g: g.wkt if g is not None and not g.is_empty else None
        )
        preview = pd.DataFrame(preview.drop(columns="geometry")).to_dict(orient="records")

        result = {
            "n_regions": int(Y.shape[0]),
            "n_periods": int(Y.shape[1]),
            "k_classes_y": int(k),
            "m_classes_lag": int(m),
            "weights_method": weights_method.lower(),
            "value_columns": value_cols,
            "discretization": {
                "cutoffs_y": tolist(getattr(sm, "cutoffs", None)),
                "cutoffs_lag": tolist(getattr(sm, "lag_cutoffs", None)),
                "fixed": bool(fixed)
            },
            "global_transition_prob_p": tolist(sm.p),      # (k x k)
            "conditional_transition_prob_P": tolist(sm.P), # (m x k x k)
            "global_steady_state_s": tolist(sm.s),         # (k,)
            "conditional_steady_states_S": tolist(sm.S),   # (m x k)
            "tests": {
                "chi2_total_x2": float(getattr(sm, "x2", np.nan)),
                "chi2_df": int(getattr(sm, "x2_dof", -1)),
                "chi2_pvalue": float(getattr(sm, "x2_pvalue", np.nan)),
                "Q": float(getattr(sm, "Q", np.nan)),
                "Q_p_value": float(getattr(sm, "Q_p_value", np.nan)),
                "LR": float(getattr(sm, "LR", np.nan)),
                "LR_p_value": float(getattr(sm, "LR_p_value", np.nan)),
            },
            "data_preview": preview,
        }

        msg = "Spatial Markov completed successfully"
        if wm == "distance" and target_crs.upper() == "EPSG:4326":
            msg += f" (threshold interpreted as {distance_threshold/111000.0:.6f} degrees)."

        return {"status": "success", "message": msg, "result": result}

    except Exception as e:
        return {"status": "error", "message": f"Failed to run Spatial Markov: {str(e)}"}

