import os
import matplotlib.pyplot as plt
import geopandas as gpd
import rasterio
from rasterio.plot import show as rioshow
from shapely import wkt
from typing import List, Dict, Any

from ..mcp import gis_mcp

@gis_mcp.tool()
def create_map(
    layers: List[Dict[str, Any]],
    filename: str = "map",
    filetype: str = "png",
    title: str = None,
    show_grid: bool = True,
    add_legend: bool = True,
    output_dir: str = "outputs"
) -> Dict[str, Any]:
    """
    Create a styled map from multiple inputs (vectors, rasters, WKT, or coords).

    Args:
        layers: List of dicts, each containing "data" and "style".
        filename: Output filename (without extension).
        filetype: png, pdf, jpg...
        title: Optional map title.
        show_grid: Draw a grid.
        add_legend: Add legend if labels are provided.
        output_dir: Directory to save output.
    """
    try:
        fig, ax = plt.subplots(figsize=(8, 8))

        for layer in layers:
            data = layer.get("data")
            style = layer.get("style", {})
            label = style.get("label", None)

            if isinstance(data, str):
                if data.endswith(".shp"):
                    gdf = gpd.read_file(data)
                    gdf.plot(ax=ax, **style)
                elif data.endswith(".tif"):
                    with rasterio.open(data) as src:
                        rioshow(src, ax=ax, **style)
                else:
                    geom = wkt.loads(data)
                    gdf = gpd.GeoDataFrame(geometry=[geom])
                    gdf.plot(ax=ax, **style)

            elif isinstance(data, list):
                from shapely.geometry import Polygon, LineString, Point
                if len(data) > 2:
                    geom = Polygon(data)
                elif len(data) == 2:
                    geom = LineString(data)
                else:
                    geom = Point(data)
                gdf = gpd.GeoDataFrame(geometry=[geom])
                gdf.plot(ax=ax, **style)

        # Add extras
        if title:
            ax.set_title(title, fontsize=14)
        if show_grid:
            ax.grid(True, linestyle="--", alpha=0.5)
        if add_legend:
            handles, labels = ax.get_legend_handles_labels()
            if labels:
                ax.legend()

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{filename}.{filetype}")
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        return {
            "status": "success",
            "message": f"Map created and saved to {output_path}",
            "output_path": output_path
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
