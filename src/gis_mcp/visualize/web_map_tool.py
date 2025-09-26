import os
import folium
import geopandas as gpd
from shapely import wkt
from ..mcp import gis_mcp

try:
    from folium.plugins import ScaleBar, MiniMap
    HAS_SCALEBAR = True
except ImportError:
    from folium.plugins import MiniMap
    HAS_SCALEBAR = False


@gis_mcp.tool()
def create_web_map(
    layers,
    filename: str = "map.html",
    title: str = "My Map",
    output_dir: str = "outputs",
    show_grid: bool = True,
    add_legend: bool = True,
    basemap: str = "OpenStreetMap",
    add_minimap: bool = True,
):
    """
    Create an interactive web map (HTML) using Folium.
    Each shapefile/layer gets its own label in the legend,
    and the title updates dynamically when layers are toggled.

    Args:
        layers (list): List of dicts like {"data": "...", "style": {...}}
                       - "style" may include {"label": "Layer Name", "color": "blue"}
        filename (str): Output HTML filename.
        title (str): Main map title.
        output_dir (str): Output directory for HTML.
    """
    try:
        m = folium.Map(location=[20, 0], zoom_start=2, tiles=basemap)
        legend_items = []

        for layer in layers:
            data = layer.get("data")
            style = layer.get("style", {})
            label = style.get("label", "Layer")
            color = style.get("color", "blue")

            # Read data
            if isinstance(data, str) and data.endswith(".shp"):
                gdf = gpd.read_file(data)
            elif isinstance(data, str) and data.endswith(".geojson"):
                gdf = gpd.read_file(data)
            elif isinstance(data, str):
                geom = wkt.loads(data)
                gdf = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")
            elif isinstance(data, gpd.GeoDataFrame):
                gdf = data
            else:
                raise ValueError(f"Unsupported data type for {data}")

            fields = [c for c in gdf.columns if c != gdf.geometry.name]

            gj = folium.GeoJson(
                gdf,
                name=label,
                style_function=lambda x, col=color: {
                    "color": col,
                    "fillColor": col,
                    "weight": 2,
                    "fillOpacity": 0.5,
                },
                tooltip=folium.GeoJsonTooltip(fields=fields, aliases=fields) if fields else None,
            )
            gj.add_to(m)
            legend_items.append((label, color))

        # Layer control
        folium.LayerControl().add_to(m)

        # Scale bar & lat/lon
        if show_grid:
            folium.LatLngPopup().add_to(m)
            if HAS_SCALEBAR:
                ScaleBar(position="bottomleft").add_to(m)

        # MiniMap
        if add_minimap:
            MiniMap(toggle_display=True, position="bottomright").add_to(m)

        # Legend
        if add_legend and legend_items:
            legend_html = """
            <div style="
                position: fixed; 
                bottom: 50px; left: 50px; width: 200px; 
                background-color: white; 
                border:2px solid grey; 
                z-index:9999; 
                font-size:14px;
                padding: 10px;
            ">
            <b>Legend</b><br>
            """
            for label, color in legend_items:
                legend_html += f"<i style='background:{color};width:18px;height:18px;float:left;margin-right:8px;'></i>{label}<br>"
            legend_html += "</div>"
            m.get_root().html.add_child(folium.Element(legend_html))

        # Title & dynamic subtitle
        if title:
            title_html = f"""
                <div id="mapTitle" style="
                    position: fixed;
                    top: 10px;
                    left: 50%;
                    transform: translateX(-50%);
                    z-index: 9999;
                    font-size: 20px;
                    font-weight: bold;
                    background-color: rgba(255, 255, 255, 0.7);
                    padding: 5px 10px;
                    border-radius: 5px;
                    text-align: center;
                ">
                    {title}<br>
                    <span id="layerTitle" style="font-size:14px; font-weight:normal;">Showing: All layers</span>
                </div>
            """
            m.get_root().html.add_child(folium.Element(title_html))

            # Add JS to update subtitle on layer toggle
            script = """
            <script>
            var map = window.map;
            map.on('overlayadd', function(e) {
                document.getElementById('layerTitle').innerHTML = 'Showing: ' + e.name;
            });
            map.on('overlayremove', function(e) {
                document.getElementById('layerTitle').innerHTML = 'Showing: All layers';
            });
            </script>
            """
            m.get_root().html.add_child(folium.Element(script))

        # Save file
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        m.save(output_path)

        return {"status": "success", "message": f"Map created: {output_path}", "output_path": output_path}

    except Exception as e:
        return {"status": "error", "message": str(e)}
